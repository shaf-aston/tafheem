"""Which known word a misspelt one was meant to be, for every search with typo
help (Hadith, Dictionary, Qur'an). Each brings its own known words and how
common each is; nothing here knows a module.

One rule for every slip: a letter missing, added, swapped with its neighbour
or replaced (ظ for ض, chairty for charity) is one edit, and so is a long vowel
spelt doubled (jibreel for jibril), however many letters. A word may be
`spelling_edits_per_letter` wrong (one slip in a short word, two in a long
one). The winner is the one a typist most likely meant: common and few edits
away, each slip costing `spelling_edit_cost` in log-frequency. The typed word
competes too, so a real word ("jail") is kept rather than "fixed".

Near words are found by lookup, not by comparing against every word: each
known word is filed under itself and under it with one letter dropped, and so
is the typed word (also with its doubled long vowels written single). That
finds a word one slip away, or a doubled long vowel off; a word two slips away
shares no entry with it and is not found.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from functools import lru_cache
from typing import Callable, Iterable, Mapping

from spellchecker import SpellChecker

from backend.config import get_settings
from backend.services.arabic_text import bare_letters, has_arabic

def fold(word: str) -> str:
    """The word (or text) as the indexes spell it; ة as ه, since typists write الجنه for الجنة."""
    return bare_letters(word).replace("ة", "ه") if has_arabic(word) else word.lower()


def deletes(word: str) -> set[str]:
    """The word with each one letter dropped."""
    return {word[:i] + word[i + 1:] for i in range(len(word))}


def respell(word: str) -> str:
    """The word with each doubled long vowel written single: dawood as dawud."""
    for doubled, single in get_settings().spelling_long_vowels.items():
        word = word.replace(doubled, single)
    return word


def variants(word: str) -> set[str]:
    """The entries a word one slip from `word` may be filed under."""
    respelled = respell(word)
    return {word, respelled} | deletes(word) | deletes(respelled)


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
    return min(edits(typed, known), 1 + edits(respell(typed), known))


def allowed(length: int) -> int:
    """The slips a word of `length` letters may be off: `spelling_edits_per_letter` of it, at least one."""
    return max(1, int(length * get_settings().spelling_edits_per_letter))


def best(word: str, candidates: Iterable[str], frequency: Callable[[str], float]) -> str | None:
    """The likeliest meant word among `candidates`, or None when nothing is close or the typed word wins."""
    settings = get_settings()
    if len(word) < settings.spelling_min_letters:
        return None
    limit = allowed(len(word))
    typed = frequency(word)
    best_score, best_word = (math.log(typed), None) if typed else (-math.inf, None)
    for known in candidates:
        distance = slips(word, known)
        if 1 <= distance <= limit and (common := frequency(known)):
            score = math.log(common) - distance * settings.spelling_edit_cost
            if score > best_score:
                best_score, best_word = score, known
    return best_word


def everyday(word: str, lang: str) -> float:
    """The fraction of everyday `lang` ("ar" or "en") writing that is `word` (folded); 0 when unknown.

    A search's own text cannot tell a slip from a real word it never uses:
    "jail" is in no hadith, yet nobody meant "wail". pyspellchecker's word
    counts (film subtitles, ~150k words a language) say what people write.
    """
    counts, total = _everyday_counts(lang)
    return counts.get(word, 0) / total


@lru_cache(maxsize=2)
def _everyday_counts(lang: str) -> tuple[dict[str, int], int]:
    counts = Counter()
    for word, n in SpellChecker(language=lang, distance=1).word_frequency.dictionary.items():
        counts[fold(word)] += n
    return dict(counts), sum(counts.values())


def everyday_weights(words: Iterable[str], lang: str) -> dict[str, float]:
    """Each word's everyday share, every word counted as seen once more, so one
    everyday writing never uses can still be the word meant."""
    counts, total = _everyday_counts(lang)
    return {w: (counts.get(fold(w), 0) + 1) / total for w in words}


class Vocabulary:
    """Known words held in memory, each with how common it is, filed for near lookup."""

    def __init__(self, frequency: Mapping[str, float]):
        self._frequency = frequency
        self._filed: dict[str, set[str]] = defaultdict(set)
        for known in frequency:
            for entry in {known} | deletes(known):
                self._filed[entry].add(known)

    def holds(self, part: str) -> bool:
        """Whether some known word is or contains `part` (رحمن inside الرحمن)."""
        return part in self._frequency or any(part in known for known in self._frequency)

    def nearest(self, word: str) -> str | None:
        """The known word `word` was likeliest meant to be, or None when nothing is close or the typed word wins."""
        near = set().union(*(self._filed.get(v, ()) for v in variants(word)))
        return best(word, near, lambda w: self._frequency.get(w, 0))
