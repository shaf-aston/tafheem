"""Request and reply types for routers/daleel.py."""

from __future__ import annotations

from pydantic import BaseModel

from backend.models.common import Source


class DaleelHit(BaseModel):
    """One quotation, exactly as its book has it.

    There is deliberately no field for a summary, an explanation or an answer.
    Daleel shows where something is written and stops; a field for a verdict
    would be a field somebody eventually fills in."""

    locator: str
    """How a person would cite it: "2:255", "§1.4.4". Never blank."""
    arabic: str
    english: str = ""
    match: str
    """exact | partial | root | loose. The screen labels a loose match as one
    rather than letting a probable typo-fix pass for a clean find."""
    source: Source
    book: str = ""
    """Which book of that source. Fourteen classical works share one badge, so
    the badge alone no longer says where a quotation is from."""


class DaleelBook(BaseModel):
    """One book a reader can narrow the search to."""

    name: str
    """What the book calls itself. Also its id: the index stores this string,
    so there is no second name to keep in step with this one."""
    source: str
    """The source it is credited to, so the list can be grouped the way the
    results are."""
    category: str = ""
    """The shelf it sits on: Qur'an, Fiqh, Grammar. Read from sources.json, so
    a new shelf is a line of data rather than a change here."""
    english: str = ""
    """Its name in English letters, for a reader who cannot type Arabic. Empty
    when the book's own name is already English, and empty rather than invented
    when nobody has written one; never used as an id."""


class DaleelResponse(BaseModel):
    query: str
    hits: list[DaleelHit]
    books: list[str] = []
    """The books this search was narrowed to, echoed back. Names the reader
    asked for that no book has are dropped, so this is what was actually
    searched rather than what was requested."""
    # False when the index has not been built yet, so the panel can say that
    # instead of showing an empty list, which would read as "not in any book".
    ready: bool = True
