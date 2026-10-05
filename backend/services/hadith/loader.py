"""Read hadith.db: collections, their books, and the hadiths in each book.

The only reader of hadith.db. Built by scripts/build_hadith_index.py, never
written while serving. Missing is a valid state, same as daleel.db before it
is built: the router says so rather than pretending the collection is empty.
"""
from __future__ import annotations

import json
import sqlite3
from functools import lru_cache

from backend.config import data_path


def is_built() -> bool:
    return data_path("hadith_index_path").exists()


def _connect() -> sqlite3.Connection:
    path = data_path("hadith_index_path")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


@lru_cache(maxsize=1)
def collections() -> list[tuple[str, str, str, bool]]:
    """Every collection's id, name, short name and whether all of it is sahih, in the order the database holds them."""
    if not is_built():
        return []
    conn = _connect()
    try:
        return [(cid, name, short, bool(sahih)) for cid, name, short, sahih in
                conn.execute("SELECT id, name, short, sahih FROM collection ORDER BY rowid")]
    finally:
        conn.close()


@lru_cache(maxsize=8)
def collection_name(collection_id: str) -> str | None:
    return next((name for cid, name, *_ in collections() if cid == collection_id), None)


@lru_cache(maxsize=8)
def cite_of(collection_id: str) -> str:
    if not is_built():
        return ""
    conn = _connect()
    try:
        row = conn.execute("SELECT cite FROM collection WHERE id = ?", (collection_id,)).fetchone()
        return row[0] if row else ""
    finally:
        conn.close()


def cite_url(template: str, number: int, part: str) -> str:
    """sunnah.com's page for one narration; the letter picks it out of those sharing a number (muslim:157c)."""
    return template.replace("{number}", f"{number}{part}") if template else ""


@lru_cache(maxsize=8)
def books(collection_id: str) -> list[dict]:
    """Every book of a collection, each with how many hadiths it holds."""
    if not is_built():
        return []
    conn = _connect()
    try:
        return [
            {"number": number, "name": name, "count": count}
            for number, name, count in conn.execute(
                "SELECT b.number, b.name, count(h.rowid) "
                "FROM book b LEFT JOIN hadith h "
                "  ON h.collection_id = b.collection_id AND h.book_number = b.number "
                "WHERE b.collection_id = ? GROUP BY b.number ORDER BY b.number",
                (collection_id,),
            )
        ]
    finally:
        conn.close()


def hadiths(collection_id: str, book_number: int) -> list[dict]:
    """Every hadith in one book, in the order sunnah.com prints them."""
    if not is_built():
        return []
    conn = _connect()
    try:
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
    finally:
        conn.close()


def numbered(collection_id: str, number: int, part: str = "") -> tuple[int, list[tuple]]:
    """The hadith carrying this number (every lettered part, unless one letter is asked).

    A number the collection does not use gives the nearest number it does
    (Muslim starts at 8), returned first so the caller can say so.
    Rows are (collection, book, number, part, arabic, english, grades), search's shape.
    """
    if not is_built():
        return number, []
    conn = _connect()
    try:
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
    finally:
        conn.close()
