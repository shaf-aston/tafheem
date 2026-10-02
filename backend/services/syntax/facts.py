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
from backend.services.nahw_book import is_one
from backend.services.syntax.vowels import (
    CAMEL_CASE, command_shape, has_tanween, past_passive_shape, typed_case, typed_passive)

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


def case_of(token: dict) -> str | None:
    """What the reader typed first, the parser's guess second."""
    return (typed_case(token.get("typed"), token.get("stuck_on", 0))
            or CAMEL_CASE.get(token.get("cas")))


def children_of(token: dict, tokens: list[dict]) -> list[dict]:
    return [t for t in tokens if t["head"] == token["id"]]


def noun_before(particle: dict, by_id: dict) -> bool:
    """The particle follows a noun it can join to, which an oath و does not."""
    before = by_id.get(particle["head"])
    return bool(before and before["id"] < particle["id"] and before["pos"] in ("NOM", "PROP")
                and not is_verb(before))


def _follows(token: dict, tokens: list[dict]) -> str:
    """Which follower (tabi') the word is, or none: a follower takes its case from the
    word it follows, every other noun from a governor (Tasheel 3.10 p88).

    A word is a follower only on the evidence of both its link and what it hangs on;
    an indefinite word after a definite or construct noun is a khabar or hal, so it
    answers none and the rest of the naming decides it."""
    by_id = {t["id"]: t for t in tokens}
    head = by_id.get(token["head"])
    # the noun pointed at by a demonstrative child: هذا البستانُ
    pointer = next((c for c in children_of(token, tokens) if "dem" in c.get("pos_camel", "")), None)
    if pointer and case_of(pointer) in (None, case_of(token)) and token.get("stt") == "d":
        return "naat"
    if not head:
        return "none"
    # لكن is also an inna sister; it joins only when no clause of its own follows
    if head["pos"] == "PRT" and is_one(head["lemma"], "atf") and not is_one(head["lemma"], "inna")             and noun_before(head, by_id):
        return "atf"
    # الخليفة عمر: a bare name right after a noun with ال is that noun's badal
    if token["pos"] == "PROP" and token["rel"] == "MOD" and head["id"] == token["id"] - 1             and head["pos"] == "NOM" and head["form"].startswith("ال") and not is_verb(head)             and not has_tanween(token.get("typed")):
        return "badal"
    with_pronoun = any(k.get("pos_camel") == "pron" for k in children_of(token, tokens))
    if is_one(token["lemma"], "tawkeed", "with_pronoun" if with_pronoun else "without_pronoun")             and head["id"] < token["id"] and not is_verb(head) and head["pos"] != "PRT":
        return "tawkeed"
    if token["rel"] != "MOD" or is_verb(head):
        return "none"
    mine, theirs = case_of(token), case_of(head)
    if mine and mine == theirs:
        # a na't matches its noun in "the" as well as case, and a word in idafa
        # counts as definite, so an indefinite word after either is the khabar
        return "none" if token.get("stt") == "i" and head.get("stt") in ("d", "c") else "naat"
    # لا رجلَ حاضرٌ (khabar) and a hal or tamyeez in nasb are not followers
    if mine and theirs and head["rel"] in ("SBJ", "TPC") and mine != "a":
        return "none"
    if mine == "a" and token.get("stt") != "d":
        return "none"
    return "naat" if token.get("ud") == "ADJ" else "none"


# Each axis is one question the book asks of a word, with a closed list of answers
# and a function that gives exactly one. Siblings in the tree split on one axis
# and each takes one answer, so they cannot overlap.
AXES: dict[str, tuple[tuple[str, ...], Callable[[dict, list[dict]], str]]] = {
    "kind": (("harf", "fil", "ism"), _kind),
    "follows": (("naat", "atf", "tawkeed", "badal", "none"), _follows),
}


def of(token: dict, tokens: list[dict]) -> dict[str, str]:
    """The word's answer on every axis."""
    values = {}
    for axis, (allowed, answer) in AXES.items():
        values[axis] = answer(token, tokens)
        if values[axis] not in allowed:
            raise ValueError(f"axis {axis} answered {values[axis]!r}, not one of {allowed}")
    return values
