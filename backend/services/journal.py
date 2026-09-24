"""One append-only record of what happened to a recitation.

Everything backend.log already says is still said there; this is a second,
narrower log, one JSON object per line, built to answer one question fast:
"where did this particular reading go wrong, server side or page side, and at
what point". A reading id ties the two sides together, so a support
conversation is "send me reading abc123" rather than a stretch of prose logs
either side has to be read start to end to place.

Every line has the same shape: {"at", "side": "server"|"page", "kind", plus
whatever that kind of event knows}. `note` writes the server's half, called
from routers/listen.py and services/recitation/ears.py. `note_page` writes the
page's half, called only from routers/journal.py, which is the one door the
browser has onto this file.

Its own logger, and propagate=False, so a line written here does not also land
in backend.log: the two logs answer different questions and mixing them would
make both slower to read.
"""
from __future__ import annotations

import contextvars
import json
import logging
import logging.handlers
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import get_settings

# backend/services/journal.py -> backend/services -> backend -> project root,
# the folder that holds backend/. journal_path is relative to here rather than
# to backend/ the way data_path's paths are: the journal belongs beside
# backend.log, not inside the app's own data folder.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_journal = logging.getLogger("recite.journal")
_journal.propagate = False
# Which settings the handler currently open was built from, so a changed
# journal_path (a test pointing it at tmp_path, or a reloaded .env) is picked
# up on the next line instead of writing to wherever the first line went.
_built_from: tuple[str, int, int] | None = None
# Two request threads can both find the handler stale at once; without a
# lock both would add one, and every line after would be written twice.
_configure_lock = threading.Lock()


class JournalConfigError(ValueError):
    """A journal setting is not usable. Raised the first time something is
    actually logged, so a bad .env value fails loud rather than the app
    silently writing nowhere."""


def _ensure_configured() -> None:
    global _built_from
    settings = get_settings()
    if settings.journal_max_kb <= 0:
        raise JournalConfigError("journal_max_kb must be positive")
    if settings.journal_keep <= 0:
        raise JournalConfigError("journal_keep must be positive")
    key = (settings.journal_path, settings.journal_max_kb, settings.journal_keep)
    if key == _built_from:
        return
    # Two worker threads can both see a stale _built_from at once; without
    # this lock both add a handler, and every line after is written twice.
    with _configure_lock:
        if key == _built_from:
            return
        for old in list(_journal.handlers):
            _journal.removeHandler(old)
            old.close()
        path = (_PROJECT_ROOT / settings.journal_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=settings.journal_max_kb * 1024, backupCount=settings.journal_keep, encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        _journal.addHandler(handler)
        _journal.setLevel(logging.INFO)
        _built_from = key


# The reading a deep call (ears.py, several layers below the router) is
# journalling for, without threading an id as an argument through every
# function in between. Set once per request in routers/listen.py and read by
# anything that wants to say which reading it was working on. Safe across the
# thread a recitation is heard on: run_in_threadpool copies the current
# context into that thread, so a value set here before the call is visible
# inside it.
reading_id: contextvars.ContextVar[str] = contextvars.ContextVar("reading_id", default="")


# A raw SDK exception carries the request that made it, headers and all,
# which is the API key (see groq_backend.py's own note on this). A bearer
# header or a gsk_-prefixed key is the shape that leaks; both are scrubbed
# before a message or traceback ever reaches the journal file.
_SECRET = re.compile(r"Bearer\s+\S+|gsk_[A-Za-z0-9]+", re.IGNORECASE)
_SCRUB_LIMIT = 300


def scrub(text: str) -> str:
    """A raw error message or traceback, made safe to journal: no bearer
    token or key, and capped so one huge message cannot blow up a line."""
    return _SECRET.sub("[redacted]", text)[:_SCRUB_LIMIT]


def _jsonable(value: Any) -> Any:
    """Anything that cannot go straight into JSON, stringified rather than
    dropped: a half-written line is worse than an ugly field."""
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def note(kind: str, **fields: Any) -> None:
    """One line from the server side of the app.

    `reading` is filled from the current reading (see `reading_id`) unless the
    caller names one. Fields that are None or "" are left out rather than
    written, so a line only carries what it actually knows.
    """
    fields.setdefault("reading", reading_id.get())
    line: dict[str, Any] = {
        "at": datetime.now().astimezone().isoformat(timespec="milliseconds"),
        "side": "server",
        "kind": kind,
    }
    for key, value in fields.items():
        if value not in (None, ""):
            line[key] = _jsonable(value)
    _ensure_configured()
    _journal.info(json.dumps(line, ensure_ascii=False))


def note_page(event: dict[str, Any]) -> None:
    """One line the page reported about itself, through POST /api/journal.

    Written exactly as sent: two identical events in one batch make two
    identical lines, on purpose. The page may legitimately repeat an event (a
    retry, a mic gate closing twice), and deciding which repeat was the "real"
    one is not this file's job, it is a question for whoever reads the log.
    """
    line: dict[str, Any] = {
        "at": event.get("at"),
        "side": "page",
        "kind": event.get("kind", ""),
    }
    for key in ("session", "reading", "detail"):
        value = event.get(key)
        if value not in (None, ""):
            line[key] = _jsonable(value)
    _ensure_configured()
    _journal.info(json.dumps(line, ensure_ascii=False))
