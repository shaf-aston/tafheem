"""Which candidate is the better answer. Pure, so it can be argued with in a test.

Every candidate gets a rank of four numbers, all smaller-is-better: its `Tier`,
a strength within that tier, where the first hit falls, and how long the
passage is. `close_enough` then drops poor guesses at a misspelling, and
`spread` picks the page so every book with an answer gets a place on it.
"""
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from backend.services.daleel.match.typos import allowed_edits, closeness
from backend.services.daleel.match.words import first_use, uses

if TYPE_CHECKING:
    from backend.services.daleel.index.row import IndexedPassage
    from backend.services.daleel.query.expand import Expansion

Rank = tuple[int, int, int, int]
Ranked = list[tuple[Rank, "IndexedPassage"]]


class Tier(IntEnum):
    """How a passage matched, best first. Its `label` is carried to the screen,
    so a loose match is labelled as one instead of passing for a clean find."""

    EXACT = 0
    """Every typed word, or the typed words as a phrase."""
    PARTIAL = 1
    """Some of the typed words."""
    RELATED = 2
    """A word the typed ones were expanded to: a synonym or translation."""
    ROOT = 3
    """None of the words, but their root."""
    LOOSE = 4
    """None of that: a guess at a misspelling."""

    @property
    def label(self) -> str:
        return self.name.lower()


# Stronger than any count of whole words, so the phrase always leads its tier.
PHRASE = 1000


def rank_of(row: IndexedPassage, expansion: Expansion) -> Rank:
    """How good a match this row is.

    Position matters because a passage whose opening words answer the
    question reads as the better quotation; length breaks the remaining ties
    towards the tighter passage rather than the rambling one.

    The three weaker tiers each need their own strength, because the one that
    suits a word match means nothing to them. A root match has no position to
    speak of, so it counts how many of the query's roots the passage carries; a
    loose match counts how far the passage is from the misspelt word.
    """
    _, _, _, _, english, roots, fold = row

    # Both halves of the passage count as places a term can be found. Some
    # books here are English only, Ibn Kathir among them, and a rule that read
    # the Arabic alone would rank every one of their passages as a bad match.
    fold = f"{fold} {english.lower()}"

    present = [term for term in expansion.typed if first_use(term, fold) >= 0]
    also = [term for term in expansion.related if first_use(term, fold) >= 0]

    if expansion.phrase and first_use(expansion.phrase, fold) >= 0:
        # The words as typed, in order, beat the same words anywhere.
        return (Tier.EXACT, -PHRASE, first_use(expansion.phrase, fold), len(fold))
    if expansion.typed and len(present) == len(expansion.typed):
        tier = Tier.EXACT
    elif present:
        tier = Tier.PARTIAL
    elif also:
        tier = Tier.RELATED
    elif shared_roots := sum(has_root(roots, root) for root in expansion.roots):
        return (Tier.ROOT, -shared_roots, 0, len(fold))
    else:
        return (Tier.LOOSE, closeness(expansion.loose, fold), 0, len(fold))

    # A passage using the word beats one that merely contains its letters.
    # Without this the shortest passage won every tie, and the shortest thing
    # in the index is a dictionary headword: searching كتب returned كتبي and
    # كتبة ahead of the ayahs that actually say كُتِبَ.
    #
    # The test is that the word *ends* where a word ends, and deliberately says
    # nothing about what comes before it. Arabic writes its prefixes joined on,
    # so بِالصَّبْرِ is the ordinary way an ayah says الصبر; demanding a space on
    # both sides called that a poor match and put a dictionary entry above the
    # verse. A suffix is different: كتبي is a different word from كتب.
    matched = present or also
    whole = sum(next(uses(term, fold, whole=True), None) is not None for term in matched)

    first = min((first_use(term, fold) for term in matched), default=len(fold))
    return (tier, -whole, first, len(fold))


def has_root(roots: str, root: str) -> bool:
    """Whether the passage carries that exact root.

    Compared word by word rather than as a substring: the roots column is a
    space-joined list, and a plain `in` would let كتب match a longer root that
    merely contains those letters.
    """
    return root in roots.split()


def close_enough(ranked: Ranked, expansion: Expansion) -> Ranked:
    """The guesses at a misspelling that are as near as the nearest one.

    Every book is promised a place by `spread`, so without this each one sent
    its best guess however poor: searching الرحييم gave al-Fatihah and ten
    passages that shared a run of letters with it, a millstone idiom and a
    grammar's opening page among them. A guess is kept when it is no more
    letters away than the closest guess, and never more than a third of the word.
    """
    loose = [rank[1] for rank, _ in ranked if rank[0] == Tier.LOOSE]
    if not loose:
        return ranked
    most = min(min(loose), allowed_edits(expansion.loose))
    return [item for item in ranked if item[0][0] != Tier.LOOSE or item[0][1] <= most]


def spread(ranked: Ranked, limit: int) -> Ranked:
    """The best matches, with every book that has one getting a place.

    Sorted purely on how good a match each passage is, so no book is favoured;
    but a book that matched is then guaranteed one slot before the rest of the
    list is filled. Without that guarantee the Qur'an wins every slot on almost
    any query, simply because it has by far the most passages, and a reader
    would never learn that the dictionary or Ibn Faris had an answer too.
    """
    best_of: dict[str, tuple] = {}
    for item in ranked:
        best_of.setdefault(item[1].source, item)

    chosen = list(best_of.values())[:limit]
    taken = {item[1].key for item in chosen}

    for item in ranked:
        if len(chosen) >= limit:
            break
        if item[1].key not in taken:
            chosen.append(item)
            taken.add(item[1].key)

    return sorted(chosen, key=lambda i: i[0])
