"""A condition the tying letter is written on is the answer of the condition before it, drawn whole as that answer.

فَإِمَّا يَأْتِيَنَّكُمْ مِنِّي هُدًى فَمَنْ تَبِعَ هُدَايَ فَلَا خَوْفٌ عَلَيْهِمْ (2:38): مَنْ تَبِعَ ... فَلَا خَوْفٌ is جواب الشرط of إمّا.
"""
from tests.nahw_helpers import analyze, needs_parser

AYAH = "فَإِمَّا يَأْتِيَنَّكُمْ مِنِّي هُدًى فَمَنْ تَبِعَ هُدَايَ فَلَا خَوْفٌ عَلَيْهِمْ"


def roles(node: dict) -> list:
    return [kid.get("role") for kid in node.get("children", [])]


@needs_parser
def test_the_inner_condition_is_the_outer_answer():
    tree = analyze(AYAH)["tree"]["tree"]
    outer = tree
    assert roles(outer) == ["إنْ الشرطية المدغمة في ما الزائدة", "فعل الشرط", "حرف رابط", "جواب الشرط"]
    inner = outer["children"][-1]
    assert roles(inner) == ["مبتدأ", "فعل الشرط", "حرف رابط", "جواب الشرط"]


@needs_parser
def test_a_plain_condition_keeps_its_own_answer():
    tree = analyze("مَنْ يَدْرُسْ فَإِنَّهُ نَاجِحٌ")["tree"]["tree"]
    assert roles(tree) == ["مبتدأ", "فعل الشرط", "حرف رابط", "جواب الشرط"]
