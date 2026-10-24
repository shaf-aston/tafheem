"""What counts as a passage using a term: the one rule ranking and marking share."""
from __future__ import annotations

import re
from typing import Iterator

from backend.services.text import fts
from backend.services.text.arabic_text import has_arabic

# Whatever Arabic writes joined on in front of a word: and, so, with, for, like,
# the, and لل, which is ل and ال with the alef dropped.
PROCLITIC = "(?:[وف]?(?:لل|[بلك]?(?:ال)?))"
# Arabic letters as the folded text holds them, with Persian and Urdu forms and
# the presentation forms, so none of them reads as the edge of a word.
ARABIC_LETTER = "ء-يٱ-ۓﭐ-﷿ﹰ-﻿"
NOT_LETTER = f"(?![a-z{ARABIC_LETTER}])"
PROCLITIC_AT_START = re.compile(f"^{PROCLITIC}")
WORDS = re.compile(f"[a-z{ARABIC_LETTER}]+")

# A short word with a letter joined on that is a word of its own: لما is
# "when", not ل and ما, and was being passed off as a clean find for ما.
OWN_WORDS = frozenset({"لما"})


def pattern(term: str, whole: bool = False) -> re.Pattern:
    """What counts as using the term, as a pattern whose group 1 is the term.

    Containing its letters is not enough, and how much more is needed depends
    on the word. An English word has to start where a word starts, or prayer
    found "sprayer" and zakat found "zawzakat" and both were called clean
    finds. A two-letter Arabic word has to be the whole word, bar what Arabic
    joins on in front: أب was found inside الكتاب and تراب, and من inside every
    منه. A longer Arabic word keeps matching inside a word, because that is
    how Arabic inflects it: يكتب and كتبه are كتب.

    `whole` asks further that the word end there, which is the strength inside a tier.
    """
    word = f"({re.escape(term)})"
    if not has_arabic(term):
        found = f"(?<![a-z]){word}"
    elif len(term) < fts.TRIGRAM_MIN:
        found = f"(?<![{ARABIC_LETTER}]){PROCLITIC}{word}{NOT_LETTER}"
    else:
        found = word
    return re.compile(found + (NOT_LETTER if whole else ""))


def uses(term: str, text: str, whole: bool = False) -> Iterator[re.Match]:
    """Each place the term is used as a word in the text. See `pattern`."""
    for found in pattern(term, whole).finditer(text):
        if text[found.start():found.end(1)].lstrip("وف") not in OWN_WORDS:
            yield found


def first_use(term: str, text: str) -> int:
    """Where the term is first used as a word in the text, or -1."""
    found = next(uses(term, text), None)
    return found.start(1) if found else -1
