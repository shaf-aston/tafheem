"""The questions (axes) the naming tree splits a word on.

An axis is a small pure test of one token and what hangs round it that answers
with exactly one value from a closed list; the tree (data/nahw_rules/naming_tree.json)
names the axis each branch splits on, walker.py reads the answers.

`is_verb` lives here, not in naming, so facts can be imported by the walker that
naming calls without a loop. Pure: tokens in, names out.
"""
from __future__ import annotations

from typing import Callable

from backend.services.arabic_text import bare_letters, strip_diacritics
from backend.services.syntax.vowels import (
    command_shape, has_tanween, past_passive_shape, typed_passive)

PRESENT_PREFIX = set("أنيت")


def is_verb(token: dict) -> bool:
    if has_tanween(token.get("typed")):
        return False  # a verb never carries tanween, whatever the parser tagged it
    if token["pos"].startswith("VRB"):  # VRB-PASS is a verb too
        return True
    # the word is unknown to the morphology, but the reader typed a passive verb or a
    # hollow command (بِعْ, which CAMeL takes for a name)
    typed = token.get("typed") or ""
    if len(bare_letters(typed)) == 2 and command_shape(typed):
        return token.get("pos_camel") in ("noun", "noun_prop")  # نَمْ is not the noun نَمّ
    return token.get("pos_camel") == "noun_prop" and (
        (strip_diacritics(typed)[:1] in PRESENT_PREFIX and typed_passive(typed, True))
        or past_passive_shape(typed))


def _kind(token: dict, tokens: list[dict]) -> str:
    if token["pos"] == "PRT":
        return "harf"
    return "fil" if is_verb(token) else "ism"


# Each axis is one question the book asks of a word, with a closed list of answers
# and a function that gives exactly one. Siblings in the tree split on one axis
# and each takes one answer, so they cannot overlap.
AXES: dict[str, tuple[tuple[str, ...], Callable[[dict, list[dict]], str]]] = {
    "kind": (("harf", "fil", "ism"), _kind),
}


def of(token: dict, tokens: list[dict]) -> dict[str, str]:
    """The word's answer on every axis."""
    values = {}
    for axis, (allowed, answer) in AXES.items():
        values[axis] = answer(token, tokens)
        if values[axis] not in allowed:
            raise ValueError(f"axis {axis} answered {values[axis]!r}, not one of {allowed}")
    return values
