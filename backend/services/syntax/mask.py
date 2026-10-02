"""Links the book rules out, as masks over the parser's scores, and the few links it
settles outright, written over the parser's tree.

Pure: takes the words' tags and returns which (dependent, head, relation) labels
are impossible, so the decoder picks the best reading the book allows instead of
the best reading full stop; `book_links` then fixes a structure the book states
whatever the scores say. Which rules are on lives in
data/nahw_rules/closed_words.json ("vetoes"). Index 0 is the root, word i is
index i, as in the score matrices.
"""
from __future__ import annotations

import numpy as np

from backend.services.nahw_book import is_plain_noun, vetoes


def _verb_subject_follows(toks, add_rel) -> None:
    """A فاعل never comes before its verb: a noun to the left of a verb is a
    mubtada (the parser's topic), so SBJ is ruled out. A noun typed with fatha
    or tanween-fath stays open: it is a fronted object. OBJ and MOD go
    with it, since an untyped noun before its verb is no object either, so
    what is left is the topic (الطعامَ أكل الولدُ)."""
    for d, dep in enumerate(toks, 1):
        if not is_plain_noun(dep) or dep.get("case") == "a":
            continue
        for h in range(d + 1, len(toks) + 1):
            if toks[h - 1]["pos"].startswith("VRB"):
                for label in ("SBJ", "OBJ", "MOD"):
                    add_rel(d, h, label)


_VETOES = {"verb_subject_follows": _verb_subject_follows}


def book_mask(toks: list[dict], labels: list[str]) -> np.ndarray:
    """rel_ok[L, L, R] for L = words + root; True = the label is allowed."""
    rel_ok = np.ones((len(toks) + 1, len(toks) + 1, len(labels)), dtype=bool)

    def add_rel(d, h, label):
        rel_ok[d, h, labels.index(label)] = False

    on = vetoes()
    for name, rule in _VETOES.items():
        if on.get(name):
            rule(toks, add_rel)
    return rel_ok


def _pointer_heads_its_noun(toks, heads, rels) -> None:
    """هذا الكتابُ: a pointer and the noun with ال after it are one unit, the pointer its
    head: it takes the job the pair has and the noun (the مشار إليه) hangs on it (Tasheel
    1.4.3 p10). The parser often draws it the other way round."""
    def above(word: int, target: int) -> bool:
        while word:
            if word == target:
                return True
            word = heads[word - 1]
        return False

    for d, dep in enumerate(toks[:-1], 1):
        n = d + 1  # the noun
        noun = toks[n - 1]
        if "dem" not in dep.get("pos_camel", "") or noun.get("stt") != "d" or not is_plain_noun(noun):
            continue
        if heads[n - 1] == d or above(heads[n - 1], d):
            continue  # already under the pointer, or the swap would make a loop
        # the pointer takes the noun's place in the sentence; the noun hangs on it
        heads[d - 1], rels[d - 1] = heads[n - 1], rels[n - 1]
        heads[n - 1], rels[n - 1] = d, "MOD"


_LINKS = {"pointer_heads_its_noun": _pointer_heads_its_noun}


def book_links(toks: list[dict], heads: list[int], rels: list[str]) -> tuple[list[int], list[str]]:
    """The parser's heads and labels with every link the book settles written over them."""
    heads, rels = list(heads), list(rels)
    on = vetoes()
    for name, rule in _LINKS.items():
        if on.get(name):
            rule(toks, heads, rels)
    return heads, rels
