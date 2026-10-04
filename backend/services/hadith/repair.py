"""The indexed word a misspelt one was meant to be.

A misspelling shares most of its three-letter runs with the word meant, so the
`word` table (every distinct word in the index, trigram-tokenised) is asked for
the words sharing the most runs, and the closest of those by letter-for-letter
likeness is taken when it is close enough. Nothing is guessed from meaning:
the answer is always a word some hadith actually holds, and the caller shows
it as a correction rather than passing it off as what was typed.
"""
from __future__ import annotations

import difflib
import math
import sqlite3

# The trigram tokenizer cannot see anything shorter than three letters; a
# shorter word is matched exactly or not at all.
_TRIGRAM_MIN = 3


def nearest(conn: sqlite3.Connection, word: str, lang: str, *, min_ratio: float, candidates: int) -> str | None:
    """The closest indexed word in `lang` ("ar" or "en"), or None when none is close enough.

    Among words equally close the more frequent wins: الجنة over الجن for الجنه.
    """
    if len(word) < _TRIGRAM_MIN:
        return None
    runs = {word[i:i + _TRIGRAM_MIN] for i in range(len(word) - _TRIGRAM_MIN + 1)}
    match = " OR ".join('"' + run.replace('"', "") + '"' for run in runs)
    try:
        rows = conn.execute(
            "SELECT spelling, n FROM word WHERE word MATCH ? AND lang = ? ORDER BY rank LIMIT ?",
            (match, lang, candidates),
        ).fetchall()
    except sqlite3.OperationalError:
        # An index built before the word table existed, or a run FTS5 cannot parse.
        return None

    best: tuple[float, float, str] | None = None
    for found, n in rows:
        ratio = difflib.SequenceMatcher(None, word, found).ratio()
        if ratio >= min_ratio and (best is None or (ratio, math.log(n)) > best[:2]):
            best = (ratio, math.log(n), found)
    return best[2] if best else None
