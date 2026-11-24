"""Whether a passage answers the question, or only shares a word with it. Pure.

The search always finds something: the trigram index matches inside words, and
the dictionaries hold nearly every English word. Ranking decides what comes
first; this decides whether anything counts as an answer at all, so a question
the books do not cover is told so instead of handed weak matches.
"""
from __future__ import annotations

import re

from backend.services.daleel.index.row import IndexedPassage
from backend.services.daleel.query.expand import Expansion

# The sources.json shelf whose entries define words rather than answer questions.
DICTIONARY = "Dictionary"


def share_of(row: IndexedPassage, expansion: Expansion, related_weight: float) -> float:
    """How much of the question this passage covers, 0 for none.

    Each typed word found counts 1; a related word (a synonym, a translation)
    stands in for a missing one at `related_weight`. An English word must start
    where a word starts: "mining" is not in "undermining". Arabic words may sit
    anywhere, its prefixes being written joined on (بالصبر). A question of
    several words needs at least one of them in the passage itself, or one
    word's loose translations pile up into a pass ("quantum physics").
    """
    english, _, fold = row[4:7]
    text = f"{fold} {english.lower()}"

    def found(term: str) -> bool:
        if term.isascii():
            return re.search(rf"(?<![a-z']){re.escape(term)}", text) is not None
        return term in text

    typed = expansion.typed
    if not typed:
        return 0.0
    direct = sum(found(term) for term in typed)
    if direct == 0 and len(typed) > 1:
        return 0.0
    stand_ins = min(sum(found(term) for term in expansion.related), len(typed) - direct)
    return (direct + related_weight * stand_ins) / len(typed)


def answered(shares: list[float], shelves: list[str], words: int, least: float) -> list[bool]:
    """Which passages answer, given each one's share and shelf.

    A dictionary defines one word, so it holds "stock" and "market" for any
    question: a question of several words is answered only if a book backs it.
    """
    passes = [share >= least for share in shares]
    if words > 1 and not any(ok and shelf != DICTIONARY for ok, shelf in zip(passes, shelves)):
        return [False] * len(passes)
    return passes
