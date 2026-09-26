"""Sound in, words out, done on somebody else's machine.

The same job as listen.py and the same one function, so the two are swappable:
whoever calls `transcribe` cannot tell which of them answered. This one sends the
recording to Groq, who run Whisper large-v3-turbo. Free, and nothing here is paid
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
from functools import lru_cache

from backend.config import get_settings

log = logging.getLogger(__name__)

# What the reader may be speaking. Groq works the language out for itself, which
# is better than this machine can do, but "works it out" includes working it out
# wrong: one English word has been heard as Urdu and written in Urdu letters. So
# an answer in neither language is asked again, said to be Arabic, which is what
# this app is mostly for. Full names because that is how the reply spells them.
_EXPECTED = {"arabic": "ar", "english": "en"}


def is_available(key: str) -> bool:
    """True when this key may be used at all: switched on, and a key to use."""
    return get_settings().listening_hosted and bool(key)


def transcribe(audio: bytes, key: str, language: str | None = None, hint: str = "") -> str:
    """Words said, heard on `key`'s account. Raises rather than guessing.

    `language`: hear it in that one; none lets Groq pick within the two above.
    `hint`: text Whisper reads first, sets register. Empty sends none.
    """
    heard, spoken = _ask(audio, key, language, hint)
    if language or spoken in _EXPECTED.values():
        return heard

    log.info("heard as %s, which is neither, so reading it again as Arabic", spoken)
    return _ask(audio, key, "ar", hint)[0]


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

    # A name the service will accept. It reads the extension, and the browser
    # sends webm; the local engine gets the same suffix for the same reason.
    handle = io.BytesIO(audio)
    handle.name = "recording.webm"

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
