"""The practice questions say what the cards say: one analysis, asked about.

Runs typed sentences through the real endpoints, the cards and the questions a
learner sees, so a question can never answer with a name the cards do not give.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.syntax.catib_onnx import files_present

pytestmark = pytest.mark.skipif(not files_present(), reason="CATiB parser model files not present")
client = TestClient(app)


def asked(sentence: str) -> tuple[list[dict], list[dict]]:
    cards = client.post("/api/analyze", json={"sentence": sentence}).json()["words"]
    return cards, client.post("/api/practice", json={"sentence": sentence}).json()["questions"]


def test_the_role_question_answers_with_the_cards_own_reason():
    cards, questions = asked("مَنْ شَاءَ فَلْيَصُمْهُ وَمَنْ شَاءَ أَفْطَرَ")
    role = questions[1]
    assert "حرف جر" not in role["answer"]
    asked_about = next(card for card in cards if f"«{card['word']}»" in role["question"])
    assert asked_about["reason"] in role["answer"]


def test_the_doer_is_asked_about_first():
    cards, questions = asked("كَتَبَ الطَّالِبُ الدَّرْسَ")
    assert "«الطَّالِبُ»" in questions[1]["question"]
    assert cards[1]["reason"] in questions[1]["answer"]
