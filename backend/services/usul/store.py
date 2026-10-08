"""Read usul.db: where a chain's weak narrators are named, and the scale they sit on.

The only reader of usul.db. Built by scripts/build_usul.py, never written
while serving. Missing is a valid state: a hadith then looks as it did before
weak points, with no notes and no scale.
"""
from __future__ import annotations

from backend.config import data_path
from backend.services.readonly_db import ReadOnlyDb
from backend.services.usul.rule import rule

_db = ReadOnlyDb(lambda: data_path("usul_index_path"))


def is_built() -> bool:
    return _db() is not None


def notes(collection: str, book: int, chains: dict[str, list[list[int]]]) -> dict[str, list[dict]]:
    """{"1620a": [{at, id, level, kind, grade}, ...]}: each weak narrator named in a book's hadith, in text order.

    Kept only where `chains` (rijal.store.chains of the same book) still names that
    narrator at that place, so a rijal.db rebuilt after usul.db shows no stale note."""
    placed = {(key, start, who) for key, names in chains.items() for start, _, who in names}
    db = _db()
    found: dict[str, list[dict]] = {}
    if db:
        for number, part, at, who, level, kind, grade in db.execute(
            "SELECT note.number, note.part, note.at, note.narrator_id, note.level, note.kind, narrator_level.grade "
            "FROM note JOIN narrator_level ON narrator_level.narrator_id = note.narrator_id "
            "WHERE note.collection = ? AND note.book = ? ORDER BY note.number, note.part, note.at", (collection, book)
        ):
            if (f"{number}{part}", at, who) not in placed:
                continue
            found.setdefault(f"{number}{part}", []).append(
                {"at": at, "id": who, "level": level, "kind": kind, "grade": grade})
    return found


def scale() -> list[dict]:
    """The twelve levels as the page prints them, none while usul.db is not built.

    A level's lift is keyed by kind: level 5 lifts for a memory fault, not for an innovation."""
    if not is_built():
        return []
    cfg = rule()
    books = {key: book["label"] for key, book in cfg["sources"].items()}
    out = []
    for row in cfg["levels"]:
        kinds = {row["kind"], *row.get("kinds", {}).values()}
        lifts = {kind: found for kind in kinds if (found := cfg["lift"].get(str(row["level"])) or cfg["lift"].get(kind))}
        out.append({
            "level": row["level"], "ar": row["ar"], "en": row["en"], "kind": row["kind"],
            "weak": row["level"] >= cfg["weak_from"], "source": books[cfg["levels_source"]],
            "lift": {kind: {"en": found["en"], "lifts": found.get("lifts", True), "quote": found["quote"],
                            "source": books[found["book"]]} for kind, found in lifts.items()},
        })
    return out
