"""What a typed hadith query is made of. Pure: no file, no database.

A word is kept in the spelling the index keeps (marks and variants folded off
Arabic, English lowered), its attached particles are taken off so الصبر finds
بالصبر and وصبروا, and the words that are in almost every hadith are dropped
when anything else is left to search for.
"""
from __future__ import annotations

import re

from backend.services.arabic_text import bare_letters, has_arabic
from backend.services.noise_words import ENGLISH_NOISE

# What an isnad and a translator put in nearly every hadith. Searching for them
# narrows nothing; "hadith about the man who prayed" must search for the man
# and the prayer. Dropped only when a real word remains, so قال on its own is
# still a search for قال.
ARABIC_NOISE = frozenset("قال عن بن ابن حدثنا اخبرنا سمعت ان الله عليه صلى وسلم رسول النبي من في الى على ما لا و".split())
HADITH_NOISE = ENGLISH_NOISE | frozenset("hadith hadeeth narrated narrates prophet messenger allah said".split())

# Particles written onto the front of an Arabic word: و ف (and, so), ب ل ك
# (with, for, like), ال (the), and their joins. Longest first so وال is taken
# as one piece. Nothing is taken off the end: suffixes change the word's shape
# too much to be sure of, and prefix matching already reaches صبر from صبروا.
_PREFIXES = ("وبال", "فبال", "وال", "فال", "بال", "كال", "ولل", "لل", "ال", "وب", "ول", "فب", "فل", "و", "ف", "ب", "ل", "ك")
# A stem shorter than this is a particle itself, not a word: ولم must stay ولم.
_MIN_STEM = 3

ARABIC_WORD = re.compile("[ء-ي]{2,}")
ENGLISH_WORD = re.compile("[a-z]{2,}")


def fold(word: str) -> str:
    """The word (or text) as the index spells it; ة as ه, since typists write الجنه for الجنة."""
    return bare_letters(word).replace("ة", "ه") if has_arabic(word) else word.lower()


def stem(word: str) -> str:
    """The folded word without its front particles, when enough word is left."""
    for prefix in _PREFIXES:
        if word.startswith(prefix) and len(word) - len(prefix) >= _MIN_STEM:
            return word[len(prefix):]
    return word


def stems(folded_text: str) -> str:
    """Every word of a folded Arabic text stemmed, for the index's stem column."""
    return " ".join(stem(w) for w in ARABIC_WORD.findall(folded_text))


def content_words(query: str) -> list[tuple[str, str]]:
    """(typed, folded) for each word worth searching, in the order typed.

    Noise is dropped only when something else remains; punctuation-only tokens
    never count. Repeats are kept once.
    """
    seen: dict[str, str] = {}
    for typed in query.split():
        folded = fold(typed.strip('"\'.,;:!?()[]،؛؟'))
        if (ARABIC_WORD.search(folded) or ENGLISH_WORD.search(folded)) and folded not in seen:
            seen[folded] = typed
    noise = ARABIC_NOISE | HADITH_NOISE
    content = [(typed, folded) for folded, typed in seen.items() if folded not in noise]
    return content or [(typed, folded) for folded, typed in seen.items()]
