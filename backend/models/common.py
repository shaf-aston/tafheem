"""Types every feature shares: where an answer came from, and a spelling fix."""

from __future__ import annotations

from pydantic import BaseModel



class Source(BaseModel):
    """Where a result came from and how far it can be trusted. Attached to every
    answer so the UI never shows a claim without saying who made it."""
    key: str
    label: str
    confidence: str   # verified | derived | translated | guessed, see lib/confidence.js
    detail: str


class Correction(BaseModel):
    """A typed word the search did not know, and the known word searched in its place (services/spelling.py)."""
    typed: str
    used: str
