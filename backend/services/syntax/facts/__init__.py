"""The questions (axes) the naming tree splits a word on.

An axis is a small pure test of one token and what hangs round it that answers
with exactly one value from a closed list; the tree (data/nahw_rules/naming_tree.json)
names the axis each branch splits on, walker.py reads the answers.

`is_verb` lives here, not in naming, so the walker (which naming calls) can
import the axes without a loop. Pure: tokens in, names out.

The axes live one module each, on two shared layers; nothing imports upwards:

    word      what one word shows on its own (kind, typed case, agreement, lists)
    sentence  the parsed sentence and its lookups (Sentence)
    kind → follows → slot → governor, and voice: one axis each

Callers import from here (facts.is_verb, facts.Sentence); which module a name lives in
is this package's own business.
"""
from __future__ import annotations

from typing import Callable

from backend.services.syntax.facts.word import (WEAK, read_as, is_verb, is_light, is_passive, typed_case_of, shows_nasb_by_kasra, shows_jarr, shown_cases, is_preposition, typed_or_parsed_case, same_case, agrees, unlike, told_of_subject, indefinite_nasb, is_state_word, state_or_specification, is_deputy, is_object_pronoun, is_called_alone, is_called_noun, _skeleton, same_root, is_participle, is_masdar, _listed)
from backend.services.syntax.facts.sentence import (Sentence, puts_in_jarr, place_case, told_of_lone_mubtada, verb_above, previous_noun, jarr_takes)
from backend.services.syntax.facts.kind import (calling_head, _joins_clauses, asked_verb, negates, _kind)
from backend.services.syntax.facts.follows import (stands_for, with_waw, _follows)
from backend.services.syntax.facts.slot import (takes_tamyeez, completes_kaada, is_zarf, zarf_of_khabar, _place_time, _object_of_participle, _verb_place, _nominal_place, _slot)
from backend.services.syntax.facts.governor import (_governor, _governing)
from backend.services.syntax.facts.voice import (_voice)

__all__ = ["WEAK", "read_as", "is_verb", "is_light", "is_passive", "typed_case_of", "shows_nasb_by_kasra", "shows_jarr", "shown_cases", "is_preposition", "typed_or_parsed_case", "same_case", "agrees", "unlike", "told_of_subject", "indefinite_nasb", "is_state_word", "state_or_specification", "is_deputy", "is_object_pronoun", "is_called_alone", "is_called_noun", "_skeleton", "same_root", "is_participle", "is_masdar", "_listed", "Sentence", "puts_in_jarr", "place_case", "told_of_lone_mubtada", "verb_above", "previous_noun", "jarr_takes", "calling_head", "_joins_clauses", "asked_verb", "negates", "_kind", "stands_for", "with_waw", "_follows", "takes_tamyeez", "completes_kaada", "is_zarf", "zarf_of_khabar", "_place_time", "_object_of_participle", "_verb_place", "_nominal_place", "_slot", "_governor", "_governing", "_voice", "AXES", "of_sentence"]


# Each axis is one question the book asks of a word, with a closed list of answers
# and a function that gives exactly one. Axes never call one another: what they share
# is the plain helpers above. Siblings in the tree split on one axis and each takes
# one answer, so they cannot overlap.
AXES: dict[str, tuple[tuple[str, ...], Callable[[dict, Sentence], str]]] = {
    "kind": (("harf", "fil", "ism"), _kind),
    "follows": (("naat", "atf", "tawkeed", "badal", "none"), _follows),
    "governor": (("harf_jarr", "idafa", "verb", "noun", "inna", "kana", "kaada", "zanna", "nida", "istithna",
                  "none"), _governor),
    "slot": (("subject", "predicate", "object", "second_object", "absolute", "place_time", "accompaniment",
              "state", "specification", "none"), _slot),
    "voice": (("active", "passive", "none"), _voice),
}


def of_sentence(tokens: list[dict]) -> tuple[list[dict[str, str]], dict[int, int]]:
    """Every token's answer on every axis, in token order, with the sentence's lookups built
    once; and which word governs each governed token, by id."""
    s = Sentence(tokens)
    answers = []
    for token in tokens:
        values = {}
        for axis, (allowed, answer) in AXES.items():
            values[axis] = answer(token, s)
            if values[axis] not in allowed:
                raise ValueError(f"axis {axis} answered {values[axis]!r}, not one of {allowed}")
        answers.append(values)
    return answers, s.governed_by
