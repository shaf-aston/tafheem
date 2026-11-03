"""A sentence typed with no short vowel on any word carries one line saying its voice and case were read
from word order; one vowel anywhere, or all of them, carries none (teacher.json case_said.unvowelled)."""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def asked(sentence: str) -> dict:
    return client.post("/api/analyze", json={"sentence": sentence}).json()


def test_a_sentence_without_vowels_carries_the_line_in_both_languages():
    line = asked("كتب الولد الدرس")["unvowelled"]
    assert line["en"].startswith("No harakat typed") and "لم تُكتب الحركات" in line["ar"]


def test_one_typed_vowel_or_all_of_them_carry_no_line():
    for sentence in ("كَتَبَ الْوَلَدُ الدَّرْسَ", "كتب الولدُ الدرس", "كتب الولد الدرسَ"):
        assert asked(sentence)["unvowelled"] is None, sentence


def test_a_sukun_or_shadda_alone_is_not_a_vowel():
    assert asked("كتب الولد الدرْس")["unvowelled"] is not None
