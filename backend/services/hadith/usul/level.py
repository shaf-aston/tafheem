"""A narrator's level, read from the words of his grade. Pure: no I/O.

Ibn Hajar ranks narrators in twelve levels, each with the words that put one
there (data/usul/usul.json). The grade and the terms are folded the same way,
so سيء and سيئ, يخطىء and يخطئ are one word. Terms match whole words, longest
first, and a matched span is taken out before a shorter term looks, so
مجهول الحال is level 7 and not 9. The level is the highest matched; the words
no term took come back as they are, never guessed at. A level with `under`
falls short of that level (Ibn Hajar's fifth: "من قصر عن الرابعة قليلا"), so its
terms count only where nothing above `under` was said: ثقة رمي بالتشيع stays 3.
"""
from __future__ import annotations

from functools import lru_cache

from backend.services.arabic_text import bare_letters

# A grade is split on spaces; what is left of a word once these are off is its letters.
_EDGE = "،؛؟.,:;()[]«»\"'"
_SEATS = str.maketrans({"ئ": "ء", "ؤ": "ء"})


@lru_cache(maxsize=None)
def fold_word(word: str) -> str:
    """Letters only, one alef, one hamza: a hamza on a yeh seat is a bare hamza (سيئ, سيء, يخطىء, يخطئ)."""
    return bare_letters(word.strip(_EDGE)).translate(_SEATS).replace("يء", "ء")


def _terms(levels: list[dict]) -> list[tuple[int, str, tuple[str, ...]]]:
    """(level, term, its folded words) for every term, the longest first."""
    found = [(row["level"], term, tuple(fold_word(w) for w in term.split())) for row in levels for term in row["terms"]]
    return sorted(found, key=lambda t: (-len(t[2]), -sum(map(len, t[2]))))


def level_of(grade_ar: str, levels: list[dict]) -> tuple[int | None, list[str], str]:
    """(highest level matched or None, the terms matched in the order said, the words left over)."""
    shown = [w for w in grade_ar.split() if fold_word(w)]
    left: list[str | None] = [fold_word(w) for w in shown]
    hits: list[tuple[int, int, str]] = []
    for level, term, words in _terms(levels):
        i = 0
        while i <= len(left) - len(words):
            if tuple(left[i:i + len(words)]) == words:
                hits.append((i, level, term))
                left[i:i + len(words)] = [None] * len(words)
                i += len(words)
            else:
                i += 1
    hits.sort()
    under = {row["level"]: row["under"] for row in levels if "under" in row}
    top = min((level for _, level, _ in hits), default=None)
    counted = [level for _, level, _ in hits if level not in under or top >= under[level]]
    return (max(counted, default=None),
            [term for _, _, term in hits],
            " ".join(w for w, kept in zip(shown, left) if kept is not None))


def kind_of(level: int, matched: list[str], levels: list[dict]) -> str:
    """The sort of weakness: the level's own kind, unless a matched term says otherwise (رمي is an innovation)."""
    row = next(r for r in levels if r["level"] == level)
    return next((row["kinds"][t] for t in matched if t in row.get("kinds", {})), row["kind"])
