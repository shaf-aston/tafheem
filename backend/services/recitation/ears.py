"""The ears, and the order they are asked in.

An ear turns sound into words. There are two, they do the same job at very
different speeds, and nothing above this file knows which one answered:

    hosted   Groq's machines, whisper-large-v3-turbo   about 250ms
    letters  this computer, tilawa's Qur'an model      about 640ms, recitations only
    here     this computer, faster-whisper             about 1,600ms

Measured on this machine, from the timing log. The order comes from config
(`recitation_ears`), so putting this computer first is a setting and not a code
change; that is the switch for a session where nothing should leave the machine.

Why this is an interface rather than the `if` it used to be
----------------------------------------------------------
The app already had this exact problem once and solved it properly for the AI
backends that explain grammar: an interface, an ordered chain, and a dead engine
struck off for the rest of the run (services/ai). Listening had the same shape
written a second, rougher way, and it showed. A rejected key was retried on
every single recording, three in a row in the log, each paying a full round trip
to be told the same thing. Both sides now retire an engine the same way, through
services/fallback.

Word sureness
-------------
Checking a recitation asks how sure the ear is of each word the page expects,
and only the ear on this machine can answer that: Groq returns text and nothing
else. So checking (services/recitation/__init__.py's `check`) never comes
through here at all, it calls the model on this machine directly. This file is
only about which ear writes the words down, and every ear can do that.
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

from backend.config import get_settings
from backend.services import journal
from backend.services.fallback import Retirable, permanent_failure
from backend.services.recitation import hosted, letters, listen
from backend.services.timing import timed

log = logging.getLogger(__name__)


class Unreadable(RuntimeError):
    """The recording itself cannot be decoded, so no ear will ever read it.

    Not an engine failing: falling through to the next one only spends another
    few seconds reaching the same answer. It has happened, from a truncated
    browser recording that carried a valid webm header and nothing playable
    behind it, and it reached the reader as "Could not make that out", which
    blames the listening for something the recording did.
    """


class Ear(Retirable, ABC):
    """Sound in, words out. Every ear answers the same question the same way."""

    #: Runs on this machine's processor, so a recitation it reads waits its turn.
    local: bool = False
    #: Knows only the Qur'an, so a search is never sent to it.
    reciting_only: bool = False

    @abstractmethod
    def transcribe(self, audio: bytes, language: str | None, hint: str) -> str:
        """What was said. Name a language to hear it in that one."""

    @abstractmethod
    def is_available(self) -> bool:
        """True when this ear can be asked right now."""

    @abstractmethod
    def name(self, reciting: bool = False) -> str:
        """What to call it in the log and on the health line.

        `reciting` because the ear here keeps two models, one that knows the
        Qur'an and one that knows ordinary words, and the log is worth nothing
        if it cannot say which of them was slow.
        """


class HostedEar(Ear):
    """Groq's machines. Quick, and the sound leaves this computer to get there."""

    def transcribe(self, audio: bytes, language: str | None, hint: str) -> str:
        return hosted.transcribe(audio, language, hint)

    def is_available(self) -> bool:
        return hosted.is_available()

    def name(self, reciting: bool = False) -> str:
        return get_settings().recitation_hosted_model


class LocalEar(Ear):
    """faster-whisper on this computer. Slower, and nothing leaves the machine.

    The last ear in every order on purpose: it needs no key, no internet and
    nobody's permission, so it is the one that is always there to catch a fall.
    """

    local = True

    def transcribe(self, audio: bytes, language: str | None, hint: str) -> str:
        return listen.transcribe(audio, language, hint)

    def is_available(self) -> bool:
        return True

    def name(self, reciting: bool = False) -> str:
        settings = get_settings()
        return f"local-{settings.recitation_model if reciting else settings.dictation_model}"


class LettersEar(Ear):
    """tilawa's small Qur'an model on this computer (letters.py).

    Measured on the 1,950 marked recordings: 640ms a reading against 1,600ms
    for the ear below, and it placed 95% of them against 72%, because it writes
    the letters that were said where Whisper wrote والله for هو الله.
    """

    local = True
    reciting_only = True

    def transcribe(self, audio: bytes, language: str | None, hint: str) -> str:
        return letters.read(listen.sound_of(audio))

    def is_available(self) -> bool:
        return letters.installed()

    def name(self, reciting: bool = False) -> str:
        return "letters"


