"""The Qur'an's word-by-word English, read from the local build.

This module is the only thing that opens meanings.db. Everything else asks it,
the same rule quran_corpus.py follows for the grammar, for the same reason.

Built by scripts/build_quran_meanings.py. If it has never been run the database
is simply absent, and `is_built()` is False: callers then fall back to fetching
one ayah at a time over the network, which is what the app did before. Nothing
here fails loudly for a missing file, because a missing file is a valid state;
it means "not built yet", not "broken".
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.services.readonly_db import ReadOnlyDb

DATA_DIR = Path(__file__).parent.parent / "data" / "quran"
DATABASE = DATA_DIR / "meanings.db"


def is_built() -> bool:
    return DATABASE.exists()


_db = ReadOnlyDb(lambda: DATABASE)


def for_ayah(surah: int, ayah: int) -> dict[int, str]:
    """One ayah's English, keyed by word number. Empty if it was never built."""
    db = _db()
    if db is None:
        return {}
    rows = db.execute(
        "SELECT word, en FROM meaning WHERE surah = ? AND ayah = ?", (surah, ayah)
    ).fetchall()
    return {row["word"]: row["en"] for row in rows}


def for_surah(surah: int) -> dict[int, dict[int, str]]:
    """A whole surah's English in one query, as {ayah: {word: english}}.

    One query rather than one per ayah is the entire point of this module: it is
    what turns reading a surah from hundreds of round trips into a single read.
    """
    db = _db()
    if db is None:
        return {}
    english: dict[int, dict[int, str]] = {}
    for row in db.execute(
        "SELECT ayah, word, en FROM meaning WHERE surah = ? ORDER BY ayah, word", (surah,)
    ):
        english.setdefault(row["ayah"], {})[row["word"]] = row["en"]
    return english


def surah_names() -> dict[int, dict]:
    """Every surah's name and length, for the reader's picker. Empty if unbuilt."""
    db = _db()
    if db is None:
        return {}
    return {
        row["id"]: {"name_en": row["name_en"], "name_ar": row["name_ar"], "ayahs": row["ayahs"]}
        for row in db.execute("SELECT id, name_en, name_ar, ayahs FROM surah ORDER BY id")
    }


def uthmani_for_ayah(surah: int, ayah: int) -> dict[int, str]:
    """One ayah's printed Uthmani spelling (waqf marks included), keyed by word
    number. Empty if the build predates this table or was never run."""
    db = _db()
    if db is None:
        return {}
    try:
        rows = db.execute(
            "SELECT word, ar FROM uthmani WHERE surah = ? AND ayah = ?", (surah, ayah)
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {row["word"]: row["ar"] for row in rows}


def ayah_end_mark(surah: int, ayah: int) -> str | None:
    """The ring-and-number that closes a printed ayah, or None if unbuilt."""
    db = _db()
    if db is None:
        return None
    try:
        row = db.execute(
            "SELECT number FROM ayah_end WHERE surah = ? AND ayah = ?", (surah, ayah)
        ).fetchone()
    except sqlite3.OperationalError:
        return None
    return f"۝{row['number']}" if row else None


def surah_name(surah: int) -> dict | None:
    db = _db()
    if db is None:
        return None
    row = db.execute(
        "SELECT name_en, name_ar, ayahs FROM surah WHERE id = ?", (surah,)
    ).fetchone()
    return dict(row) if row else None
