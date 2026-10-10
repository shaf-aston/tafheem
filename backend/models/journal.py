"""Request and reply types for routers/journal.py."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator



# ── Recite journal: what the page reports about itself ──────────────────────
# The same shape routers/listen.py uses for a reading id, so a page-reported
# event can be joined to the server-side lines for the same reading.
_ID_RE = re.compile(r"[A-Za-z0-9._:-]{1,64}")


class JournalPageEvent(BaseModel):
    """One thing the page itself saw: a mic gate closing, a reading it gave up
    waiting on. Server-side events are written straight to the journal through
    journal.note() and never pass through here."""
    at: str | int | float
    """When the page saw it, in whatever shape its own clock gave it."""
    kind: str = Field(min_length=1, max_length=40)
    session: str | None = Field(default=None, max_length=64)
    reading: str | None = Field(default=None, max_length=64)
    detail: dict | None = None

    @field_validator("kind")
    @classmethod
    def _kind_shape(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9._-]{0,39}", value):
            raise ValueError("kind must start with a lowercase letter and use only a-z 0-9 . _ -")
        return value

    @field_validator("session", "reading")
    @classmethod
    def _id_shape(cls, value: str | None) -> str | None:
        if value is not None and not _ID_RE.fullmatch(value):
            raise ValueError("must be 1-64 characters of letters, digits, . _ : -")
        return value


class JournalBatch(BaseModel):
    """What the page sends in one POST /api/journal. Event-count and byte-size
    limits are enforced by the router, from config, not here: they are
    runtime-tunable and a Pydantic Field constraint is fixed at import time."""
    events: list[JournalPageEvent]
