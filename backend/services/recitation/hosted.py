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
import wave
from functools import lru_cache

import numpy as np

from backend.config import get_settings
from backend.services.recitation.recording import kind_of

log = logging.getLogger(__name__)

# What the reader may be speaking. Groq works the language out for itself, which
# is better than this machine can do, but "works it out" includes working it out
# wrong: one English word has been heard as Urdu and written in Urdu letters. So
# an answer in neither language is asked again, said to be Arabic, which is what
# this app is mostly for. Full names because that is how the reply spells them.
_EXPECTED = {"arabic": "ar", "english": "en"}

# What the decoder hands back (faster_whisper decodes to 16kHz mono).
_RATE = 16000


def is_available(key: str) -> bool:
    """True when this key may be used at all: switched on, and a key to use."""
    return get_settings().listening_hosted and bool(key)


def transcribe(audio: bytes, key: str, language: str | None = None, hint: str = "") -> str:
    """Words said, heard on `key`'s account. Raises rather than guessing.

    `language`: hear it in that one; none lets Groq pick within the two above.
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


def _hear(audio: bytes, key: str, language: str | None, hint: str) -> tuple[str, str]:
    """One piece heard and its language, asked again as Arabic if Groq took it for neither."""
    heard, spoken = _ask(audio, key, language, hint)
    if language or spoken in _EXPECTED.values():
        return heard, language or spoken

    log.info("heard as %s, which is neither, so reading it again as Arabic", spoken)
    return _ask(audio, key, "ar", hint)[0], "ar"


def _pieces(audio: bytes) -> list[bytes]:
    """The recording as is when it fits Groq's 30s, else cut at quiet moments into 16kHz WAV pieces."""
    from backend.services.recitation import loudness, whisper

    settings = get_settings()
    sound = whisper.sound_of(audio)
    cuts = loudness.quiet_cuts(sound, _RATE, settings.listening_piece_s,
                               settings.listening_cut_search_s, settings.listening_cut_window_s)
    if not cuts:
        return [audio]
    log.info("cut a %.1fs recording into %d pieces", len(sound) / _RATE, len(cuts) + 1)
    return [_wav(piece) for piece in np.split(sound, cuts)]


def _wav(sound) -> bytes:
    """Mono 16-bit WAV of decoded sound."""
    out = io.BytesIO()
    with wave.open(out, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(_RATE)
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


def _ask(audio: bytes, key: str, language: str | None, hint: str) -> tuple[str, str]:
    """One request. The words, and the language they were taken to be in."""
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
        # Asked for so the reply says which language it decided on. Without it
        # the text comes back alone and there is nothing to check it against.
        response_format="verbose_json",
        **({"language": language} if language else {}),
        **({"prompt": hint} if hint else {}),
    )
    said = str(getattr(answer, "language", "") or "").strip().lower()
    return (answer.text or "").strip(), _EXPECTED.get(said, said)
