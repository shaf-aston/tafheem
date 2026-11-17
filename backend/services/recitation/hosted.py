"""Sound in, words out, done on somebody else's machine.

The same job as whisper.py and the same one function, so the two are swappable:
whoever calls `transcribe` cannot tell which of them answered. This one sends the
recording to Groq, who run `listening_model`. Free, and nothing here is paid
for.

It spends whichever of `LISTENING_GROQ_API_KEYS` the asking ear holds, never
the one the grammar explanations run on unless no listening key is set. Config
resolves the list (`listening_keys`); services/recitation/ears.py makes one ear
per key, so each account's allowance is spent and rested on its own.

Why it exists, measured on this machine with one spoken English word:

    on this computer   base model, eight cores busy   about 2,700ms
    on Groq            large model, no cores busy     about   450ms

So it is six times quicker on a model several sizes bigger, and the processor
does no work at all. Its one cost is that the few seconds of sound leave this
computer, where the local engine never let them. That is the whole trade, and
`listening_hosted` in config turns it off.

Never the last word. Anything at all going wrong here, no internet, a retired
key, the free allowance spent, is not an error the reader should meet: the
package falls back to the engine on this machine, which is slower and still
right. That is why every failure in this file is simply raised.
"""
from __future__ import annotations

import io
import logging
import unicodedata
import wave
from functools import lru_cache

import numpy as np

from backend.config import get_settings
from backend.services.recitation import loudness
from backend.services.recitation.recording import kind_of

log = logging.getLogger(__name__)

# Each language config's `dictation_languages` may name: how Groq's reply spells it, and the alphabet its letters
# are named for in Unicode. Groq picks the language itself, and about 1 single word in 10 it picks wrong (72 synthetic
# search words, 2026-11-17: "Moses" as Japanese, رحمة as German, "mercy" as French).
_LANGUAGES = {"ar": ("arabic", "ARABIC"), "en": ("english", "LATIN")}


def is_available(key: str) -> bool:
    """True when this key may be used at all: switched on, and a key to use."""
    return get_settings().listening_hosted and bool(key)


def transcribe(audio: bytes, key: str, language: str | None = None, hint: str = "") -> str:
    """Words said, heard on `key`'s account. Raises rather than guessing.

    `language`: hear it in that one; none lets Groq pick, held to whisper.dictation_languages().
    `hint`: text Whisper reads first, sets register. Empty sends none.
    """
    said = []
    for piece in _pieces(audio):
        # Later pieces keep the first piece's language and read the words before them, as Whisper does
        # across its own 30s windows: guessed afresh, one Qur'an piece came back translated into English,
        # and with no words before it another began with an invented "Surah Al-Fatihah".
        heard, language = _hear(piece, key, language, said[-1] if said else hint)
        said.append(heard)
    return " ".join(filter(None, said))


def _hear(audio: bytes, key: str, language: str | None, hint: str) -> tuple[str, str | None]:
    """One piece heard and its language. Unnamed, the answer is always in an allowed language and its alphabet."""
    from backend.services.recitation import whisper

    heard, spoken, _ = _ask(audio, key, language, hint)
    allowed = whisper.dictation_languages()
    if language or (spoken in allowed and _written_in(heard, spoken)):
        return heard, language or spoken

    # Heard again in each allowed language. Named Arabic, "Moses" still came back in Japanese letters, so only an
    # answer in its own alphabet counts; of those the surer wins (the 7 misheard words: every Arabic one stayed Arabic).
    log.info("heard as %s, so hearing it again in %s", spoken, ", ".join(allowed))
    kept = []
    for code in allowed:
        text, _, sure = _ask(audio, key, code, hint)
        if _written_in(text, code):
            kept.append((sure, text, code))
    if not kept:
        return "", None
    _, heard, spoken = max(kept)
    return heard, spoken


def _written_in(text: str, code: str) -> bool:
    """True when `text` has letters and every one is in `code`'s alphabet. Vowel marks and digits are not letters."""
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and all(unicodedata.name(c, "").startswith(_LANGUAGES[code][1]) for c in letters)


def _pieces(audio: bytes) -> list[bytes]:
    """The recording as is when it fits Groq's 30s, else cut at quiet moments into 16kHz WAV pieces."""
    from backend.services.recitation import whisper

    settings = get_settings()
    sound = whisper.sound_of(audio)
    cuts = loudness.quiet_cuts(sound, loudness.SAMPLE_RATE, settings.listening_piece_s,
                               settings.listening_cut_search_s, settings.listening_cut_window_s)
    if not cuts:
        return [audio]
    log.info("cut a %.1fs recording into %d pieces", len(sound) / loudness.SAMPLE_RATE, len(cuts) + 1)
    return [_wav(piece) for piece in np.split(sound, cuts)]


def _wav(sound) -> bytes:
    """Mono 16-bit WAV of decoded sound."""
    out = io.BytesIO()
    with wave.open(out, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(loudness.SAMPLE_RATE)
        file.writeframes((np.clip(sound, -1, 1) * 32767).astype("<i2").tobytes())
    return out.getvalue()


# One client per key, kept: the ears take turns, and a cache of one rebuilt
# the client (about 450ms) on every turn.
@lru_cache(maxsize=8)
def _client(api_key: str, timeout: float):
    """A Groq client for one key, built once and kept.

    Building one costs about 450ms on this machine, the certificate store being
    read and a connection being opened, and the request itself then takes
    about 150ms. Built per recording, as it first was, the client was most of
    the wait: a spoken word answered in 780ms answers in 300ms with it kept.
    Keyed on the key and timeout so a changed setting builds a fresh one.
    """
    from groq import Groq

    # Timeout short on purpose. This is the quick way of hearing, so a slow
    # answer has already failed at its job; the engine on this machine is
    # waiting and will beat a stalled request.
    return Groq(api_key=api_key, timeout=timeout, max_retries=0)


def _ask(audio: bytes, key: str, language: str | None, hint: str) -> tuple[str, str, float]:
    """One request. The words, the language they were taken to be in, and how sure (mean log-probability)."""
    settings = get_settings()
    client = _client(key, settings.listening_timeout_s)

    # A name the service will accept, and a true one: it reads the extension.
    # Chrome records webm but Safari records mp4, and an mp4 called .webm is
    # a refusal that rests this key and sends every reading after it to the
    # slower ear on this machine.
    handle = io.BytesIO(audio)
    handle.name = f"recording.{kind_of(audio) or 'webm'}"

    answer = client.audio.transcriptions.create(
        file=handle,
        model=settings.listening_model,
        # Asked for so the reply says which language it decided on, and how sure it was. Without it
        # the text comes back alone and there is nothing to check it against.
        response_format="verbose_json",
        **({"language": language} if language else {}),
        **({"prompt": hint} if hint else {}),
    )
    said = str(getattr(answer, "language", "") or "").strip().lower()
    spoken = next((code for code, (name, _) in _LANGUAGES.items() if name == said), said)
    segments = getattr(answer, "segments", None) or []
    sure = sum(s["avg_logprob"] for s in segments) / len(segments) if segments else float("-inf")
    return (answer.text or "").strip(), spoken, sure
