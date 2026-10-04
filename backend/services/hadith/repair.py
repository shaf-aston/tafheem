"""The indexed word a misspelt one was meant to be.

One rule for every slip: a letter missing, added, swapped with its neighbour
or replaced (ظ for ض, chairty for charity) is one edit. Candidates come from
the `deletion` table (each indexed word, and it with one letter dropped): any
word one slip away shares an entry with the typed word, as do some two slips
away (a letter dropped and another added). The winner is the one a typist
most likely meant: common in the hadith and few edits away. The answer is
always a word some hadith holds; the caller shows it as a correction.
"""
from __future__ import annotations

import math
import sqlite3

from backend.services.hadith.words import deletes

# Below this a word is mostly particle; one edit turns it into too many others.
_MIN_LETTERS = 3


def edits(a: str, b: str) -> int:
    """Letters missing, added, replaced, or swapped with a neighbour, to turn a into b."""
    rows = [list(range(len(b) + 1))]
    for i, ca in enumerate(a, 1):
        row = [i]
        for j, cb in enumerate(b, 1):
            row.append(min(rows[-1][j] + 1, row[j - 1] + 1, rows[-1][j - 1] + (ca != cb)))
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                row[j] = min(row[j], rows[-2][j - 2] + 1)
        rows.append(row)
    return rows[-1][-1]


def nearest(conn: sqlite3.Connection, word: str, lang: str, *, edits_per_letter: float, edit_cost: float) -> str | None:
    """The likeliest meant word in `lang` ("ar" or "en"), or None when nothing is close.

    A word may be `edits_per_letter` wrong (a quarter: one slip in a short word,
    two in a long one). Each edit costs `edit_cost` in log-frequency, so a word
    one edit further must be that much more common to win.
    """
    if len(word) < _MIN_LETTERS:
        return None
    allowed = max(1, int(len(word) * edits_per_letter))
    variants = sorted({word} | deletes(word))
    try:
        rows = conn.execute(
            "SELECT DISTINCT w.spelling, w.n FROM deletion d "
            "JOIN word w ON w.spelling = d.spelling AND w.lang = d.lang "
            f"WHERE d.lang = ? AND d.variant IN ({','.join('?' * len(variants))})",
            (lang, *variants),
        ).fetchall()
    except sqlite3.OperationalError:
        # An index built before the deletion table existed.
        return None

    best: tuple[float, str] | None = None
    for spelling, n in rows:
        distance = edits(word, spelling)
        if 1 <= distance <= allowed:
            score = math.log(n) - distance * edit_cost
            if best is None or score > best[0]:
                best = (score, spelling)
    return best[1] if best else None
