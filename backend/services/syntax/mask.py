"""Links the book rules out, as masks over the parser's scores.

Pure: takes the words' tags and returns which (dependent, head) arcs and which
(dependent, head, relation) labels are impossible, so the decoder picks the best
reading the book allows instead of the best reading full stop. Which vetoes are
on lives in data/nahw_rules/closed_words.json ("vetoes"). Index 0 is the root,
word i is index i, as in the score matrices.
"""
from __future__ import annotations

import numpy as np

from backend.services.nahw_book import vetoes

_NOT_A_NOUN = ("pron", "rel", "interrog", "dem")


def _is_noun(tok: dict) -> bool:
    camel = tok.get("pos_camel", "")
    return tok["pos"] in ("NOM", "PROP") and not any(k in camel for k in _NOT_A_NOUN)


def _verb_subject_follows(toks, add_rel) -> None:
    """A فاعل never comes before its verb: a noun to the left of a verb is a
    mubtada (the parser's topic), so SBJ is ruled out. A noun typed with fatha
    or tanween-fath stays open: it is a fronted object. OBJ and MOD go
    with it, since an untyped noun before its verb is no object either, so
    what is left is the topic (الطعامَ أكل الولدُ)."""
    for d, dep in enumerate(toks, 1):
        if not _is_noun(dep) or dep.get("case") == "a":
            continue
        for h in range(d + 1, len(toks) + 1):
            if toks[h - 1]["pos"].startswith("VRB"):
                for label in ("SBJ", "OBJ", "MOD"):
                    add_rel(d, h, label)


_VETOES = {"verb_subject_follows": _verb_subject_follows}


def book_mask(toks: list[dict], labels: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """(arc_ok[L, L], rel_ok[L, L, R]) for L = words + root; True = allowed."""
    L = len(toks) + 1
    arc_ok = np.ones((L, L), dtype=bool)
    rel_ok = np.ones((L, L, len(labels)), dtype=bool)

    def add_arc(d, h):
        arc_ok[d, h] = False

    def add_rel(d, h, label):
        rel_ok[d, h, labels.index(label)] = False

    on = vetoes()
    for name, rule in _VETOES.items():
        if on.get(name):
            rule(toks, add_rel)
    return arc_ok, rel_ok
