"""The Qur'an's tarkeeb as scholars recorded it, read from data/tarkeeb/tarkeeb.db.

The only thing that opens that database. It is built once by
scripts/build_tarkeeb.py from the Quranic Treebank; see that script for where
the data comes from and what it has to pass before it is written.

Not every ayah is in here. An ayah whose arrows cross cannot be drawn as
brackets at all, so it is left out rather than drawn wrong; 5,023 of the 6,236
are present. The rest fall back to the rules in tarkeeb.py, which say less but
say it honestly.
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.services import tarkeeb
from backend.services.readonly_db import ReadOnlyDb

DATABASE = Path(__file__).parent.parent / "data" / "tarkeeb" / "tarkeeb.db"

_db = ReadOnlyDb(lambda: DATABASE)


def is_built() -> bool:
    return DATABASE.exists()


def _named(node: dict, count: list[int]) -> None:
    """Count the words whose job is actually named, so coverage is measured, not claimed."""
    if node.get("children"):
        for child in node["children"]:
            _named(child, count)
    elif node.get("role"):
        count[0] += 1


def for_ayah(surah: int, ayah: int) -> dict | None:
    """One ayah's recorded tarkeeb, or None when it is not in the database."""
    db = _db()
    if db is None:
        return None
    row = db.execute(
        "SELECT words, tree FROM tarkeeb WHERE surah = ? AND ayah = ?", (surah, ayah)
    ).fetchone()
    if row is None:
        return None

    settings = tarkeeb._rules()["treebank"]
    words = json.loads(row["words"])
    tree = json.loads(row["tree"])
    named = [0]
    _named(tree, named)
    return {
        "words": words,
        "tree": tree,
        "coverage": round(named[0] / len(words), 2) if words else 0.0,
        # Which text stands for a word that is understood but not written. The
        # page draws those columns quietly; it is told the mark rather than
        # knowing it, so the mark stays a single value in the rules file.
        "unwritten": {"mark": settings["unwritten_mark"], "note": settings["unwritten_note"]},
    }
