"""Versions of one hadith number compared: the narrators at each place of the chains, and the words one telling alone has.

Pure: no I/O. Knobs are usul.json `routes`; the build (scripts/build_usul.py) writes the results to usul.db and
store.py reads them back.

Routes: chains are lined up from the Companion end, because they differ in length at the compiler end. A place
is a position in the chain, which is not always a generation (two Companions in one chain, a Successor from a
Successor). The places counted are those every telling reaches; the shortest chain's last place is its compiler's
teacher, and the compiler himself is not a place. The term is set by the place with the fewest distinct narrators
(Nuzhat al-Nazar), never tawatur, which needs conditions we cannot check.

Words: each telling's matn (chain.chain_of) folded to its letters. A word found in exactly one telling is marked
there. A word that differs from another telling's only by a clitic or the app's spelling folds is no difference;
one that matches only once the dots are gone is marked as a dot difference. Never labelled better or worse.
"""
from __future__ import annotations

import re
from typing import NamedTuple

from backend.services.hadith.chain import chain_of, passed_on, without_asides
from backend.services.spelling import fold

_LETTERS = re.compile("[^ء-ي]")
# The hadith.json chain rule hides a ح (a new strand) among its marks; passed_on names it.
_BREAKS = {"strand", "unnamed"}


class Mark(NamedTuple):
    at: int        # index of the word in the matn split on whitespace
    word: str      # the word as written
    kind: str      # "only" or "dots"
    other: str     # for "dots": the word of another telling it matches without dots


def word_key(word: str, cfg: dict) -> str:
    """The word's letters, folded as the app folds, with a joined و, ف or ب gone while a stem is left. "" for no word."""
    key = _LETTERS.sub("", fold(word))
    for _ in range(cfg["clitic_max"]):
        if key[:1] in cfg["clitics"] and len(key) - 1 >= cfg["clitics"][key[:1]]:
            key = key[1:]
    return key


def rasm(word: str, groups: list[str]) -> str:
    """The word with letters that differ only by their dots written as one (ب ت ث ن ي, ج ح خ ...)."""
    out = word
    for group in groups:
        for letter in group[1:]:
            out = out.replace(letter, group[0])
    return out


def chain_ids(arabic: str, mentions: list[tuple[int, int, int]], generation: dict[int, str],
              companions: set[str]) -> tuple[list[int], str]:
    """(narrator ids of the chain in text order, "") or ([], why the places cannot be trusted).

    `mentions` are (start, end, narrator id) in text order, one per start. why: no_chain (the Arabic has no plain
    chain, or rijal placed no name in it), strand (a ح starts another strand), unplaced_name (words between two names
    that no name of rijal's explains), companion_end_unplaced / companion_end_other (the last name is not a Companion
    for rijal, or is not placed in a generation at all), two_companions (the last two names are both Companions)."""
    chain, _ = chain_of(arabic)
    if not chain:
        return [], "no_chain"
    limit = arabic.find(chain) + len(chain)
    named = [m for m in mentions if m[1] <= limit]
    if not named:
        return [], "no_chain"
    for (_, end, _), (start, _, _) in zip(named, named[1:]):
        _, why = passed_on(without_asides(arabic[end:start]))
        if why in _BREAKS:
            return [], why if why == "strand" else "unplaced_name"
    ids = [who for *_, who in named]
    last = generation.get(ids[-1], "")
    if last not in companions:
        return [], "companion_end_other" if last else "companion_end_unplaced"
    if len(ids) > 1 and generation.get(ids[-2], "") in companions:
        return [], "two_companions"
    return ids, ""


def layers(chains: list[list[int]]) -> list[set[int]]:
    """The distinct narrators at each place counted from the Companion end (chains are in text order, Companion last),
    for the places every chain reaches. A chain given twice counts once, as a narrator at a place counts once."""
    if not chains:
        return []
    reach = min(len(c) for c in chains)
    return [{c[-1 - i] for c in chains} for i in range(reach)]


def term_of(thinnest: int, terms: list[dict]) -> dict:
    """The term whose min is the highest the count reaches."""
    return max((t for t in terms if t["min"] <= thinnest), key=lambda t: t["min"])


def marks(matns: dict[str, list[str]], cfg: dict) -> tuple[dict[str, list[Mark]], dict[str, str]]:
    """({part: its marked words}, {part: why it was not compared}) for the tellings' matn words.

    A telling of fewer than `min_words` words (marks and numbers are no words) is not compared (short_matn); with fewer than two compared there is nothing to
    set against and nothing is marked. A word counts once however often a telling says it."""
    keys = {p: [word_key(w, cfg) for w in words] for p, words in matns.items()}
    kept = {p: matns[p] for p, row in keys.items() if sum(map(bool, row)) >= cfg["min_words"]}
    left = {p: "short_matn" for p in matns if p not in kept}
    if len(kept) < 2:
        return {}, left
    holders: dict[str, set[str]] = {}
    rasms: dict[str, dict[str, str]] = {}   # rasm of a key -> {part: a written word with it}
    for p in kept:
        for key, word in zip(keys[p], kept[p]):
            if key:
                holders.setdefault(key, set()).add(p)
                rasms.setdefault(rasm(key, cfg["rasm"]), {}).setdefault(p, word)
    found: dict[str, list[Mark]] = {p: [] for p in kept}
    for p in kept:
        for at, (key, word) in enumerate(zip(keys[p], kept[p])):
            if not key or len(holders[key]) != 1:
                continue
            twin = next((w for q, w in rasms[rasm(key, cfg["rasm"])].items() if q != p), "") if len(key) >= cfg["dot_min"] else ""
            found[p].append(Mark(at, word, "dots" if twin else "only", twin))
    return {p: m for p, m in found.items() if m}, left
