"""Read rijal.db: narrators, who they taught and learnt from, and where each is named in the hadith.

The only reader of rijal.db. Built by scripts/build_rijal.py, never written
while serving. Missing is a valid state: the router says "not built" rather
than pretending nobody narrated anything.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from backend.config import data_path
from backend.services.hadith import chain, loader, words
from backend.services.core.readonly_db import ReadOnlyDb

_db = ReadOnlyDb(lambda: data_path("rijal_index_path"))
_SUMMARY = "n.id, n.name_ar, n.name_en, n.grade_ar, n.grade_rank"


_counts: tuple | None = None  # (db stamp, [(narrator id, hadith named in), ...] most first)
_kin: tuple | None = None     # (db stamp, {(collection, number): lettered narrations}) where more than one


def _has(db, table: str, column: str) -> bool:
    """Whether this file has the column: a file built before it was added still serves until the next build."""
    return any(r[1] == column for r in db.execute(f"PRAGMA table_info({table})"))


def _chained(db, table: str = "mention") -> str:
    """The condition keeping a hadith's chain and leaving out names told inside its story ("" for a file built before the flag)."""
    return f"AND {table}.in_chain" if _has(db, "mention", "in_chain") else ""


@lru_cache(maxsize=1)
def rule() -> dict:
    """rijal.json, read once: the only reader of it."""
    return json.loads((data_path("rijal_dir") / "rijal.json").read_text(encoding="utf-8"))


def _ranked(db) -> list[tuple[int, int]]:
    """Every narrator in the chain of a hadith with how many hadith he is in, most first. One ~1 s scan per build of the file."""
    global _counts
    stamp = _db.stamp()
    if _counts is None or _counts[0] != stamp:
        rows = db.execute("SELECT narrator_id, COUNT(DISTINCT collection || number || part) n FROM mention "
                          f"WHERE 1 {_chained(db)} GROUP BY narrator_id ORDER BY n DESC, narrator_id").fetchall()
        _counts = (stamp, [(r[0], r[1]) for r in rows])
    return _counts[1]


def narrators(generation: str, offset: int, limit: int) -> dict:
    """A page of narrators by how many hadith name them; `generation` is a key of rijal.json's groups, "" for all."""
    db = _db()
    groups = rule()["generations"]
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
            f"SELECT number, part, start, end, narrator_id FROM mention WHERE collection = ? AND book = ? {_chained(db)} "
            "ORDER BY number, part, ord", (collection, book)
        ):
            found.setdefault(f"{number}{part}", []).append([start, end, who])
    return found


def kin(collection: str, book: int) -> dict[str, int]:
    """{"782": 3}: the lettered narrations each number of this book has across the whole collection, where more than
    one (a number's letters can sit in two books). One scan per build of the file."""
    global _kin
    db = _db()
    if not db:
        return {}
    if _kin is None or _kin[0] != _db.stamp():
        _kin = (_db.stamp(), {(c, n): k for c, n, k in db.execute(
            "SELECT collection, number, COUNT(DISTINCT part) k FROM mention GROUP BY collection, number HAVING k > 1")})
    numbers = {n for (n,) in db.execute("SELECT DISTINCT number FROM mention WHERE collection = ? AND book = ?", (collection, book))}
    return {str(n): _kin[1][collection, n] for n in numbers if (collection, n) in _kin[1]}


def _ties(db, narrator_id: int, side: str, other: str, order: str) -> list[dict]:
    """Narrators on one side of a link to this one, in the order his own page lists them (the most narrated first where
    that page was never fetched). side and other are tie's two id columns, order the column holding his page's order."""
    ranked = _has(db, "tie", order)
    first = f"tie.{order} IS NULL, tie.{order}, " if ranked else ""
    # His page is the source for his own list: a link only the other narrator's page declares is left out once his is fetched.
    own = f"AND (tie.{order} IS NOT NULL OR NOT (SELECT fetched FROM narrator WHERE id = ?)) " if ranked and _has(db, "narrator", "fetched") else ""
    args = (narrator_id, narrator_id) if own else (narrator_id,)
    return [dict(row) for row in db.execute(
        f"SELECT {_SUMMARY} FROM tie JOIN narrator n ON n.id = tie.{side} WHERE tie.{other} = ? {own}"
        f"ORDER BY {first}COALESCE(n.hadith_total, 0) DESC", args)]


