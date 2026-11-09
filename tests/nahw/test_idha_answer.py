"""An answer tied by a فاء is the first clause that carries it; later clauses join on to it.

After a non-jazim word (إذا، لو) the clause is «جملة الشرط», never a «فعل الشرط» (only a jazim
particle or noun has one); a clause joined by a conjunction written onto its verb (فَلْيَتَّقِ) is
a عطف جملة, never a صفة or حال of the noun before it; قَدْ before a past verb is حرف تحقيق.
"""
import pytest

from tests.nahw_helpers import analyze, cards, needs_parser

pytestmark = needs_parser

THE_SENTENCE = "إِذَا تَزَوَّجَ الْعَبْدُ فَقَدِ اسْتَكْمَلَ نِصْفَ الدِّينِ فَلْيَتَّقِ اللَّهَ فِي النِّصْفِ الْبَاقِي"


def nodes(node: dict):
    yield node
    for kid in node.get("children", []):
        yield from nodes(kid)


def top(sentence: str) -> dict:
    return analyze(sentence)["tree"]["tree"]


@pytest.mark.parametrize("sentence", [
    THE_SENTENCE,
    "إِذَا نَجَحَ الطَّالِبُ فَقَدْ فَازَ فَلْيَشْكُرِ اللَّهَ",  # not the sentence it was built on
])
def test_every_clause_after_the_tying_fa_is_the_answer_of_the_one_condition(sentence):
    picture = top(sentence)
    assert picture["label"] == "جُمْلَةٌ شَرْطِيَّةٌ"
    assert [kid.get("role") for kid in picture["children"]] == ["مفعول فيه", "جملة الشرط", "حرف رابط", "جواب الشرط"]
    answer = picture["children"][3]
    joined = [n for n in answer["children"] if n.get("label") == "جُمْلَةٌ فِعْلِيَّةٌ"]
    assert len(joined) == 1 and joined[0]["children"][0]["role"] == "حرف عطف"
    assert not any(n.get("role") in ("حال", "صفة") for n in nodes(picture))


def test_no_فعل_الشرط_after_idha_but_a_jazim_particle_keeps_it():
    assert not any(n.get("role") == "فعل الشرط" for n in nodes(top(THE_SENTENCE)))
    assert "وجملة الشرط في محل جر بالإضافة" in cards(THE_SENTENCE)[1]["reason"]
    jazim = top("إِنْ نَجَحَ الطَّالِبُ فَقَدْ فَازَ فَلْيَشْكُرِ اللَّهَ")
    assert [kid.get("role") for kid in jazim["children"]][:2] == ["حرف شرط جازم", "فعل الشرط"]


def test_qad_before_a_past_verb_is_tahqiq_and_before_a_present_verb_stays_plain():
    assert cards(THE_SENTENCE)[3]["reason"].startswith("حرف تحقيق")
    assert not cards("إِذَا جَاءَ زَيْدٌ فَقَدْ يَنْجَحُ")[3]["reason"].startswith("حرف تحقيق")
