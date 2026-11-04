"""A sentence drawn in halves side by side (a مبتدأ unit beside its unwritten خبر ثابت) is all of them,
so no half is the sentence alone: the مبتدأ unit keeps its job, not the name of what it is made of."""
from __future__ import annotations

import pytest

from tests.nahw_helpers import analyze, needs_parser

pytestmark = needs_parser


@pytest.mark.parametrize("sentence, inside", [
    # not كُوبٌ كَبِيرٌ مِنَ الْقَهْوَةِ: مِن on a measure brings its tamyeez (roles.json understood.measured),
    # so that phrase is the khabar of an unwritten هذا (test_phrase_alone), with no ثابت beside it
    ("رَجُلٌ كَرِيمٌ فِي الدَّارِ", ["موصوف", "صفة"]),
    ("كِتَابُ الطَّالِبِ فِي الْبَيْتِ", ["مضاف", "مضاف إليه"]),
])
def test_a_mubtada_unit_beside_an_unwritten_khabar_is_named_mubtada(sentence, inside):
    tree = analyze(sentence)["tree"]["tree"]
    halves = tree["children"]
    unit = next(kid for kid in halves if kid.get("children") and kid["children"][0].get("role") == inside[0])
    assert unit["role"] == "مبتدأ" and not unit.get("label")
    assert [kid["role"] for kid in unit["children"]] == inside
    assert any(kid.get("role") == "خبر" and kid.get("hidden") for kid in halves)
