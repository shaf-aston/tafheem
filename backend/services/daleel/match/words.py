"""What counts as a passage using a term: the one rule ranking and marking share."""
from __future__ import annotations

import re
from functools import lru_cache
from itertools import product
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
# The same, written out: every way it can be spelled, and the empty one. A
# short list, so each can be looked back for at a fixed width.
PROCLITICS = tuple(sorted(
    {"".join(letters) for size in range(5) for letters in product("وفلبكا", repeat=size)
     if re.fullmatch(PROCLITIC, "".join(letters))},
    key=len,
))
WORDS = re.compile(f"[a-z{ARABIC_LETTER}]+")
_ARABIC_LETTER = re.compile(f"[{ARABIC_LETTER}]")

# A short word with a letter joined on that is a word of its own: لما is
# "when", not ل and ما, and was being passed off as a clean find for ما.
OWN_WORDS = frozenset({"لما"})


@lru_cache(maxsize=1024)
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
        # The word first and the edge test after it, looking back across the
        # word: the same rule, but a pattern opening with letters is found by
        # a fast scan, while one opening with a look-behind is tried at every
        # character. Ranking runs this a dozen times over each of 240 passages,
        # some of them pages of English, and it was 81ms of a search for god.
        found = f"{word}(?<![a-z]{re.escape(term)})"
    elif len(term) < fts.TRIGRAM_MIN:
        # The same order for the same reason: the word, then a look back for
        # what may be joined on in front of it and for the edge before that.
        # Opening with the edge, رب for "god" was 60ms of ranking on the server.
        found = f"{word}(?:{_joined_on_in_front(term)}){NOT_LETTER}"
    else:
        found = word
    return re.compile(found + (NOT_LETTER if whole else ""))


def _joined_on_in_front(term: str) -> str:
    """Behind the term, one of the `PROCLITICS` and before it no Arabic letter."""
    return "|".join(
        f"(?<={re.escape(joined + term)})(?<![{ARABIC_LETTER}]{re.escape(joined + term)})"
        for joined in PROCLITICS
    )


def uses(term: str, text: str, whole: bool = False) -> Iterator[re.Match]:
    """Each place the term is used as a word in the text, as group 1. See `pattern`."""
    short = has_arabic(term) and len(term) < fts.TRIGRAM_MIN
    for found in pattern(term, whole).finditer(text):
        if _as_written(text, found, short).lstrip("وف") not in OWN_WORDS:
            yield found


def _as_written(text: str, found: re.Match, short: bool) -> str:
    """The word found, and for a short one what is joined on in front of it."""
    start = found.start(1)
    if short:
        while start > 0 and _ARABIC_LETTER.match(text[start - 1]):
            start -= 1
    return text[start:found.end(1)]


def first_use(term: str, text: str) -> int:
    """Where the term is first used as a word in the text, or -1."""
    found = next(uses(term, text), None)
    return found.start(1) if found else -1