_EARS: dict[str, Ear] = {"hosted": HostedEar(), "letters": LettersEar(), "here": LocalEar()}


def named(key: str) -> Ear:
    """One ear by the name config uses for it."""
    return _EARS[key]


def order(reciting: bool = False) -> list[Ear]:
    """The ears to try, in turn. Unknown names in config are said, not ignored."""
    wanted = [name.strip() for name in get_settings().recitation_ears.split(",") if name.strip()]
    chain = []
    for name in wanted:
        if name not in _EARS:
            log.warning("recitation_ears names '%s', which is not an ear; ignoring it", name)
            continue
        if reciting or not _EARS[name].reciting_only:
            chain.append(_EARS[name])
    # Never leave the app with no ear at all because a setting was mistyped.
    if not any(isinstance(ear, LocalEar) for ear in chain):
        chain.append(_EARS["here"])
    return chain


def hear(audio: bytes, language: str | None, hint: str) -> str:
    """Ask each ear in turn until one answers. Raises only when none can.

    Every way of not answering is the same thing to the reader, a moment longer,
    so they are caught together rather than told apart: no internet, a key that
    has been retired, an allowance spent for the hour. The recording is still in
    hand and the ear here still works, so there is nothing for them to do about
    any of them. A key that was *rejected* is different, because it will be
    rejected again, so that ear is struck off for the rest of the run; anything
    else earns a short rest instead (see Retirable.rest), so the next recording
    or two does not pay for the same failure again.
    """
    reciting = language is not None
    last: Exception | None = None
    for ear in order(reciting):
        if ear.retired_reason or ear.resting() or not ear.is_available():
            continue
        name = ear.name(reciting)
        try:
            started = time.perf_counter()
            heard = timed("heard", ear.transcribe, audio, language, hint,
                         ear=name, bytes=len(audio), hint=bool(hint))
            # Written here, inside the ear that actually answered, rather than
            # by the caller guessing from `active()`: the router used to log
            # the ear that *would* answer, which named Groq even on a reading
            # the local engine fell back to.
            journal.note("ear.heard", ear=name, ms=round((time.perf_counter() - started) * 1000), chars=len(heard))
            return heard
        except Unreadable:
            raise
        except Exception as exc:
            last = exc
            # Only what fallback.permanent_failure already reads off the raw
            # SDK exception, plus its type name: never the exception itself,
            # which carries the request that made it, headers and key.
            status = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
            journal.note("ear.failed", ear=name, error=type(exc).__name__, status=status, message=journal.scrub(str(exc)))
            if reason := permanent_failure(exc):
                ear.retire(reason)
                log.warning("retiring the %s ear for this run, %s", name, reason)
                journal.note("ear.retired", ear=name, reason=reason)
            else:
                rest_s = get_settings().recitation_hosted_rest_s
                ear.rest(rest_s, journal.scrub(str(exc)))
                log.info("the %s ear did not answer (%s), resting it for %.0fs", name, exc, rest_s)
                journal.note("ear.resting", ear=name, seconds=rest_s, reason=journal.scrub(str(exc)))
    if last is not None:
        raise last
    raise listen.NotInstalled("No ear is available on this machine.")


def active(reciting: bool = False) -> str:
    """Which ear would answer next, for the health line.

    `reciting` also names the local ear by its Qur'an model rather than its
    general one (LocalEar.name), and lets in the ears that only know the Qur'an.
    """
    for ear in order(reciting):
        if not ear.retired_reason and not ear.resting() and ear.is_available():
            return ear.name(reciting)
    return "none"


def would_answer_locally(reciting: bool = True) -> bool:
    """True when an ear on this machine is the one that would answer right now.

    routers/listen.py asks this to decide whether a recitation needs `_turn`:
    that queue exists to protect this machine's own CPU from two readings at
    once, and Groq answering costs this machine nothing to queue behind.
    """
    for ear in order(reciting):
        if not ear.retired_reason and not ear.resting() and ear.is_available():
            return ear.local
    return True
