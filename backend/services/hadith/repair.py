"""The indexed word a misspelt one was meant to be.

One rule for every slip: a letter missing, added, swapped with its neighbour
or replaced (ظ for ض, chairty for charity) is one edit, and so is a long vowel
spelt doubled (jibreel for jibril), however many letters. Candidates come from
the `deletion` table (each indexed word, and it with one letter dropped): any
word one slip away shares an entry with the typed word, as do some two slips
away (a letter dropped and another added). The winner is the one a typist
most likely meant: common in writing and few edits away. How common is judged
by everyday writing (language.py) and by the hadith together, so the typed word
itself competes too: "jail" is common, so it is kept rather than made "wail",
and left to meaning search. A swap is always to a word some hadith holds; the
caller shows it as a correction.
"""
from __future__ import annotations

import math
import sqlite3

from backend.config import get_settings
from backend.services.hadith import language
from backend.services.hadith.words import deletes, respell

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


def slips(typed: str, known: str) -> int:
    """Edits from typed to known, a doubled long vowel undone (dawood as dawud) counting as one slip in all."""
    respelled = respell(typed, get_settings().hadith_repair_long_vowels)
    return min(edits(typed, known), 1 + edits(respelled, known))


def nearest(conn: sqlite3.Connection, word: str, lang: str) -> str | None:
    """The likeliest meant word in `lang` ("ar" or "en"), or None when nothing is close or the typed word wins.

    A word may be `hadith_repair_edits_per_letter` wrong (a quarter: one slip in
    a short word, two in a long one). Each slip costs `hadith_repair_edit_cost`
    in log-frequency, so a word one slip further must be that much more common
    to win. A word's frequency is its share of everyday writing and of the
    hadith, mixed `hadith_repair_everyday_weight` to the rest.
    """
    if len(word) < _MIN_LETTERS:
        return None
    settings = get_settings()
    allowed = max(1, int(len(word) * settings.hadith_repair_edits_per_letter))
    respelled = respell(word, settings.hadith_repair_long_vowels)
    variants = sorted({word, respelled} | deletes(word) | deletes(respelled))
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

    total = conn.execute("SELECT SUM(n) FROM word WHERE lang = ?", (lang,)).fetchone()[0] or 1

    def frequency(spelling: str, n: int) -> float:
        weight = settings.hadith_repair_everyday_weight
        return weight * language.share(spelling, lang) + (1 - weight) * n / total

    typed = frequency(word, 0)
    best: tuple[float, str | None] = (math.log(typed), None) if typed else (-math.inf, None)
    for spelling, n in rows:
        distance = slips(word, spelling)
        if 1 <= distance <= allowed:
            score = math.log(frequency(spelling, n)) - distance * settings.hadith_repair_edit_cost
            if score > best[0]:
                best = (score, spelling)
    return best[1]
