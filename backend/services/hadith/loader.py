"""Read hadith.db: collections, their books, and the hadiths in each book.

The only reader of hadith.db. Built by scripts/build_hadith_index.py, never
written while serving. Missing is a valid state, same as daleel.db before it
is built: the router says so rather than pretending the collection is empty.
"""
from __future__ import annotations

import json
from functools import lru_cache, wraps

from backend.config import data_path
from backend.services.arabic_text import has_arabic
from backend.services.readonly_db import ReadOnlyDb


def is_built() -> bool:
    return data_path("hadith_index_path").exists()


# This thread's read-only connection to hadith.db, reopened when a build replaces it.
db = ReadOnlyDb(lambda: data_path("hadith_index_path"))


def _per_build(empty, maxsize: int = 8):
    """Cache a read per build of hadith.db on disk (path and mtime), so a rebuild is seen; `empty` when unbuilt."""
    def wrap(read):
        def cached(stamp, *args):
            return read(*args) if stamp else empty

        cached = lru_cache(maxsize)(cached)

        return wraps(read)(lambda *args: cached(db.stamp(), *args))
    return wrap


@_per_build([], maxsize=1)
def collections() -> list[tuple[str, str, str, str, str, bool]]:
    """Every collection's id, name, short name, Arabic name, short Arabic name and whether all of it is sahih, in the order the database holds them."""
    return [(*names, bool(sahih)) for *names, sahih in
            db().execute("SELECT id, name, short, arabic, arabic_short, sahih FROM collection ORDER BY rowid")]


@_per_build(0, maxsize=2)
def total(lang: str) -> int:
    """How many words of `lang` ("ar" or "en") the hadith hold, counting each word once per hadith."""
    return db().execute("SELECT SUM(n) FROM word WHERE lang = ?", (lang,)).fetchone()[0] or 0


@_per_build(0.0, maxsize=256)
def share(word: str) -> float:
    """The fraction of the hadith text in the word's language that is this word, as the index spells it."""
    lang = "ar" if has_arabic(word) else "en"
    if not (whole := total(lang)):
        return 0.0
    row = db().execute("SELECT n FROM word WHERE lang = ? AND spelling = ?", (lang, word)).fetchone()
    return row[0] / whole if row else 0.0


def collection_name(collection_id: str) -> str | None:
    return next((name for cid, name, *_ in collections() if cid == collection_id), None)


@_per_build("")
def cite_of(collection_id: str) -> str:
    row = db().execute("SELECT cite FROM collection WHERE id = ?", (collection_id,)).fetchone()
    return row[0] if row else ""


def cite_url(template: str, number: int, part: str) -> str:
    """sunnah.com's page for one narration; the letter picks it out of those sharing a number (muslim:157c)."""
    return template.replace("{number}", f"{number}{part}") if template else ""


@_per_build([])
def books(collection_id: str) -> list[dict]:
    """Every book of a collection, each with how many hadiths it holds."""
    return [
        {"number": number, "name": name, "count": count}
        for number, name, count in db().execute(
            "SELECT b.number, b.name, count(h.rowid) "
            "FROM book b LEFT JOIN hadith h "
            "  ON h.collection_id = b.collection_id AND h.book_number = b.number "
            "WHERE b.collection_id = ? GROUP BY b.number ORDER BY b.number",
            (collection_id,),
        )
    ]


def hadiths(collection_id: str, book_number: int) -> list[dict]:
    """Every hadith in one book, in the order sunnah.com prints them."""
    if not is_built():
        return []
    conn = db()
    cite = cite_of(collection_id)
    return [
        {
            "collection": collection_id, "book": book_number, "number": number,
            "part": part, "arabic": arabic, "english": english,
            "grades": json.loads(grades), "cite": cite_url(cite, number, part),
        }
        for number, part, arabic, english, grades in conn.execute(
            "SELECT number, part, arabic, english, grades FROM hadith "
            "WHERE collection_id = ? AND book_number = ? ORDER BY number, part",
            (collection_id, book_number),
        )
    ]


def every_hadith() -> list[tuple[str, int, int, str, str]]:
    """(collection, book number, number, part, arabic) of every hadith, in every book or none."""
    if not is_built():
        return []
    return db().execute("SELECT collection_id, book_number, number, part, arabic FROM hadith").fetchall()


def numbered(collection_id: str, number: int, part: str = "") -> tuple[int, list[tuple]]:
    """The hadith carrying this number (every lettered part, unless one letter is asked).

    A number the collection does not use gives the nearest number it does
    (Muslim starts at 8), returned first so the caller can say so.
    Rows are (collection, book, number, part, arabic, english, grades), search's shape.
    """
    if not is_built():
        return number, []
    conn = db()
    near = conn.execute(
        "SELECT number FROM hadith WHERE collection_id = ? ORDER BY abs(number - ?), number LIMIT 1",
        (collection_id, number),
    ).fetchone()
    if not near:
        return number, []
    shown = near[0]
    rows = conn.execute(
        "SELECT collection_id, book_number, number, part, arabic, english, grades FROM hadith "
        "WHERE collection_id = ? AND number = ? ORDER BY part",
        (collection_id, shown),
    ).fetchall()
    # One letter asked narrows to it; a letter the number does not have shows them all.
    return shown, [r for r in rows if shown == number and r[3] == part] or rows
