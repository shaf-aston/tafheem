"""Where in the whole Qur'an a reading sits. Pure: words in, a place out.

The Qur'an is one long line of words, and a reading is found on it the way
a satnav keeps one position on the whole map: every heard word that is on the
line votes for where the reading would start if that word is where it is.
Rare words count for more, since a word like ٱللَّهِ is on nearly every page.
The best few starts are then compared letter by letter, so a misheard word
costs a little rather than everything, and a reading that runs on from one
ayah into the next is found like any other.

Sure means no other place fits nearly as well: the first words of 2:255 are
also all of 3:2, and until the reciter says more the two tie. Measured on
1,050 Groq readings cut into 4-word pieces: 1,247 placed right, 0 wrong, the
rest not sure (see recitation_place_margin).
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher

from backend.services.recitation.place import PLACES_IT, letters

# Starts compared letter by letter; the rest are left out by their votes alone.
_KEEP = 8
# Words a reading may gain or drop against the text, either side of a start.
_SLACK = 2


@dataclass(frozen=True)
class Line:
    """The whole Qur'an as one line of words, built once."""

    words: tuple[str, ...]           # folded words, in order
    where: tuple[tuple[int, int], ...]  # (surah, ayah) of each word
    index: dict[str, list[int]]      # word -> where it stands on the line
    weight: dict[str, float]         # word -> how much it tells, rarer more


@dataclass(frozen=True)
class Place:
    surah: int
    ayah: int    # where the reading starts
    sure: bool   # no other place fits nearly as well
    home: bool   # inside `near`, the page the reciter has open


def build(ayahs) -> Line:
    """`ayahs` is ((surah, ayah), text) in Qur'an order."""
    words, where = [], []
    for key, text in ayahs:
        for word in text.split():
            if folded := letters(word):
                words.append(folded)
                where.append(key)
    index = defaultdict(list)
    for at, word in enumerate(words):
        index[word].append(at)
    weight = {word: math.log(len(words) / len(at)) for word, at in index.items()}
    return Line(tuple(words), tuple(where), dict(index), weight)


def _spots(heard: list[str], line: Line) -> list[tuple[float, int]]:
    """(score, start) of the places that hold at least PLACES_IT heard words, best first."""
    votes = defaultdict(float)
    for i, word in enumerate(heard):
        for at in line.index.get(word, ()):
            votes[at - i] += line.weight[word]
    near = lambda start: sum(votes.get(start + k, 0) for k in range(-_SLACK, _SLACK + 1))
    starts = []
    for start in sorted(votes, key=near, reverse=True):
        if all(abs(start - other) > len(heard) for other in starts):
            starts.append(start)
        if len(starts) == _KEEP:
            break
    said = " ".join(heard)
    out = []
    for start in starts:
        lo, hi = max(start - _SLACK, 0), min(start + len(heard) + _SLACK, len(line.words))
        span = line.words[lo:hi]
        hits = [b for b in SequenceMatcher(None, heard, list(span), autojunk=False).get_matching_blocks() if b.size]
        if sum(b.size for b in hits) < PLACES_IT:
            continue
        shared = sum(b.size for b in SequenceMatcher(None, said, " ".join(span), autojunk=False).get_matching_blocks())
        out.append((shared / len(said), lo + hits[0].b))
    return sorted(out, reverse=True)


def find(heard: str, line: Line, margin: float, near: tuple[int, int] | None = None) -> Place | None:
    """Where `heard` starts, or None when no place holds PLACES_IT of its words.

    `near` is (first, last + 1) on the line: the open page. A place there that
    fits within `margin` of the best is taken, since carrying on is likelier
    than a jump that the words cannot tell apart.
    """
    found = _spots([w for w in map(letters, heard.split()) if w], line)
    if not found:
        return None
    best = found[0]
    home = [spot for spot in found if near and near[0] - _SLACK <= spot[1] < near[1]]
    if home and home[0][0] >= best[0] - margin:
        return Place(*line.where[home[0][1]], sure=True, home=True)
    rival = found[1][0] if len(found) > 1 else 0.0
    return Place(*line.where[best[1]], sure=best[0] - rival >= margin, home=False)


def span(line: Line, first: tuple[int, int], last: tuple[int, int]) -> tuple[int, int]:
    """(first, last + 1) on the line for the ayahs first..last, and the ayah after.

    The ayah after the page is home too: reciting on past the page's end is
    the page turning, not the reciter being elsewhere.
    """
    start = line.where.index(first)
    end = len(line.where) - line.where[::-1].index(last)
    after = line.where[end] if end < len(line.where) else None
    while end < len(line.where) and line.where[end] == after:
        end += 1
    return start, end
