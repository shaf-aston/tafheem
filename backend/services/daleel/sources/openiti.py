"""The classical books, as passages Daleel can quote.

One adapter, instantiated once per collection, the same shape as LibrarySource.
Which books a collection holds is data/books/openiti-books.json; this file never
names a book.

A collection rather than a source per book, and the reason is the result limit.
Daleel guarantees every matching book one slot before the rest of the list is
filled, which is what stops the Qur'an winning every place. Registering every
book would turn that guarantee against itself: thirty-four books each claiming
a slot fills a nine-result page with one line from each and pushes the Qur'an
off it entirely. Grouped, they compete for one guaranteed slot and win the rest
on merit.

These texts carry no harakat and no translation, which is not a defect to be
fixed here. It means they are quotable and searchable but cannot teach i'rab,
and the Qur'an tab remains the only place a vowelled text is shown.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from backend.services.core.readonly_db import ReadOnlyDb
from backend.services.daleel.sources.model import Passage

_BOOKS = Path(__file__).resolve().parents[3] / "data" / "books"
_DB = _BOOKS / "openiti.db"
_MANIFEST = _BOOKS / "openiti-books.json"
# This thread's read-only connection to the books, reopened when an import replaces it.
_db = ReadOnlyDb(lambda: _DB)


class OpenItiSource:
    """Every passage of every book credited to one collection."""

    def __init__(self, collection: str) -> None:
        self.id = collection

    def passages(self) -> Iterable[Passage]:
        if (conn := _db()) is None:
            return

        rows = conn.execute(
            "SELECT b.title, p.heading, p.arabic"
            "  FROM passage p JOIN book b ON b.file = p.file"
            " WHERE p.collection = ?"
            " ORDER BY p.id",
            (self.id,),
        )
        for title, heading, arabic in rows:
            yield Passage(
                source=self.id,
                book=title,
                locator=_cite(title, heading),
                arabic=arabic,
            )


def _cite(title: str, heading: str) -> str:
    """How a person would write down where they found it.

    The book first, because with thirty-four books under one badge the badge no
    longer says which one this is. Then the chapter.

    The printed page is deliberately not shown. It is the page of one scanned
    edition, so it does not lead a reader holding a different printing to the
    passage, and next to a chapter name it read as a stray number.
    """
    parts = [title]
    if heading:
        parts.append(heading)
    return " · ".join(parts)


def collections() -> list[str]:
    """The collection ids the manifest defines, in the order it defines them."""
    if not _MANIFEST.exists():
        return []
    return list(json.loads(_MANIFEST.read_text(encoding="utf-8"))["collections"])
