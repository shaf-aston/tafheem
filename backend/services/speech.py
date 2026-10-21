"""Text in, spoken Arabic out. The synthetic voices behind GET /api/speak.

Same shape as the ears (services/recitation/ears.py): each voice answers the
same question, config names the order, and a voice that breaks is retired
(services/fallback.py) so later words skip it. Real reciters are not here; the
page plays their recordings straight from quran.com (frontend lib/speak.js).

Adding a voice, a cloned reciter say, is one class below plus its name in
`speech_voices`.

A spoken dialect is said by a speaker of it, not by the Fusha voice guessing:
a caller may name one voice to try first (`say(text, first="edge:ar-SY-...")`),
and `voice_named` makes it from the name, so which dialect gets which speaker is
data (colloquial/dialects.json), never code. The default order stays behind it,
so a dialect phrase is still said when that speaker cannot be reached.

Every word said is kept on disk by (voice, text), because a quiz asks the same
words again and again and the second time should cost a file read.

The engine makes one word at a time (it uses every core), so who goes next
matters more than how fast it is. A word pressed goes before any word the page
is only readying (lib/speak.js's `prepare`): a lesson sheet readies ten lines
at once, and a press used to wait behind all ten. A word already being made
when it is pressed is not made twice: the press takes the next turn and finds
it stored.

Each word made is logged with how long it waited for its turn and how long the
engine took, so a slow press can be read off the server's log:

    said 'كيف حالك' (8 letters, pressed) in 0.62s after 0.00s waiting [fastpitch]
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import re
import threading
import time
import uuid
import wave
from abc import ABC, abstractmethod
from contextlib import contextmanager, nullcontext
from pathlib import Path

from backend.config import get_settings
from backend.services.fallback import Retirable

log = logging.getLogger(__name__)

CACHE = Path(__file__).resolve().parents[1] / "data" / "speech_cache"
# How fast every voice speaks, and the speeds a reader may pick, kept with the page's
# own voice settings so the server's voices and the phone's never drift apart.
_SPEAK = json.loads((Path(__file__).resolve().parents[2] / "frontend" / "src" / "speak.json").read_text("utf-8"))
PACE: float = _SPEAK["pace"]
SPEEDS: dict[str, float] = _SPEAK["speeds"]
# The marks a phrase ends or breathes on.
PAUSE = "[،؛؟.!?,]"


# How the pages write what is not said aloud, and what is said instead.
SAID_INSTEAD = (
    (r"\([^)]*\)", " "),                    # a stage note: (بعد شوية) هذا مضبوط
    (r"\s*[/|]\s*|:", "، "),                # both forms, a pause between: آسف / آسفة; a colon breathes
    ("[\"«»ـ\u200e\u200f\u06e2\u06e5]", ""),  # quotes, the stretching ـ, direction marks, Qur'an spelling signs
    (f"{PAUSE}+(?={PAUSE})", ""),            # a run of marks is its last: عِ...؟ is عِ؟
)


def tidy(text: str) -> str:
    """The text as it is said: what is only written (see SAID_INSTEAD) taken out, one
    space between words and none before a mark, so كيفك ؟ and كيفك؟ are one phrase
    and one stored sound."""
    for written, said in SAID_INSTEAD:
        text = re.sub(written, said, text)
    return re.sub(f" (?={PAUSE})", "", " ".join(text.split()))


class Voice(Retirable, ABC):
    """Arabic text in, WAV bytes out."""

    name: str
    #: Changes whenever the same name would sound different (another model), so the cache misses.
    version: str = ""
    #: Runs on this machine's cores, so it takes its turn (see Turns); a voice over the network does not.
    local: bool = True

    @abstractmethod
    def say(self, text: str, speed: float = 1.0) -> bytes:
        """The spoken text as a WAV file, at `speed` times this voice's own pace (below 1 is slower)."""


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


def long_aa_spelt_out(text: str) -> str:
    """Write the small alif over a letter (هٰذَا) as a full one (هَاذَا): the engine drops it, and
    the letter under it with no other vowel comes out bare, hdha for haadha."""
    return re.sub("َ?ٰ", "َا", text)


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
    # It has no g or ch either and drops the dialect letters for them, so they become the nearest it has.
    PAUSES = str.maketrans({"،": " ,", "؛": " ,", "؟": " ?", ",": " ,", "?": " ?", ".": " .", "!": " !",
                            "گ": "ك", "ڭ": "ك", "چ": "تش"})

    def __init__(self) -> None:
        self._model = None
        self._lock = threading.Lock()

    @property
    def version(self) -> str:
        settings = get_settings()
        return (f"hifigan-speaker{settings.speech_fastpitch_speaker}-pace{PACE}"
                f"-lead{settings.speech_lead_ms}-name2"
                f"-peak{settings.speech_peak}-fade{settings.speech_fade_ms}")

    def say(self, text: str, speed: float = 1.0) -> bytes:
        # One word at a time: the model is not known to be safe to share between threads.
        with self._lock:
            if self._model is None:
                from tts_arabic import get_model

                self._model = get_model("fastpitch", "hifigan", cuda=None)
            settings = get_settings()
            audio = self._model.infer(long_aa_spelt_out(name_spelt_out(text)).translate(self.PAUSES),
                                      speaker=settings.speech_fastpitch_speaker,
                                      pace=PACE * speed)
        return wav(shaped(audio))


