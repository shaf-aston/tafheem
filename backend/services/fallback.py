"""Choosing between engines that do the same job, and giving up on a dead one.

Two parts of the app hire outside engines for a job this machine can also do
more slowly: the AI backends that explain grammar (services/ai) and the ears
that turn sound into words (services/recitation). Both want the same three
things, so both get them from here rather than each inventing its own:

    Retirable          an engine that can be struck off for the rest of the run
    permanent_failure  whether an error means "never again" or "try again"
    retry_after        how long the engine itself said to wait, when it said

What each side does with an engine that will not answer is its own business and
stays there: the AI backends pick one and fall back to the rule engine, the ears
walk an order and try the next. Only the two ideas above are the same idea.

Why retiring matters at all: a key that has been rejected once will be rejected
every time, and without this every later request pays a full round trip to be
told so again. It has happened twice on this machine, a Groq 401 and a
SambaNova 402, and the log shows three recordings in a row each paying for it.
"""
from __future__ import annotations

import time


class Retirable:
    """An engine that can be struck off for the rest of the run, or rested for
    a while when the failure is not necessarily permanent."""

    #: Why this engine gave up, or "" while it is still usable.
    retired_reason: str = ""
    #: The moment (time.monotonic()) a rest ends, or 0.0 when it is not resting.
    _resting_until: float = 0.0
    #: Why it is resting, kept beside the moment so `resting()` can say why.
    _resting_reason: str = ""

    def retire(self, reason: str) -> None:
        """Stop offering this engine until the app is restarted.

        A wrong key or a model that no longer exists does not fix itself.
        Retrying it on every request makes each one slow and makes the app
        claim an engine it cannot actually reach; retiring is how the health
        line stays honest.
        """
        self.retired_reason = reason

    def rest(self, seconds: float, reason: str) -> None:
        """Stop offering this engine for a while, not for the rest of the run.

        A timeout, a rate limit or a bad gateway is not proof the engine is
        broken, only that this one call did not work, and asking again on
        every request while it is having a bad minute pays the full cost of a
        dead key for something that fixes itself. `retire` is still the answer
        for a failure that will not.
        """
        self._resting_until = time.monotonic() + seconds
        self._resting_reason = reason

    def resting(self) -> str:
        """Why this engine is resting, or "" once the rest is over."""
        if self._resting_until and time.monotonic() < self._resting_until:
            return self._resting_reason
        return ""


def permanent_failure(exc: Exception) -> str:
    """Why this error will happen again, or "" when it might not.

    Read off the HTTP status the SDK carried back, because that is the one
    thing every one of these services agrees on. Anything else, no internet, a
    timeout, an allowance spent for the hour, is worth another try later.
    """
    # Off the error itself first, then off the answer it came with. Both, because
    # an engine may hand the status on without handing on the whole answer: the
    # answer holds the request that made it, and the request holds the key.
    status = (getattr(exc, "status_code", None)
              or getattr(getattr(exc, "response", None), "status_code", None))
    if status in (401, 403):
        return "the API key was rejected"
    if status == 404:
        return "the configured model does not exist for this key"
    return ""


def retry_after(exc: Exception) -> float | None:
    """Seconds the engine said to wait before asking again, or None when it did
    not say. Read off the answer's Retry-After header only, never the rest of
    the answer, which holds the request and so the key.

    A refusal for the minute says a few seconds and one for the day says hours;
    resting every refusal a fixed minute asked again all day long for the one,
    and sat idle long after the other was over.
    """
    headers = getattr(getattr(exc, "response", None), "headers", None) or {}
    try:
        seconds = float(headers.get("retry-after", ""))
    except (TypeError, ValueError):
        return None
    return seconds if seconds > 0 else None
