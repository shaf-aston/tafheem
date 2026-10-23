"""Which books can be searched, and the English name of each.

`books` and `known_books` read the catalogue table the build writes beside the
passages; `english_of` names a book whose own name is Arabic.

`english_of` is the only reader of data/books/english-titles.json. Kept apart from the source
adapters on purpose: the books needing an English name arrive from three
different places with three different manifest shapes, and an English name is
one idea, so it is answered in one place rather than added to each of them.

Empty is a real answer and stays one. A book already named in English has no
entry, and neither does one nobody has written a name for yet; the picker shows
what it has rather than transliterating a guess.
"""
from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from backend.config import get_settings

from backend.services.daleel.index.connection import db

_FILE = Path(__file__).resolve().parents[2] / "data" / "books" / "english-titles.json"


@cache
def _titles() -> dict[str, str]:
    """Read once. The file is sixteen lines and never changes while serving."""
    if not _FILE.exists():
        return {}
    with _FILE.open(encoding="utf-8") as handle:
        return json.load(handle).get("titles", {})


def english_of(name: str) -> str:
    """This book in English letters, or "" if it has no English name."""
    return _titles().get(name, "")


def books() -> list[tuple[str, str]]:
    """Every book in the index and the source it is credited to.

    Read from the index rather than from a manifest, so the picker can only
    ever offer a book that is genuinely searchable. A book listed but not
    indexed would be a filter that always finds nothing.

    From the catalogue table the build writes, not from the passages. Asking
    the passages for DISTINCT book made FTS5 unpack every column of every row,
    which is fifteen seconds of the picker sitting empty for forty-seven names.
    """
    conn = db()
    if conn is None:
        return []
    # Ordered by source first so the list arrives grouped the way the page
    # already groups its results, one shape for the reader to learn.
    return [tuple(row) for row in conn.execute("SELECT name, source FROM book ORDER BY source, name")]


def known_books(asked: list[str]) -> tuple[str, ...]:
    """The asked books the index holds, once each, at most daleel_max_books.

    Unknown names are dropped, not refused: a bookmark naming a removed book
    searches the rest of the library instead of reading as "no book says this".
    """
    known = {name for name, _ in books()}
    most = get_settings().daleel_max_books
    return tuple(dict.fromkeys(b for b in asked[:most] if b in known))
