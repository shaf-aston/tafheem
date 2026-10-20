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
    which is the correct pause form. Known fault: ظ is said like ذ.
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
        return get_settings().speech_piper_model

    def say(self, text: str) -> bytes:
        model = self._load()
        out = io.BytesIO()
        # One word at a time: the model is not known to be safe to share between threads.
        with self._lock, wave.open(out, "wb") as file:
            model.synthesize_wav(text, file)
        return out.getvalue()


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
        return audio
    raise RuntimeError("no voice could say this")
