"""Where in the text as printed each matched word is, so the screen can underline it.

The screen knows nothing about how Arabic is matched; it gets [start, end)
character offsets into the passage it already has, and marks those.
"""
from __future__ import annotations

import re
from functools import lru_cache
from itertools import compress

from backend.services.text.arabic_text import bare_letters

from backend.services.daleel.match.words import uses

Span = tuple[int, int]

_SMALL_ALEF = "ٰ"
_MARK = re.compile("[ؐ-ًؚ-ٟۖ-ۭ]")
_WORD_LETTER = re.compile("[\\wؐ-ًؚ-ٰٟۖ-ۭ]")


def marks(text: str, terms: tuple[str, ...]) -> tuple[Span, ...]:
    """Where in the text as printed each term is used, each widened to its whole word.

    The terms are folded and the text is not, so the text is folded with a
    note of where each folded letter came from. It is folded
    twice, once for each spelling the index holds, so الصلاة is found in the
    ayah's الصلوٰة as well as in a book's الصلاة. The rule for what counts as
    a use is `words.uses`, the same one that ranked the passage.
    """
    if not text or not terms:
        return ()
    found: list[Span] = []
    # The second spelling differs from the first only around a small alef, so
    # a text without one would be folded twice into the same string.
    for written in (False, True) if _SMALL_ALEF in text else (False,):
        folded, origin = _folded_with_origin(text, written)
        for term in terms:
            for use in uses(term, folded):
                start, end = origin[use.start(1)], origin[use.end(1) - 1] + 1
                found.append(_widened(text, start, end))
    return tuple(_merged(found))


def _folded_with_origin(text: str, written: bool) -> tuple[str, list[int]]:
    """The text folded as the index folds it, and for each folded letter the
    place in `text` it came from. `written` spells the small alef out, as the
    second of the index's two spellings does: a waw or ya carrying it becomes
    that alef, as in الصلوٰة.

    Without a step per letter: each different letter is folded once into a
    table, a few dozen for a page, and the text is mapped through it in C. The
    second spelling then changes only the letters at a small alef and the few
    before it. Where each folded letter came from is every place whose letter
    folds to something. The loop this replaced was nine tenths of marking a
    page of results, and a passage of thirty thousand letters took 20ms.
    """
    folded_as = {letter: _fold_letter(letter) for letter in set(text)}
    if any(len(piece) > 1 for piece in folded_as.values()):
        # A letter folding to two, such as a ligature, puts two folded letters
        # at one place, which `compress` cannot say. Rare enough to walk.
        return _folded_letter_by_letter(text, written)
    pieces = list(map(folded_as.__getitem__, text))
    if written:
        alef = text.find(_SMALL_ALEF)
        while alef >= 0:
            pieces[alef] = "ا"
            for at in range(max(alef - 3, 0), alef):
                if text[at] in "وي" and _carries_small_alef(text, at):
                    pieces[at] = ""
            alef = text.find(_SMALL_ALEF, alef + 1)
    return "".join(pieces), list(compress(range(len(text)), pieces))


def _folded_letter_by_letter(text: str, written: bool) -> tuple[str, list[int]]:
    """`_folded_with_origin` a letter at a time, for a text holding a letter
    that folds to more than one."""
    out: list[str] = []
    origin: list[int] = []
    for at, letter in enumerate(text):
        if written and letter == _SMALL_ALEF:
            piece = "ا"
        elif written and letter in "وي" and _carries_small_alef(text, at):
            piece = ""
        else:
            piece = _fold_letter(letter)
        out.append(piece)
        origin.extend([at] * len(piece))
    return "".join(out), origin


@lru_cache(maxsize=4096)
def _fold_letter(letter: str) -> str:
    return bare_letters(letter).lower()


def _carries_small_alef(text: str, at: int) -> bool:
    """Whether the next letter after any vowel marks is the small alef."""
    for letter in text[at + 1:at + 4]:
        if letter == _SMALL_ALEF:
            return True
        if not _MARK.match(letter):
            return False
    return False


def _widened(text: str, start: int, end: int) -> Span:
    """Out to the edges of the word, so بالصبر is marked whole, not just صبر."""
    while start > 0 and _WORD_LETTER.match(text[start - 1]):
        start -= 1
    while end < len(text) and _WORD_LETTER.match(text[end]):
        end += 1
    return start, end


def _merged(spans: list[Span]) -> list[Span]:
    """In order, with overlapping ones made one."""
    out: list[Span] = []
    for start, end in sorted(spans):
        if out and start <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], end))
        else:
            out.append((start, end))
    return out
