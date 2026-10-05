"""Read rijal.db: narrators, who they taught and learnt from, and where each is named in the hadith.

The only reader of rijal.db. Built by scripts/build_rijal.py, never written
while serving. Missing is a valid state: the router says "not built" rather
than pretending nobody narrated anything.
"""
from __future__ import annotations

import json
import re

from backend.config import data_path
from backend.services.hadith import words
from backend.services.readonly_db import ReadOnlyDb

_db = ReadOnlyDb(lambda: data_path("rijal_index_path"))
_SUMMARY = "n.id, n.name_ar, n.name_en, n.grade_ar, n.grade_rank"


def is_built() -> bool:
    return _db() is not None


def chains(collection: str, book: int) -> dict[str, list[list[int]]]:
    """{"1620a": [[start, end, narrator id], ...]}: where each narrator is named in a book's hadith, in chain order."""
    db = _db()
    found: dict[str, list[list[int]]] = {}
    if db:
        for number, part, start, end, who in db.execute(
            "SELECT number, part, start, end, narrator_id FROM mention WHERE collection = ? AND book = ? "
            "ORDER BY number, part, ord", (collection, book)
        ):
            found.setdefault(f"{number}{part}", []).append([start, end, who])
    return found


def _ties(db, narrator_id: int, side: str, other: str) -> list[dict]:
    """Narrators on one side of a link to this one, the most narrated first. side and other are tie's two columns."""
    return [dict(row) for row in db.execute(
        f"SELECT {_SUMMARY} FROM tie JOIN narrator n ON n.id = tie.{side} WHERE tie.{other} = ? "
        "ORDER BY COALESCE(n.hadith_total, 0) DESC", (narrator_id,))]


def narrator(narrator_id: int) -> dict | None:
    db = _db()
    row = db.execute("SELECT * FROM narrator WHERE id = ?", (narrator_id,)).fetchone() if db else None
    if row is None:
        return None
    return {
        **dict(row),
        "books_ar": json.loads(row["books_ar"]),
        "texts": [{"book": book, "body": body} for book, body in json.loads(row["texts"])],
        "verdicts": [dict(v) for v in db.execute(
            "SELECT scholar, quote FROM verdict WHERE narrator_id = ? ORDER BY ord", (narrator_id,))],
        "teachers": _ties(db, narrator_id, "teacher_id", "student_id"),
        "students": _ties(db, narrator_id, "student_id", "teacher_id"),
    }


def hadith_of(narrator_id: int, limit: int) -> list[dict]:
    """The hadith in the built books that name him, in number order."""
    db = _db()
    return [dict(row) for row in db.execute(
        "SELECT DISTINCT collection, number, part FROM mention WHERE narrator_id = ? "
        "ORDER BY collection, number, part LIMIT ?", (narrator_id, limit))] if db else []


def search(query: str, limit: int) -> list[dict]:
    """Narrators whose name, kunya or full name starts with every word typed; the most narrated first."""
    terms = re.findall(r"\w+", words.fold(query))
    db = _db()
    if not terms or not db:
        return []
    return [dict(row) for row in db.execute(
        f"SELECT {_SUMMARY} FROM narrator_fts JOIN narrator n ON n.id = narrator_fts.rowid "
        "WHERE narrator_fts MATCH ? ORDER BY COALESCE(n.hadith_total, 0) DESC LIMIT ?",
        (" ".join(f'"{t}"*' for t in terms), limit))]
