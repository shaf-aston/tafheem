"""How near a misspelling is: three-letter runs to find the candidates, edits to measure them.

A trigram index matches substrings, which is not the same as tolerating a
typo: الرحييم is not a substring of anything. What does tolerate one is
comparing the query's own three-letter runs against the book's, because a
misspelt word still shares most of them with the word meant.
"""
from __future__ import annotations

from backend.services.text import fts

from backend.services.daleel.match.words import PROCLITIC_AT_START, WORDS

# Further than any guess is allowed to be.
FAR = 99


def trigrams(term: str) -> set[str]:
    """Every three-character window. What the index itself is built from."""
    size = fts.TRIGRAM_MIN
    return {term[i:i + size] for i in range(len(term) - size + 1)}


def closeness(terms: tuple, haystack: str) -> int:
    """How many letters this passage is from the misspelt word: the fewest edits
    turning any of its words into it, or FAR when none is near. Smaller is closer.

    Shared runs of letters were the measure before and could not tell a near
    miss from a far one: searching الرحييم, الرحيم and الرحى each share the same
    runs with it once ى is folded to ي, so an idiom about millstones tied with
    al-Fatihah. One edit away and two edits away is the difference a reader sees.
    """
    # Words as letters only, each also without what is joined on in front, so
    # والرحيم and الرحيم، are each one letter from الرحييم, as الرحيم is.
    words = set(WORDS.findall(haystack))
    words |= {PROCLITIC_AT_START.sub("", word) for word in words}
    best = FAR
    for term in terms:
        runs = trigrams(term)
        for candidate in {term, PROCLITIC_AT_START.sub("", term)}:
            for word in words:
                # Only words sharing a run of letters can be near; the rest are never compared.
                if abs(len(word) - len(candidate)) < best and any(run in word for run in runs):
                    best = min(best, edits(candidate, word, best))
    return best


def edits(a: str, b: str, enough: int) -> int:
    """Letters to add, drop or change to turn a into b; stops counting at `enough`."""
    previous = list(range(len(b) + 1))
    for i, letter in enumerate(a, 1):
        current = [i]
        for j, other in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (letter != other)))
        if min(current) >= enough:
            return enough
        previous = current
    return previous[-1]


def allowed_edits(terms: tuple) -> int:
    """How far a guess may be: one letter in three of the word, at least one."""
    return max(1, max((len(term) for term in terms), default=0) // 3)
