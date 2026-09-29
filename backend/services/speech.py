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
import threading
import uuid
import wave
from abc import ABC, abstractmethod
from pathlib import Path

from backend.config import get_settings
from backend.services.fallback import Retirable

log = logging.getLogger(__name__)

CACHE = Path(__file__).resolve().parents[1] / "data" / "speech_cache"


class Voice(Retirable, ABC):
    """Arabic text in, WAV bytes out."""

    name: str
    #: Changes whenever the same name would sound different (another model), so the cache misses.
    version: str = ""

    @abstractmethod
    def say(self, text: str) -> bytes:
        """The spoken text as a WAV file."""


class PiperVoice(Voice):
    """Piper's Jordanian Arabic voice (kareem), on this machine's CPU.

    Reads harakat: عَالِم and عَالَم, كَتَبَ and كُتِبَ come out different, as
    do ط/ت, ص/س, ض/د. It stops on the word, so the final short vowel is dropped,
    which is the correct pause form. Its ظ came out as ذ; _phonemes below fixes that.
    About 70ms a word once loaded; loading takes a few seconds, once.
    """

    name = "piper"

    def __init__(self) -> None:
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                from huggingface_hub import hf_hub_download
                from piper import PiperVoice as Engine

                path = get_settings().speech_piper_model
                hf_hub_download("rhasspy/piper-voices", path + ".json")
                self._model = Engine.load(hf_hub_download("rhasspy/piper-voices", path))
        return self._model

    @property
    def version(self) -> str:
        # "+zaa": words kept before the ظ fix are made again.
        return get_settings().speech_piper_model + "+zaa"

    def say(self, text: str) -> bytes:
        model = self._load()
        out = io.BytesIO()
        # One word at a time: the model is not known to be safe to share between threads.
        with self._lock, wave.open(out, "wb") as file:
            file.setframerate(model.config.sample_rate)
            file.setsampwidth(2)
            file.setnchannels(1)
            for sentence in _phonemes(model, text):
                audio = model.phoneme_ids_to_audio(model.phonemes_to_ids(sentence))
                file.writeframes((audio.clip(-1, 1) * 32767).astype("<i2").tobytes())
        return out.getvalue()


def _phonemes(model, text: str) -> list[list[str]]:
    """Piper's phonemes, with ظ said as ظ.

    Its phonemizer says ظ as ð, the sound of ذ. ظ is spelled as ض, which comes
    out as the distinct pair d ˤ, and that pair is turned into ð ˤ. Only in a
    text with no real ض, whose d ˤ would be changed too; there ظ stays as it was.
    """
    zaa, daad = "ظ", "ض"
    if zaa not in text or daad in text:
        return model.phonemize(text)
    fixed = []
    for sentence in model.phonemize(text.replace(zaa, daad)):
        out: list[str] = []
        for i, p in enumerate(sentence):
            out.append("ð" if p == "d" and sentence[i + 1:i + 2] == ["ˤ"] else p)
        fixed.append(out)
    return fixed


_VOICES: dict[str, Voice] = {voice.name: voice for voice in (PiperVoice(),)}


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
    """Keep the store under `speech_cache_max_files`, dropping the oldest first.

    Anyone can ask for any Arabic, so without a cap the disk fills. A word
    dropped here is only made again the next time someone asks.
    """
    limit = get_settings().speech_cache_max_files
    files = list(CACHE.glob("*.wav"))
    if len(files) <= limit:
        return
    files.sort(key=lambda f: f.stat().st_mtime)
    for old in files[: len(files) - limit]:
        old.unlink(missing_ok=True)


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
