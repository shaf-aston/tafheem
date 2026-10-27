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

from backend.services.nahw.syntax.facts.word import (WEAK, case_shown, case_unseen, base_tokens, is_suffix, is_prefix, is_emphasis_lam, reading, read_as, is_verb, is_built, is_light, is_passive, typed_case_of, typed_tanween, has_added, shows_nasb_by_kasra, shows_jarr, shown_cases, is_preposition, typed_or_parsed_case, same_case, agrees, unlike, told_of_subject, indefinite_nasb, is_state_word, state_or_specification, is_deputy, is_object_pronoun, is_called_alone, is_called_noun, is_particle, my_ya_dropped, same_root, is_participle, is_elative, is_describing, is_masdar, listed, is_name, is_nasab, noun_tagged, verb_tagged, present_verb_tagged, SUBJECTS, NOUN_LINKS, subject_link, holds_doer, own_doer, attached_pronoun, works_as_verb)
from backend.services.nahw.syntax.facts.sentence import (Sentence, praised_noun, busied, next_word, puts_in_jarr, place_case, told_of_lone_mubtada, verb_above, previous_noun, jarr_takes, excepted_after_la, ma_kind, khabar_behind_ba)
from backend.services.nahw.syntax.facts.kind import (calling_head, joins_clauses, owns_pronoun, asked_verb, negates, _kind)
from backend.services.nahw.syntax.facts.follows import (stands_for, verb_joined_by_waw, _follows)
from backend.services.nahw.syntax.facts.slot import (takes_tamyeez, completes_kaada, is_built_zarf, is_zarf, zarf_of_khabar, place_time, verb_place, busied_before, _slot)
from backend.services.nahw.syntax.facts.governor import (_governor)
from backend.services.nahw.syntax.facts.voice import (_voice)

__all__ = ["WEAK", "case_unseen", "base_tokens", "is_suffix", "is_prefix", "is_emphasis_lam", "next_word", "reading", "read_as", "is_verb", "is_built", "is_light", "is_passive", "typed_case_of", "shows_nasb_by_kasra", "shows_jarr", "shown_cases", "is_preposition", "typed_or_parsed_case", "same_case", "agrees", "unlike", "told_of_subject", "indefinite_nasb", "is_state_word", "state_or_specification", "is_deputy", "is_object_pronoun", "is_called_alone", "is_called_noun", "is_particle", "my_ya_dropped", "same_root", "is_participle", "is_elative", "is_describing", "is_masdar", "listed", "is_name", "is_nasab", "noun_tagged", "verb_tagged", "present_verb_tagged", "SUBJECTS", "NOUN_LINKS", "subject_link", "holds_doer", "own_doer", "attached_pronoun", "works_as_verb", "Sentence", "busied", "puts_in_jarr", "place_case", "told_of_lone_mubtada", "verb_above", "previous_noun", "jarr_takes", "calling_head", "joins_clauses", "owns_pronoun", "asked_verb", "negates", "stands_for", "verb_joined_by_waw", "takes_tamyeez", "completes_kaada", "is_zarf", "zarf_of_khabar", "place_time", "verb_place", "busied_before", "AXES", "of_sentence"]


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
              "purpose", "state", "specification", "none"), _slot),
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
