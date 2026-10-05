"""What is written onto a word, and the doer inside a verb, as the analyser shows them.

Runs typed sentences through the real endpoint and parser: the cards and the
picture a reader sees, not the functions behind them.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.syntax.catib_onnx import files_present

pytestmark = pytest.mark.skipif(not files_present(), reason="CATiB parser model files not present")
client = TestClient(app)
CONDITION = "إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا"
HADITH = "أَعَدَّ اللَّهُ لِمَنْ خَرَجَ فِي سَبِيلِهِ لاَ يُخْرِجُهُ إِلاَّ جِهَادٌ فِي سَبِيلِي وَإِيمَانٌ بِي وَتَصْدِيقٌ بِرُسُلِي"


def analysed(sentence: str) -> tuple[list[dict], dict[int, dict]]:
    """The cards, and the picture's leaf for each typed word."""
    body = client.post("/api/analyze", json={"sentence": sentence}).json()
    leaves = {}

    def walk(node):
        if node.get("word") is not None:
            leaves[node["word"]] = node
        for child in node.get("children", []):
            walk(child)
    walk(body["tree"]["tree"])
    return body["words"], leaves


def parts(leaf: dict) -> list[str]:
    return [part["role"] for part in leaf.get("parts", [])]


def test_the_answer_shows_its_fa_its_doer_and_its_object():
    _, leaves = analysed(CONDITION)
    answer = leaves[8]
    assert parts(answer) == ["حرف رابط", "فعل", "فاعل", "مفعول به"]
    assert "أنتَ" in answer["parts"][2]["detail"]
    assert parts(leaves[1]) == ["فعل ناقص", "اسم كان"]


def test_a_passive_verb_is_said_passive_and_its_object_is_the_second():
    cards, _ = analysed(CONDITION)
    assert "مبني للمجهول" in cards[4]["reason"]
    assert "مبني للمجهول" not in cards[1]["reason"]  # كُنْتَ opens with a damma, active all the same
    assert "المفعول الثاني" in cards[5]["book"]


def test_a_joining_waw_and_a_preposition_with_its_pronoun():
    cards, leaves = analysed(HADITH)
    assert parts(leaves[12])[0] == "حرف عطف"
    assert parts(leaves[13]) == ["حرف جر", "مجرور"]
    assert parts(leaves[5]) == ["مجرور", "مضاف إليه"]


def test_a_noun_with_pieces_on_it_is_not_read_as_a_command():
    cards, _ = analysed("الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ")
    assert cards[6]["role"] == "معطوف"


def test_a_command_is_never_passive():
    cards, leaves = analysed("اُكْتُبُوا الدَّرْسَ")
    assert "مبني للمجهول" not in cards[0]["reason"]
    assert "أنتم" in leaves[0]["parts"][1]["detail"]


def test_a_ta_verb_after_a_third_person_subject_is_she():
    _, leaves = analysed("هِنْدٌ تَكْتُبُ")
    assert leaves[1]["parts"][1]["detail"].endswith("هي")
