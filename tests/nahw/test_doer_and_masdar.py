"""A verb never leaves its doer out (باب الفاعل: الفاعل لا يحذف); a word of its verb's own root off a doer's
measure is the doing again, its مفعول مطلق; a hidden doer goes back to one said earlier."""
from __future__ import annotations

import pytest

from tests.nahw_helpers import analyze, needs_parser


def _roles(sentence: str) -> list[str | None]:
    return [w.get("role") for w in analyze(sentence)["words"]]


@needs_parser
@pytest.mark.parametrize("sentence, at, role", [
    ("مَا كَتَبَ الدَّرْسَ إِلَّا فَتًى", 4, "فاعل"),
    ("مَا زَارَ الْمَرِيضَ إِلَّا مُصْطَفَى", 4, "فاعل"),
])
def test_a_noun_showing_no_case_after_the_object_is_the_doer(sentence, at, role):
    assert _roles(sentence)[at] == role


@needs_parser
def test_a_word_of_the_verbs_root_off_a_doers_measure_is_its_masdar():
    assert _roles("ضَحِكَ الطِّفْلُ ضَحِكًا طَوِيلًا")[2] == "مفعول مطلق"
    assert _roles("قَامَ الرَّجُلُ قَائِمًا")[2] == "حال"  # on a doer's measure: a hal


@needs_parser
def test_a_relative_after_a_verb_whose_doer_was_said_is_its_object():
    assert _roles("لَا يَنْجَحُ الطَّالِبُ حَتَّى يَفْهَمَ مَا يَقْرَأُ")[5] == "مفعول به"
