"""What is written onto a word, and the doer inside a verb, as the analyser shows them.

Runs typed sentences through the real endpoint and parser: the cards and the
picture a reader sees, not the functions behind them. A piece written onto a word
(بِـ، وَ، ـهُ) is a word of its own in the picture, with its own column.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.syntax.catib_onnx import files_present

pytestmark = pytest.mark.skipif(not files_present(), reason="CATiB parser model files not present")
client = TestClient(app)
CONDITION = "إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا"
HADITH = "أَعَدَّ اللَّهُ لِمَنْ خَرَجَ فِي سَبِيلِهِ لاَ يُخْرِجُهُ إِلاَّ جِهَادٌ فِي سَبِيلِي وَإِيمَانٌ بِي وَتَصْدِيقٌ بِرُسُلِي"


def analysed(sentence: str) -> tuple[list[dict], dict[str, list[tuple[dict, dict]]]]:
    """The cards, and each column's leaf with the unit around it, by the column's text."""
    body = client.post("/api/analyze", json={"sentence": sentence}).json()
    columns = body["tree"]["words"]
    leaves: dict[str, list[tuple[dict, dict]]] = {}

    def walk(node, unit):
        if node.get("word") is not None:
            leaves.setdefault(columns[node["word"]], []).append((node, unit))
        for child in node.get("children", []):
            walk(child, node)
    walk(body["tree"]["tree"], {})
    return body["words"], leaves


def parts(leaf: dict) -> list[str]:
    return [part["role"] for part in leaf.get("parts", [])]


def test_the_answer_shows_its_fa_its_doer_and_its_object():
    _, leaves = analysed(CONDITION)
    assert leaves["فَ"][0][0]["role"] == "حرف رابط"
    answer = leaves["اقْبَلْهَا"][0][0]
    assert parts(answer) == ["فعل", "فاعل", "مفعول به"]
    assert "أنتَ" in answer["parts"][1]["detail"]
    assert parts(leaves["كُنْتَ"][0][0]) == ["فعل ناقص", "اسم كان"]


def test_a_passive_verb_is_said_passive_and_its_object_is_the_second():
    cards, _ = analysed(CONDITION)
    assert "مبني للمجهول" in cards[4]["reason"]
    assert "مبني للمجهول" not in cards[1]["reason"]  # كُنْتَ opens with a damma, active all the same
    assert "المفعول الثاني" in cards[5]["book"]


def test_a_preposition_written_onto_a_relative_heads_a_jar_majroor_with_its_silah():
    _, leaves = analysed(HADITH)
    jar, unit = leaves["لِ"][0]
    assert jar["role"] == "حرف جر"
    assert unit["label"] == "جَارٌّ وَمَجْرُوْرٌ" and unit["detail"] == "متعلق بـأَعَدَّ"
    majroor = next(kid for kid in unit["children"] if kid is not jar)
    assert majroor["role"] == "مجرور" and majroor["label"] == "اِسْمٌ مَوْصُوْلٌ وَصِلَتُهُ"


def test_a_joining_waw_and_a_preposition_with_its_pronoun_are_words_of_their_own():
    _, leaves = analysed(HADITH)
    assert {leaf["role"] for leaf, _ in leaves["وَ"]} == {"حرف عطف"}
    jar, unit = leaves["بِ"][0]
    assert unit["label"] == "جَارٌّ وَمَجْرُوْرٌ" and unit["detail"].startswith("متعلق بـ")
    assert [kid["role"] for kid in unit["children"]] == ["حرف جر", "مجرور"]
    mudaf, idafa = leaves["سَبِيلِ"][0]
    assert [kid["role"] for kid in idafa["children"]] == ["مضاف", "مضاف إليه"]


def test_a_noun_with_pieces_on_it_is_not_read_as_a_command():
    cards, _ = analysed("الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ")
    assert cards[6]["role"] == "معطوف"


def test_a_command_is_never_passive():
    cards, leaves = analysed("اُكْتُبُوا الدَّرْسَ")
    assert "مبني للمجهول" not in cards[0]["reason"]
    assert "أنتم" in leaves["اُكْتُبُوا"][0][0]["parts"][1]["detail"]


def test_a_ta_verb_after_a_third_person_subject_is_she():
    _, leaves = analysed("هِنْدٌ تَكْتُبُ")
    assert leaves["تَكْتُبُ"][0][0]["parts"][1]["detail"].endswith("هي")