RATE = 22050  # FastPitch's samples a second


def shaped(audio):
    """A made word as it should reach the ear: every word as loud as the next
    (speech_peak), soft at both ends so it starts and stops without a click
    (speech_fade_ms), and quiet around it for a phone's speaker to wake (speech_lead_ms)."""
    import numpy as np

    settings = get_settings()
    peak = np.abs(audio).max()
    if peak:
        audio = audio * (settings.speech_peak / peak)
    fade = min(RATE * settings.speech_fade_ms // 1000, len(audio) // 2)
    if fade:
        ramp = np.linspace(0, 1, fade, dtype=audio.dtype)
        audio[:fade] *= ramp
        audio[-fade:] *= ramp[::-1]
    lead = np.zeros(RATE * settings.speech_lead_ms // 1000, dtype=audio.dtype)
    return np.concatenate([lead, audio, lead])


def wav(audio) -> bytes:
    """Samples between -1 and 1 as a 16-bit mono WAV file."""
    out = io.BytesIO()
    with wave.open(out, "wb") as file:
        file.setframerate(RATE)
        file.setsampwidth(2)
        file.setnchannels(1)
        file.writeframes((audio.clip(-1, 1) * 32767).astype("<i2").tobytes())
    return out.getvalue()


class EdgeVoice(Voice):
    """One of Microsoft's neural voices, each a native speaker of one country's Arabic
    (ar-SY, ar-EG, ar-MA...), through the `edge-tts` package. Over the network, so it
    costs this machine nothing and shares no turn with FastPitch; MP3, not WAV.
    Reads text with or without harakat, so a dialect line is said as written."""

    local = False

    def __init__(self, speaker: str) -> None:
        self.speaker = speaker
        self.name = f"edge-{speaker}"

    @property
    def version(self) -> str:
        return f"pace{PACE}"

    def say(self, text: str, speed: float = 1.0) -> bytes:
        import asyncio

        import edge_tts

        async def spoken() -> bytes:
            # Its aiohttp ignores the usual proxy variables unless handed one.
            talk = edge_tts.Communicate(text, self.speaker, rate=edge_rate(PACE * speed),
                                        proxy=os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy"))
            return b"".join([part["data"] async for part in talk.stream() if part["type"] == "audio"])

        audio = asyncio.run(spoken())
        if not audio:
            raise RuntimeError(f"{self.speaker} returned no sound")
        return audio


def edge_rate(pace: float) -> str:
    """A pace as Edge writes it: 0.9 is "-10%"."""
    return f"{round((pace - 1) * 100):+d}%"


_VOICES: dict[str, Voice] = {voice.name: voice for voice in (FastPitchVoice(),)}
# How a voice named in data is made: the part before ':' picks the kind, the rest is its speaker.
_KINDS = {"edge": EdgeVoice}


def voice_named(name: str) -> Voice:
    """The voice `name` means: a built-in one by its name, or `kind:speaker` made once and kept,
    so its rests and retirement last the run. A name that is neither is a ValueError."""
    if name not in _VOICES:
        kind, _, speaker = name.partition(":")
        if kind not in _KINDS or not speaker:
            raise ValueError(f"{name!r} is not a voice")
        _VOICES[name] = _KINDS[kind](speaker)
    return _VOICES[name]


def media_type(audio: bytes) -> str:
    """What kind of sound file `audio` is: FastPitch writes WAV, the network voices MP3."""
    return "audio/wav" if audio[:4] == b"RIFF" else "audio/mpeg"


def order(first: str | None = None) -> list[Voice]:
    """The voices to try: `first` if named, then config's order. Unknown names are logged, not ignored."""
    chain = [voice_named(first)] if first else []
    for name in (part.strip() for part in get_settings().speech_voices.split(",")):
        if name in _VOICES:
            chain.append(_VOICES[name])
        elif name:
            log.warning("speech_voices names '%s', which is not a voice; ignoring it", name)
    return chain


def warm() -> None:
    """Load every voice by saying one word, so a learner's first press is not
    the one that waits the ~5s a model takes to load and run for the first time.
    Counts the store too, which takes a moment once it holds thousands of words."""
    with _turns.take(pressed=True):
        _trim(0)
    for voice in order():
        try:
            voice.say("كِتَاب")
        except Exception:
            log.exception("voice %s could not warm up", voice.name)


class Turns:
    """One word made at a time, and a pressed word before any word made ahead."""

    def __init__(self) -> None:
        self._free = threading.Condition()
        self._busy = False
        self._pressed_waiting = 0

    @contextmanager
    def take(self, pressed: bool):
        with self._free:
            self._pressed_waiting += pressed
            try:
                self._free.wait_for(lambda: not self._busy and (pressed or not self._pressed_waiting))
            finally:
                self._pressed_waiting -= pressed
            self._busy = True
        try:
            yield
        finally:
            with self._free:
                self._busy = False
                self._free.notify_all()


_turns = Turns()

# Bytes in the store, counted once and then kept as words are added, so a new
# word does not stat every file (~130 ms at 20,000 of them). The two server
# processes share the folder and each counts only its own words, so the store
# can pass the cap before a count notices; the recount when one does is exact.
_stored: int | None = None


def _trim(added: int) -> None:
    """Keep the store under `speech_cache_max_mb`, dropping the oldest first.

    Anyone can ask for any Arabic, so without a cap the disk fills. A word
    dropped here is only made again the next time someone asks.
    """
    global _stored
    room = get_settings().speech_cache_max_mb * 1_000_000
    if _stored is not None:
        _stored += added
        if _stored <= room:
            return
    files = sorted(((f.stat(), f) for f in CACHE.glob("*.wav")), key=lambda pair: pair[0].st_mtime)
    _stored = sum(stat.st_size for stat, _ in files)
    for stat, old in files:
        if _stored <= room:
            break
        old.unlink(missing_ok=True)
        _stored -= stat.st_size


def stored(voice: Voice, text: str, speed: float = 1.0) -> Path:
    """Where `voice` keeps `text` once said at `speed`."""
    # The usual speed keeps its old key, so every word already made is still found.
    said = f"{voice.version}\n{text}" if speed == 1.0 else f"{voice.version}\nspeed{speed}\n{text}"
    key = hashlib.sha256(said.encode()).hexdigest()[:32]
    return CACHE / f"{voice.name}-{key}.wav"  # an MP3 too: the name only has to be unique


def forget(text: str) -> None:
    """Drop the stored sound of `text`, so the next ask makes it again, for a word whose making changed."""
    for voice in order():
        stored(voice, text).unlink(missing_ok=True)


def say(text: str, pressed: bool = True, first: str | None = None, speed: float = 1.0) -> bytes:
    """Spoken `text` from the first voice that manages. Raises when none can.

    `pressed` is False for a word only being made ahead of a press, which
    waits while any pressed word is waiting. `first` names a voice to try
    before the usual order: a dialect's own speaker. `speed` is one of
    SPEEDS, below 1 slower.
    """
    for voice in order(first):
        if voice.retired_reason or voice.resting():
            continue
        cached = stored(voice, text, speed)
        if cached.exists():
            return cached.read_bytes()
        asked = time.monotonic()
        with _turns.take(pressed) if voice.local else nullcontext():
            # Made while this one waited: by the same word readied, or pressed twice.
            if cached.exists():
                return cached.read_bytes()
            if voice.retired_reason or voice.resting():  # failed for the word ahead in line
                continue
            started = time.monotonic()
            try:
                audio = voice.say(text, speed)
            except ImportError as exc:  # not installed: will not fix itself
                voice.retire(str(exc))
                continue
            except Exception as exc:  # offline on first download, one odd word: rest, then retry
                log.exception("voice %s failed", voice.name)
                voice.rest(get_settings().speech_rest_s, str(exc))
                continue
            log.info("said %r (%d letters, %s) in %.2fs after %.2fs waiting [%s]", text, len(text),
                     "pressed" if pressed else "ahead", time.monotonic() - started, started - asked, voice.name)
            # Written aside and renamed, so a request for the same word never reads half a file.
            CACHE.mkdir(parents=True, exist_ok=True)
            part = cached.with_suffix(f".{uuid.uuid4().hex}.part")
            part.write_bytes(audio)
            os.replace(part, cached)
            _trim(len(audio))
        return audio
    raise RuntimeError("no voice could say this")


def active() -> str:
    """Which voice would say the next new word, for the health line, or why none would."""
    for voice in order():
        if not voice.retired_reason and not voice.resting():
            return voice.name
    return "; ".join(f"{v.name}: {v.retired_reason or v.resting()}" for v in order()) or "none"
