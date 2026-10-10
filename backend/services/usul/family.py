"""Versions of one hadith number compared: the narrators at each place of the chains, and the words one telling alone has.

Pure: no I/O. Knobs are usul.json `family`; the build (scripts/build_usul.py) writes the results to usul.db and
store.py reads them back.

Places: chains are lined up from the Companion end, because they differ in length at the compiler end. A place
is a position in the chain, which is not always a generation (two Companions in one chain, a Successor from a
Successor). The places counted are those every telling reaches. The count is the narrators one book gives under
one number, never a name for the hadith (mashhur, 'aziz and gharib are about every route it has). The compiler's own
teachers named together (حدثنا A وB) stand before the chain and are left out; two names at one place further up are
no single line (the split is never guessed), so the family has no places.

Words: each telling's matn (chain.chain_of, split on whitespace here and nowhere else) folded to its letters. Tellings are set against each other only where
they share enough of their text to be one report; a word found in exactly one of them is marked there. A word that
differs from another telling's only by a clitic or the app's spelling folds is no difference; one that matches only
once the dots are gone is marked as a dot difference. Never labelled better or worse.
"""
from __future__ import annotations

import itertools
import math
import re
from collections import Counter
from typing import NamedTuple

from backend.services.usul.rung import in_chain, walk
from backend.services.spelling import fold

_LETTERS = re.compile("[^ء-ي]")
# The hadith.json chain rule hides a ح (a new strand) among its marks; passed_on names it.
_BREAKS = {"strand": "strand", "unnamed": "unplaced_name", "no_link": "names_joined"}


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
              companions: set[str], joiner: str) -> tuple[list[int], str]:
    """(narrator ids of the chain in text order, "") or ([], why the places cannot be trusted).

    `mentions` are (start, end, narrator id) in text order, one per start; `joiner` is the letter that joins two names
    (usul.json `family.joiner`). why: no_chain (the Arabic has no plain chain, or rijal placed no name in it past the
    compiler's own teachers), strand (a ح starts another strand), unplaced_name (words between two names
    that no name of rijal's explains), name_after_cut (rijal places a name after the chain's cut: a second chain or
    the chain's end sits in what the app shows as the text), names_joined (no passing-on or saying word between two
    names past the compiler's own teachers: two men at one place, whose next link may differ, as in "عن العلاء وسهيل
    عن أبيهما"), companion_end_unplaced / companion_end_other (the last
    name is not a Companion for rijal, or is not placed in a generation at all), two_companions (the last two names
    are both Companions)."""
    named = in_chain(arabic, mentions)
    if not named:
        return [], "no_chain"
    if len(named) < len(mentions):
        return [], "name_after_cut"
    teachers = 0   # how many names open the chain joined together: the compiler's own teachers (حدثنا A وB)
    for at, pair in enumerate(walk(arabic, named)):
        # joined: the joiner stands alone in the gap or opens the next name (rijal's span often takes it in)
        joined = arabic.startswith(joiner, pair.at) or joiner in (_LETTERS.sub("", w) for w in pair.gap.split())
        if pair.why == "no_link" and joined and at == max(teachers - 1, 0):
            teachers = at + 2
        elif pair.why:
            return [], _BREAKS[pair.why]
    ids = [who for *_, who in named[teachers:]]   # they stand before the chain, so their place is not counted
    if not ids:
        return [], "no_chain"
    last = generation.get(ids[-1], "")
    if last not in companions:
        return [], "companion_end_other" if last else "companion_end_unplaced"
    if len(ids) > 1 and generation.get(ids[-2], "") in companions:
        return [], "two_companions"
    return ids, ""


def places(chains: list[list[int]]) -> list[set[int]]:
    """The distinct narrators at each place counted from the Companion end (chains are in text order, Companion last),
    for the places every chain reaches. A chain given twice counts once, as a narrator at a place counts once."""
    if not chains:
        return []
    reach = min(len(c) for c in chains)
    return [{c[-1 - i] for c in chains} for i in range(reach)]


def weights(tellings: list[set[str]]) -> dict[str, float]:
    """ln(tellings / tellings holding the word) for every word key: a word most tellings hold weighs little."""
    held = Counter(key for keys in tellings for key in keys)
    return {key: math.log(len(tellings) / n) for key, n in held.items()}


def shares(keys: dict[str, set[str]], weight: dict[str, float]) -> dict[tuple[str, str], float]:
    """{(p, q): the weight of the words the shorter telling shares with the other, over its own weight} per pair.

    The shorter is the one with less weight, so a telling that is only part of another still scores high; a
    telling none of whose weight is held scores 0."""
    mass = {p: sum(weight[k] for k in ks) for p, ks in keys.items()}
    out = {}
    for p, q in itertools.combinations(sorted(keys), 2):
        low = min(mass[p], mass[q])
        out[p, q] = sum(weight[k] for k in keys[p] & keys[q]) / low if low else 0.0
    return out


def one_report(keys: dict[str, set[str]], weight: dict[str, float], cfg: dict) -> list[list[str]]:
    """The tellings grouped so that each is set against the ones it shares `same_text_min` of its text with (a pair
    that reaches it joins both; a group is every telling linked to one another through such pairs)."""
    group = {p: {p} for p in keys}
    for (p, q), share in shares(keys, weight).items():
        if share >= cfg["same_text_min"] and group[p] is not group[q]:
            group[p] |= group[q]
            for r in group[q]:
                group[r] = group[p]
    return [sorted(g) for g in {id(g): g for g in group.values()}.values()]


def marks(matns: dict[str, list[str]], cfg: dict, weight: dict[str, float]) -> tuple[dict[str, list[Mark]], dict[str, str]]:
    """({part: its marked words}, {part: why it was not compared}) for the tellings' matn words.

    A telling of fewer than `min_words` words (marks and numbers are no words) is not compared (short_matn); one left
    on its own has nothing to set against (alone). Of the rest, one that shares enough of its text with no
    other is not compared either (different_text); the others are compared within their group. A word counts once
    however often a telling says it."""
    keys = {p: [word_key(w, cfg) for w in words] for p, words in matns.items()}
    kept = {p: matns[p] for p, row in keys.items() if sum(map(bool, row)) >= cfg["min_words"]}
    left = {p: "short_matn" for p in matns if p not in kept}
    if len(kept) < 2:
        return {}, {**left, **{p: "alone" for p in kept}}
    sets = {p: {k for k in keys[p] if k} for p in kept}
    found: dict[str, list[Mark]] = {}
    for group in one_report(sets, weight, cfg):
        if len(group) < 2:
            left[group[0]] = "different_text"
            continue
        holders: dict[str, set[str]] = {}
        rasms: dict[str, dict[str, str]] = {}   # rasm of a key -> {key: a written word with it}
        for p in group:
            for key, word in zip(keys[p], kept[p]):
                if key:
                    holders.setdefault(key, set()).add(p)
                    rasms.setdefault(rasm(key, cfg["rasm"]), {}).setdefault(key, word)
        for p in group:
            for at, (key, word) in enumerate(zip(keys[p], kept[p])):
                if not key or len(holders[key]) != 1:
                    continue
                # a twin is another telling's word p itself lacks; one p also says leaves this word p's own
                twin = next((w for k, w in rasms[rasm(key, cfg["rasm"])].items() if p not in holders[k]),
                            "") if len(key) >= cfg["dot_min"] else ""
                found.setdefault(p, []).append(Mark(at, word, "dots" if twin else "only", twin))
    return found, left
