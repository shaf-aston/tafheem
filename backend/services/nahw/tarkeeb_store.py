"""The Qur'an's tarkeeb as scholars recorded it, read from data/tarkeeb/tarkeeb.db.

The only thing that opens that database. It is built once by
scripts/nahw/build_tarkeeb.py from the Quranic Treebank; see that script for where
the data comes from and what it has to pass before it is written.

Not every ayah is in here. An ayah whose arrows cross cannot be drawn as
brackets at all, so it is left out rather than drawn wrong; 5,023 of the 6,236
are present. The rest fall back to the rules in tarkeeb.py, which say less but
say it honestly.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from backend.services.nahw import book as nahw_book
from backend.services.text.arabic_text import alef_written_out
from backend.services.text.arabic_text import words as split_words
from backend.services.core.readonly_db import ReadOnlyDb

DATABASE = Path(__file__).parent.parent.parent / "data" / "tarkeeb" / "tarkeeb.db"

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


# The Uthmani rasm and the everyday spelling differ in the long-vowel letters (أموات is مت
# in the record, موت typed) and in an assimilated ل (الليل is ليل, typed لليل). What both
# spellings keep is the consonant skeleton, so that is the second key.
_LONG_VOWELS = str.maketrans("", "", "وىي")


def skeleton(letters_key: str) -> str:
    """A `letters` key with the long-vowel letters inside each word dropped and each run of one
    letter made one. A word's first letter stays: it may be the و or ي that is a word of its own
    (وَالْحَمْدُ is not الْحَمْدُ) or a present's prefix."""
    folded = [word[:1] + re.sub(r"(.)\1+", r"\1", word[1:].translate(_LONG_VOWELS)) for word in letters_key.split()]
    return " ".join(word for word in folded if word)


def _index(conn: sqlite3.Connection | None) -> dict[str, tuple[int, int] | None]:
    """Each ayah by its skeleton; None where two ayahs share one, so a collision never picks.
    Worked out once per build of the file (ReadOnlyDb.per_build), so a rebuilt or swapped
    database never answers from the last one's index."""
    found: dict[str, tuple[int, int] | None] = {}
    for row in conn.execute("SELECT surah, ayah, letters FROM tarkeeb") if conn else ():
        key = skeleton(row["letters"])
        found[key] = None if key in found else (row["surah"], row["ayah"])
    return found


def find(sentence: str) -> tuple[int, int, list[int]] | None:
    """The ayah a typed sentence is, word for word, and which of its columns
    were written (the rest, (هُوَ) or an elided khabar, are the book's), or None.

    Looked up by the Uthmani spelling first, then by the skeleton both spellings share; the
    second counts only when no other ayah has it and the record wrote as many words as were
    typed, so no column can slip."""
    db = _db()
    if db is None:
        return None
    typed = letters(split_words(sentence))
    try:
        row = db.execute("SELECT surah, ayah, written FROM tarkeeb WHERE letters = ?", (typed,)).fetchone()
        if row is None and (ayah := _db.per_build(db, _index).get(skeleton(typed))):
            row = db.execute("SELECT surah, ayah, written FROM tarkeeb WHERE surah = ? AND ayah = ?", ayah).fetchone()
            if row is not None and len(json.loads(row["written"])) != len(typed.split()):
                row = None
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
