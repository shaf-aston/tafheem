"""Text in, spoken Arabic out. The synthetic voices behind GET /api/speak.

Same shape as the ears (services/recitation/ears.py): each voice answers the
same question, config names the order, and a voice that breaks is retired
(services/fallback.py) so later words skip it. Real reciters are not here; the
page plays their recordings straight from quran.com (frontend lib/speak.js).

Adding a voice, a cloned reciter say, is one class below plus its name in
`speech_voices`.

Every word said is kept on disk by (voice, text), because a quiz asks the same
words again and again and the second time should cost a file read.
"""
from __future__ import annotations

import hashlib
import io
import logging
import os
import re
import threading
import uuid
import wave
from abc import ABC, abstractmethod
from pathlib import Path

from backend.config import get_settings
from backend.services.fallback import Retirable

log = logging.getLogger(__name__)

CACHE = Path(__file__).resolve().parents[1] / "data" / "speech_cache"
# The marks a phrase ends or breathes on.
PAUSE = "[،؛؟.!?,]"


def tidy(text: str) -> str:
    """One space between words and none before a mark, so كيفك ؟ and كيفك؟ are one phrase and one stored sound."""
    return re.sub(f" (?={PAUSE})", "", " ".join(text.split()))


class Voice(Retirable, ABC):
    """Arabic text in, WAV bytes out."""

    name: str
    #: Changes whenever the same name would sound different (another model), so the cache misses.
    version: str = ""

    @abstractmethod
    def say(self, text: str) -> bytes:
        """The spoken text as a WAV file."""


MARKS = "ً-ْٰ"
# The name of Allah, with or without a particle (و ف ب ت ل) in front.
NAME = re.compile(f"(?<!\\S)([وفبت][{MARKS}]*)?(?:ا[{MARKS}]*)?ل[{MARKS}]*ل[{MARKS}]*ه([{MARKS}]*)(?=\\s|{PAUSE}|$)")
OPENS = {"و": "َ", "ف": "َ", "ت": "َ", "ب": "ِ"}


def name_spelt_out(text: str) -> str:
    """Write the long aa of Allah as a full alif, the only spelling FastPitch says right.

    Its phonetiser knows the name only as a bare first word; after a particle or
    another word it says llah short or drops the vowel (لِلَّهِ, وَاللَّهِ, بِسْمِ اللَّهِ).
    """
    def one(m: re.Match) -> str:
        lead, end = m.group(1), m.group(2)
        letters = re.sub(f"[{MARKS}]", "", m.group(0))
        if lead is None:
            if letters == "الله" and m.start() == 0:
                return m.group(0)  # the engine's own entry, heavy l and all
            return ("لِلَّاه" if letters == "لله" else "اللَّاه") + end
        if not re.search(f"[{MARKS}]", lead):
            lead += OPENS[lead[0]]
        return lead + ("لِلَّاه" if letters[1:] == "لله" else "اللَّاه") + end
    return NAME.sub(one, text)


class FastPitchVoice(Voice):
    """FastPitch + HiFi-GAN, Modern Standard Arabic (nipponjo/tts_arabic), on the CPU.

    Says every haraka written, the final one too, so أَلْهَبَ is alhaba as the
    page shows it. Chosen 2026-10-01 over Piper's kareem: Whisper misheard 21%
    of letters from this voice, 67% from kareem, at any speed; a quran.com
    reciter scored as well. About 0.5s a word; the models (~250 MB) download
    from Google Drive into the package's folder on first use.
    """

    name = "fastpitch"
    # The engine pauses on Latin marks written as their own word; an Arabic ، or ؟ it drops silently.
    PAUSES = str.maketrans({"،": " ,", "؛": " ,", "؟": " ?", ",": " ,", "?": " ?", ".": " .", "!": " !"})

    def __init__(self) -> None:
        self._model = None
        self._lock = threading.Lock()

    @property
    def version(self) -> str:
        settings = get_settings()
        return f"hifigan-speaker{settings.speech_fastpitch_speaker}-pace{settings.speech_fastpitch_pace}-name2"

    def say(self, text: str) -> bytes:
        # One word at a time: the model is not known to be safe to share between threads.
        with self._lock:
            if self._model is None:
                from tts_arabic import get_model

                self._model = get_model("fastpitch", "hifigan", cuda=None)
            settings = get_settings()
            audio = self._model.infer(name_spelt_out(text).translate(self.PAUSES),
                                      speaker=settings.speech_fastpitch_speaker, pace=settings.speech_fastpitch_pace)
        out = io.BytesIO()
        with wave.open(out, "wb") as file:
            file.setframerate(22050)
            file.setsampwidth(2)
            file.setnchannels(1)
            file.writeframes((audio.clip(-1, 1) * 32767).astype("<i2").tobytes())
        return out.getvalue()


_VOICES: dict[str, Voice] = {voice.name: voice for voice in (FastPitchVoice(),)}


def order() -> list[Voice]:
    """The voices to try, in config's order. Unknown names are logged, not ignored."""
    chain = []
    for name in (part.strip() for part in get_settings().speech_voices.split(",")):
        if name in _VOICES:
            chain.append(_VOICES[name])
        elif name:
            log.warning("speech_voices names '%s', which is not a voice; ignoring it", name)
    return chain


def warm() -> None:
    """Load every voice by saying one word, so a learner's first press is not
    the one that waits the ~5s a model takes to load and run for the first time."""
    for voice in order():
        try:
            voice.say("كِتَاب")
        except Exception:
            log.exception("voice %s could not warm up", voice.name)


def _trim() -> None:
    """Keep the store under `speech_cache_max_mb`, dropping the oldest first.

    Anyone can ask for any Arabic, so without a cap the disk fills. A word
    dropped here is only made again the next time someone asks.
    """
    room = get_settings().speech_cache_max_mb * 1_000_000
    files = sorted(((f.stat(), f) for f in CACHE.glob("*.wav")), key=lambda pair: pair[0].st_mtime)
    excess = sum(stat.st_size for stat, _ in files) - room
    for stat, old in files:
        if excess <= 0:
            break
        old.unlink(missing_ok=True)
        excess -= stat.st_size


def say(text: str) -> bytes:
    """Spoken `text` from the first voice that manages. Raises when none can."""
    for voice in order():
        if voice.retired_reason or voice.resting():
            continue
        key = hashlib.sha256(f"{voice.version}\n{text}".encode()).hexdigest()[:32]
        cached = CACHE / f"{voice.name}-{key}.wav"
        if cached.exists():
            return cached.read_bytes()
        try:
            audio = voice.say(text)
        except ImportError as exc:  # not installed: will not fix itself
            voice.retire(str(exc))
            continue
        except Exception as exc:  # offline on first download, one odd word: rest, then retry
            log.exception("voice %s failed", voice.name)
            voice.rest(get_settings().speech_rest_s, str(exc))
            continue
        # Written aside and renamed, so a request for the same word never reads half a file.
        CACHE.mkdir(parents=True, exist_ok=True)
        part = cached.with_suffix(f".{uuid.uuid4().hex}.part")
        part.write_bytes(audio)
        os.replace(part, cached)
        _trim()
        return audio
    raise RuntimeError("no voice could say this")
