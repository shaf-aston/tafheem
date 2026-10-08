"""Read rijal.db: narrators, who they taught and learnt from, and where each is named in the hadith.

The only reader of rijal.db. Built by scripts/build_rijal.py, never written
while serving. Missing is a valid state: the router says "not built" rather
than pretending nobody narrated anything.
"""
from __future__ import annotations

import json
import re

from backend.config import data_path
from backend.services.hadith import loader, words
from backend.services.readonly_db import ReadOnlyDb

_db = ReadOnlyDb(lambda: data_path("rijal_index_path"))
_SUMMARY = "n.id, n.name_ar, n.name_en, n.grade_ar, n.grade_rank"


_counts: tuple | None = None  # (db stamp, [(narrator id, hadith named in), ...] most first)


def _generations() -> list[dict]:
    return json.loads((data_path("rijal_dir") / "rijal.json").read_text(encoding="utf-8"))["generations"]


def _ranked(db) -> list[tuple[int, int]]:
    """Every narrator named in a hadith with how many hadith name him, most first. One ~1 s scan per build of the file."""
    global _counts
    stamp = _db.stamp()
    if _counts is None or _counts[0] != stamp:
        rows = db.execute("SELECT narrator_id, COUNT(DISTINCT collection || number || part) n FROM mention "
                          "GROUP BY narrator_id ORDER BY n DESC, narrator_id").fetchall()
        _counts = (stamp, [(r[0], r[1]) for r in rows])
    return _counts[1]


def narrators(generation: str, offset: int, limit: int) -> dict:
    """A page of narrators by how many hadith name them; `generation` is a key of rijal.json's groups, "" for all."""
    db = _db()
    groups = _generations()
    if not db:
        return {"items": [], "total": 0, "generations": groups}
    ranked = _ranked(db)
    group = next((g for g in groups if g["key"] == generation), None)
    marks = ",".join("?" * len(group["tabaqat"])) if group else ""
    keep = {r[0] for r in db.execute(  # a mention can name someone with no page yet
        "SELECT id FROM narrator" + (f" WHERE generation_ar IN ({marks})" if group else ""), group["tabaqat"] if group else ())}
    ranked = [r for r in ranked if r[0] in keep]
    page = ranked[offset:offset + limit]
    by_id = {r["id"]: dict(r) for r in db.execute(
        f"SELECT {_SUMMARY}, n.generation_ar, n.years, n.city_ar FROM narrator n "
        f"WHERE n.id IN ({','.join('?' * len(page))})", [p[0] for p in page])}
    return {"items": [{**by_id[i], "hadith_count": n} for i, n in page if i in by_id],
            "total": len(ranked), "generations": groups}


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
        "books": json.loads(row["books"]),
        "facts": json.loads(row["facts"]),
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
        "SELECT DISTINCT collection, book, number, part FROM mention WHERE narrator_id = ? "
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


def family(collection: str, number: int) -> list[dict]:
    """Every lettered part of one number: its narrators in text order and the Arabic said after the last of them."""
    db = _db()
    rows = db.execute(
        "SELECT m.book, m.part, m.end, n.id, n.name_ar FROM mention m JOIN narrator n ON n.id = m.narrator_id "
        "WHERE m.collection = ? AND m.number = ? ORDER BY m.part, m.ord", (collection, number)) if db else []
    parts: dict[str, dict] = {}
    for book, part, end, who, name in rows:
        found = parts.setdefault(part, {"part": part, "book": book, "narrators": [], "end": 0})
        found["narrators"].append({"id": who, "name": name})
        found["end"] = max(found["end"], end)
    for found in parts.values():
        text = next((h["arabic"] for h in loader.hadiths(collection, found["book"])
                     if h["number"] == number and h["part"] == found["part"]), "")
        found["said"] = re.sub(r"^[\s\W_]+", "", text[found.pop("end"):])
    return list(parts.values())
