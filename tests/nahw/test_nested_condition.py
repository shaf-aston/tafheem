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
    assert roles(outer) == ["حرف عطف", "إنْ الشرطية المدغمة في ما الزائدة", "فعل الشرط", "حرف رابط", "جواب الشرط"]
    assert "حرف عطف" not in roles(outer["children"][2])  # the فَ before إمّا is in front of the condition, not its clause
    inner = outer["children"][-1]
    assert roles(inner) == ["مبتدأ", "فعل الشرط", "حرف رابط", "جواب الشرط"]


@needs_parser
def test_a_plain_condition_keeps_its_own_answer():
    tree = analyze("مَنْ يَدْرُسْ فَإِنَّهُ نَاجِحٌ")["tree"]["tree"]
    assert roles(tree) == ["مبتدأ", "فعل الشرط", "حرف رابط", "جواب الشرط"]


@needs_parser
def test_an_in_written_on_the_tie_opens_the_answer():
    # إِنْ جِئْتَ فَإِنْ قُمْتَ قُمْتُ: the فَ starts a sentence, so the second إنْ opens one, and it is the first one's answer
    tree = analyze("إِنْ جِئْتَ فَإِنْ قُمْتَ قُمْتُ")["tree"]["tree"]
    assert roles(tree) == ["حرف شرط جازم", "فعل الشرط", "حرف رابط", "جواب الشرط"]
    assert roles(tree["children"][-1]) == ["حرف شرط جازم", "فعل الشرط", "جواب الشرط"]


@needs_parser
def test_inna_on_the_tie_stays_the_answer():
    tree = analyze("إِنْ تَدْرُسْ فَإِنَّكَ تَنْجَحُ")["tree"]["tree"]
    assert roles(tree["children"][-1])[0] == "حرف ناسخ مشبه بالفعل"
