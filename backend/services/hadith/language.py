"""How common a word is in everyday writing, English or Arabic.

The hadith collection alone cannot tell a slip from a real word it never uses:
"jail" is in no hadith, yet nobody meant "wail". pyspellchecker's word counts
(film subtitles, ~150k words a language) say what people write. Read once per
language, folded as the index folds, so keys meet typed words.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache

from spellchecker import SpellChecker

from backend.services.hadith.words import fold


def share(word: str, lang: str) -> float:
    """The fraction of everyday `lang` ("ar" or "en") writing that is `word` (folded); 0 when unknown."""
    counts, total = _counts(lang)
    return counts.get(word, 0) / total


@lru_cache(maxsize=2)
def _counts(lang: str) -> tuple[dict[str, int], int]:
    counts = Counter()
    for word, n in SpellChecker(language=lang, distance=1).word_frequency.dictionary.items():
        counts[fold(word)] += n
    return dict(counts), sum(counts.values())
