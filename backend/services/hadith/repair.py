"""The indexed word a misspelt one was meant to be (the rule: services/spelling.py).

Candidates come from the index's `deletion` table (each indexed word, and it
with one letter dropped), the stored form of spelling.Vocabulary's filing, so
the hadith's words need not be held in memory. How common a word is mixes its
share of everyday writing with its share of the hadith, so the typed word
itself competes too: "jail" is common, so it is kept rather than made "wail",
and left to meaning search. A swap is always to a word some hadith holds; the
caller shows it as a correction.
"""
from __future__ import annotations

import sqlite3

from backend.config import get_settings
from backend.services import spelling


def nearest(conn: sqlite3.Connection, word: str, lang: str) -> str | None:
    """The likeliest meant word in `lang` ("ar" or "en"), or None when nothing is close or the typed word wins.

    A word's frequency is its share of everyday writing and of the hadith,
    mixed `hadith_repair_everyday_weight` to the rest.
    """
    entries = sorted(spelling.variants(word))
    try:
        rows = dict(conn.execute(
            "SELECT DISTINCT w.spelling, w.n FROM deletion d "
            "JOIN word w ON w.spelling = d.spelling AND w.lang = d.lang "
            f"WHERE d.lang = ? AND d.variant IN ({','.join('?' * len(entries))})",
            (lang, *entries),
        ).fetchall())
    except sqlite3.OperationalError:
        # An index built before the deletion table existed.
        return None

    total = conn.execute("SELECT SUM(n) FROM word WHERE lang = ?", (lang,)).fetchone()[0] or 1
    weight = get_settings().hadith_repair_everyday_weight

    def frequency(spelt: str) -> float:
        return weight * spelling.everyday(spelt, lang) + (1 - weight) * rows.get(spelt, 0) / total

    return spelling.best(word, rows, frequency)