def narrator(narrator_id: int) -> dict | None:
    db = _db()
    row = db.execute("SELECT * FROM narrator WHERE id = ?", (narrator_id,)).fetchone() if db else None
    if row is None:
        return None
    return {
        **dict(row),
        # False for a teacher or student known only from another narrator's lists; a build before the flag held pages only as rows with facts.
        "fetched": bool(row["fetched"]) if "fetched" in row.keys() else row["hadith_total"] is not None or row["facts"] != "[]",
        # In how many of our hadith he is in the chain: the length the hadith list below reaches before its cap.
        "hadith_count": dict(_ranked(db)).get(narrator_id, 0),
        "books": json.loads(row["books"]),
        "flags": json.loads(row["flags"]) if "flags" in row.keys() else [],
        "facts": json.loads(row["facts"]),
        # A build from before the blocks were kept holds [book, body] alone.
        "texts": [{"book": book, "body": body, "blocks": blocks[0] if blocks else []}
                  for book, body, *blocks in json.loads(row["texts"])],
        "verdicts": [dict(v) for v in db.execute(
            "SELECT scholar, quote FROM verdict WHERE narrator_id = ? ORDER BY ord", (narrator_id,))],
        "teachers": _ties(db, narrator_id, "teacher_id", "student_id", "teacher_ord"),
        "students": _ties(db, narrator_id, "student_id", "teacher_id", "student_ord"),
    }


def _said(text: str, end: int | None = None) -> str:
    """What a hadith says after its chain, where the chain reader (chain.cut_of) ends it.

    A name sunnah.com links inside the story (الحسن told of, not telling) is a mention
    too, so the last mention is not the end of the chain; `end`, the last
    mention's end, is used only where the chain reader finds no plain cut, and
    without it such a hadith gives "" rather than a guess.
    """
    at = chain.cut_of(text)
    start = at[1] if at else end
    return "" if start is None else re.sub(r"^[\s\W_]+", "", text[start:])


def hadith_of(narrator_id: int, limit: int, words: int) -> list[dict]:
    """The hadith in the built books that name him, the books in the order the tab lists them, each in number order,
    with the first `words` words said after its chain."""
    db = _db()
    if not db:
        return []
    order = [c[0] for c in loader.collections()]
    rank = "CASE collection " + " ".join("WHEN ? THEN ?" for _ in order) + f" ELSE {len(order)} END" if order else "collection"
    rows = db.execute(
        "SELECT DISTINCT collection, book, number, part FROM mention m WHERE narrator_id = ? " + _chained(db, "m") +
        f" ORDER BY {rank}, collection, number, part LIMIT ?",
        (narrator_id, *(v for i, c in enumerate(order) for v in (c, i)), limit))
    out = []
    for collection, book, number, part in rows:
        said = _said(loader.arabic(collection, number, part)).split()
        out.append({"collection": collection, "book": book, "number": number, "part": part,
                    "opening": " ".join(said[:words]) + (" …" if len(said) > words else "")})
    return out


def search(query: str, limit: int) -> list[dict]:
    """Narrators whose name, kunya or full name starts with every word typed; the most narrated first."""
    terms = re.findall(r"\w+", words.fold_en(words.fold(query)))
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
        "WHERE m.collection = ? AND m.number = ? " + _chained(db, "m") + " ORDER BY m.part, m.ord", (collection, number)) if db else []
    parts: dict[str, dict] = {}
    for book, part, end, who, name in rows:
        found = parts.setdefault(part, {"part": part, "book": book, "narrators": [], "end": 0})
        found["narrators"].append({"id": who, "name": name})
        found["end"] = max(found["end"], end)
    for found in parts.values():
        text = next((h["arabic"] for h in loader.hadiths(collection, found["book"])
                     if h["number"] == number and h["part"] == found["part"]), "")
        found["said"] = _said(text, found.pop("end"))
    return list(parts.values())
