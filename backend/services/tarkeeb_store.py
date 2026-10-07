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
import sqlite3
from pathlib import Path

from backend.services import nahw_book
from backend.services.arabic_text import alef_written_out
from backend.services.arabic_text import words as split_words
from backend.services.readonly_db import ReadOnlyDb

DATABASE = Path(__file__).parent.parent / "data" / "tarkeeb" / "tarkeeb.db"

_db = ReadOnlyDb(lambda: DATABASE)


# Letters one spelling of the Qur'an writes and another leaves out: the alef of
# ذٰلِكَ is written small, ذلك not at all; a hamza sits on a seat or on none.
_SPELLING_ONLY = str.maketrans("", "", "اءئؤ")


def is_built() -> bool:
    return DATABASE.exists()


def letters(words: list[str]) -> str:
    """What is left of an ayah's written words under any spelling of them.

    The build keys each ayah by this and a typed sentence is looked up by it,
    so the two are always folded by the same hand.
    """
    return " ".join(alef_written_out(word).translate(_SPELLING_ONLY) for word in words)


def find(sentence: str) -> tuple[int, int, list[int]] | None:
    """The ayah a typed sentence is, word for word, and which of its columns
    were written (the rest, (هُوَ) or an elided khabar, are the book's), or None."""
    db = _db()
    if db is None:
        return None
    try:
        row = db.execute("SELECT surah, ayah, written FROM tarkeeb WHERE letters = ?",
                         (letters(split_words(sentence)),)).fetchone()
    except sqlite3.OperationalError:  # built before ayahs were keyed by their letters
        return None
    return (row["surah"], row["ayah"], json.loads(row["written"])) if row else None


def for_sentence(sentence: str) -> dict | None:
    """The recorded tarkeeb of a typed sentence that is an ayah, or None.

    Carries `roles`: one entry per typed word, the role its own column was given,
    so the cards and the picture are one reading.
    """
    where = find(sentence)
    found = for_ayah(where[0], where[1]) if where else None
    if found is None:
        return None
    surah, ayah, written = where
    columns: dict[int, str] = {}
    _columns(found["tree"], columns)
    return {**found, "surah": surah, "ayah": ayah,
            "roles": [{"role": columns.get(i), "case": None} for i in written]}


def _columns(node: dict, found: dict[int, str]) -> None:
    """What each word's own column is called."""
    if node.get("children"):
        for child in node["children"]:
            _columns(child, found)
    elif "word" in node:
        found[node["word"]] = node.get("role")


def _hide(node: dict, written: set[int]) -> None:
    """Mark the leaves of columns the book supplies, (هُوَ) or an elided khabar, `hidden`."""
    if node.get("children"):
        for child in node["children"]:
            _hide(child, written)
    elif "word" in node and node["word"] not in written:
        node["hidden"] = True


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
        "SELECT words, tree, written FROM tarkeeb WHERE surah = ? AND ayah = ?", (surah, ayah)
    ).fetchone()
    if row is None:
        return None

    settings = nahw_book.tarkeeb_rules()["treebank"]
    words = json.loads(row["words"])
    tree = json.loads(row["tree"])
    _hide(tree, set(json.loads(row["written"])))
    named = [0]
    _named(tree, named)
    return {
        "words": words,
        "tree": tree,
        "coverage": round(named[0] / len(words), 2) if words else 0.0,
        # The note the page shows on a column marked `hidden` (understood, not written).
        "unwritten": {"mark": settings["unwritten_mark"], "note": settings["unwritten_note"]},
    }
