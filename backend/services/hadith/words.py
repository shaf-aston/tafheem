"""What a typed hadith query is made of. Pure: no file, no database.

Words are kept in the spelling the index keeps (marks and variants folded off
Arabic, English lowered). A number becomes the ways a hadith writes it. Which
words are too common to search for is decided by the index (search.py), never
by a list here.
"""
from __future__ import annotations

import re

from num2words import num2words

from backend.services.arabic_text import bare_letters, has_arabic

ARABIC_WORD = re.compile("[ء-ي]{2,}")
ENGLISH_WORD = re.compile("[a-z]{2,}")
# A written Arabic word with its marks, as the analyser wants it.
ARABIC_TOKEN = re.compile("[ء-ْٰ]+")
_NUMBER = re.compile("[0-9]+")
# Larger than any count a hadith gives; past it a "number" is an id, not a count.
_MAX_NUMBER = 1_000_000


def fold(word: str) -> str:
    """The word (or text) as the index spells it; ة as ه, since typists write الجنه for الجنة."""
    return bare_letters(word).replace("ة", "ه") if has_arabic(word) else word.lower()


def tokens(query: str) -> list[tuple[str, str]]:
    """(typed, folded) for each word or number in the query, in order, repeats once."""
    seen: dict[str, str] = {}
    for typed in query.split():
        folded = fold(typed.strip('"\'.,;:!?()[]،؛؟'))
        if (ARABIC_WORD.fullmatch(folded) or ENGLISH_WORD.fullmatch(folded) or _NUMBER.fullmatch(folded)) \
                and folded not in seen:
            seen[folded] = typed
    return [(typed, folded) for folded, typed in seen.items()]


def is_number(folded: str) -> bool:
    return bool(_NUMBER.fullmatch(folded)) and int(folded) < _MAX_NUMBER


def number_phrases(folded: str) -> list[list[str]]:
    """The ways a translation writes a number, each as its words: 99, ninety nine.

    English only: the Arabic joins and declines its number words (وتسعين,
    تسعة وتسعون), so a written-out Arabic number is typed as words, not digits.
    """
    return [[folded], ENGLISH_WORD.findall(num2words(int(folded)).lower())]


def respell(word: str, long_vowels: dict[str, str]) -> str:
    """The word with each doubled long vowel written single: dawood as dawud."""
    for doubled, single in long_vowels.items():
        word = word.replace(doubled, single)
    return word


def deletes(word: str) -> set[str]:
    """The word with each one letter dropped."""
    return {word[:i] + word[i + 1:] for i in range(len(word))}
