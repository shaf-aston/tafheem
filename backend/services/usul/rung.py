"""The rungs of a chain, and which of them a book says may be broken. Pure: no I/O.

A rung is two narrators the chain names one after the other in one strand with
the word that passed the hadith from the one below (the student, who says it)
to the one above (the teacher). It is read straight from the hadith's own
Arabic: the narrators are the places rijal.db found names, the word is the
last passing-on or saying word between them (services/hadith/chain.passed_on).
Two names with anything else between them (a name rijal.db did not place, a
ح that starts another strand) are not a rung, and are counted, never guessed.
"""
from __future__ import annotations

from collections import Counter
from typing import NamedTuple

from backend.services.hadith.chain import chain_of, passed_on, term_of


class Rung(NamedTuple):
    student: int        # the narrator who says `word`
    teacher: int
    at: int             # where the teacher's name starts in the hadith's Arabic
    word: str
    below: frozenset[int]   # the narrator who took it from the student in this strand (none at its start)


def in_chain(arabic: str, mentions: list[tuple[int, int, int]]) -> list[tuple[int, int, int]] | None:
    """The mentions (start, end, narrator id) that end inside the hadith's plain chain (chain.chain_of), in text order;
    None when the chain is not plain."""
    chain, _ = chain_of(arabic)
    if not chain:
        return None
    limit = arabic.find(chain) + len(chain)
    return [m for m in mentions if m[1] <= limit]


def rungs(arabic: str, mentions: list[tuple[int, int, int]]) -> tuple[list[Rung], Counter]:
    """(the rungs of the hadith's chain in text order, why each other pair of names was not one).

    `mentions` are (start, end, narrator id) in text order. A hadith whose chain is not plain (chain.chain_of) has none."""
    named = in_chain(arabic, mentions)
    if named is None:
        return [], Counter()
    found: list[Rung] = []
    skipped: Counter = Counter()
    strand = [named[0][2]] if named else []   # the narrators of the strand being read, in text order
    for (_, end, student), (start, _, teacher) in zip(named, named[1:]):
        word, why = passed_on(arabic[end:start])
        if why == "strand":
            strand = [teacher]
            continue
        if why or student == teacher:
            skipped[why or "same"] += 1
        else:
            found.append(Rung(student, teacher, start, word, frozenset(strand[-2:-1])))
        strand.append(teacher)
    return found, skipped


def tadlis(rung: Rung, collection: str, level: int | None, cfg: dict, exempt: list[dict]) -> tuple[str | None, str]:
    """(kind, "") when the rung may hide a gap by tadlis, else (None, why).

    cfg is usul.json's `tadlis`; `level` is the Ta'rif level of the student (None when he has no entry) and `exempt`
    are cfg's `unless` rules with their names turned into narrator ids. kind is tadlis or tadlis_unclear.
    why: not_mudallis, tolerated (a level the Ta'rif tolerates), heard (a word of hearing, or any other word the
    rule does not read), sahih (a book the scholars hold to have hearing established elsewhere) or exempt."""
    if level is None:
        return None, "not_mudallis"
    if not cfg["levels"].get(str(level), {}).get("notes"):
        return None, "tolerated"
    term = term_of(rung.word)
    kind = cfg["ways"].get(term["match"][0]) if term and term["way"] != "heard" else None
    if kind is None:
        return None, "heard"
    if collection in cfg["skip"]["collections"]:
        return None, "sahih"
    for rule in exempt:
        if rung.student in rule["tellers"] and rule["via"] in rung.below and rule["teacher"] in (None, rung.teacher):
            return None, "exempt"
    return kind, ""
