"""Checked practice sentences: the AI writes, a plain program checks every word.

Run: python -m pytest tests/test_sentence_check.py
"""
from __future__ import annotations

import json
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import ai, progress_store, sentence_check
from backend.services.sentence_check import check

LEMMAS = {"الكتاب": "كتاب", "كتب": "كتب", "الولد": "ولد", "البيت": "بيت"}
def fake_lemma(word):
    return LEMMAS.get(sentence_check.fold(word))
ALLOWED = {"كتاب", "كتب", "ولد"}


def test_a_sentence_of_learnt_words_passes():
    assert check("كتب الولد الكتاب", ALLOWED, fake_lemma) == []


def test_one_unlearnt_word_is_named():
    assert check("كتب الولد البيت", ALLOWED, fake_lemma) == ["البيت"]


def test_a_word_with_no_lemma_is_bad():
    assert check("كتب زززز", ALLOWED, fake_lemma) == ["زززز"]


def test_particles_are_always_allowed():
    assert check("كتب الولد في البيت", ALLOWED | {"بيت"}, fake_lemma) == []
    assert check("و كتب", ALLOWED, fake_lemma) == []


def test_tashkeel_is_ignored_for_lookup():
    assert check("كَتَبَ الوَلَدُ", ALLOWED, fake_lemma) == []


@pytest.mark.parametrize("sentence", ["", "   ", "hello world", "كتب hello", "كتب 3", "كتب\u200cزززز"])
def test_empty_or_non_arabic_or_glued_text_never_passes(sentence):
    assert check(sentence, ALLOWED, fake_lemma)


def test_a_free_particle_does_not_open_a_lookalike():
    assert check("كتب علي", ALLOWED, fake_lemma) == ["علي"]


def test_the_real_lemma_lookup_finds_the_dictionary_form():
    assert sentence_check.fold(sentence_check.lemma_of("الكتاب")) == "كتاب"


def test_learnt_words_bring_their_spellings_and_lemmas():
    words = sentence_check.learnt_words(["book"])
    assert words and all(word["meaningKey"] == "book" for word in words)
    assert "كتاب" in sentence_check.allowed(words)


# ── the AI's narrow job, with the backend faked ──────────────────────────────

def fake_ai(monkeypatch, answers):
    replies = iter(answers)
    monkeypatch.setattr(ai, "is_ai_available", lambda: True)
    monkeypatch.setattr(ai, "_ask", lambda prompt, max_tokens: next(replies))


def test_a_bad_try_is_thrown_away_and_the_next_good_one_kept(monkeypatch):
    fake_ai(monkeypatch, [{"ar": "البيت", "en": "the house"}, {"ar": "الكتاب", "en": "the book"}])
    assert ai.checked_sentence(["كتاب"], lambda ar: ar == "الكتاب") == {"ar": "الكتاب", "en": "the book"}


def test_a_failed_call_is_a_failed_try(monkeypatch):
    def flaky(prompt, max_tokens):
        raise TimeoutError
    monkeypatch.setattr(ai, "_ask", flaky)
    assert ai.checked_sentence(["كتاب"], lambda ar: True) is None


def test_three_bad_tries_give_nothing(monkeypatch):
    fake_ai(monkeypatch, [{"ar": "البيت", "en": "x"}] * 3)
    assert ai.checked_sentence(["كتاب"], lambda ar: False) is None


# ── the endpoint ─────────────────────────────────────────────────────────────

client = TestClient(app)
NAME = {"X-Tafheem-Profile": quote("amina")}


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_store, "data_path", lambda _name: target)
    progress_store.reset_connection()
    yield
    progress_store.reset_connection()


def learn(keys):
    """Answer each word right, spread over a month, so the schedule calls it learnt."""
    db = progress_store._db()
    with db:
        for key in keys:
            for days in (30, 20, 10, 4, 1):
                db.execute(
                    "INSERT INTO attempts (user, module, item, correct, at) "
                    "VALUES ('amina', 'quiz', ?, 1, datetime('now', ?))", (key, f"-{days} days"))


def common_keys(n):
    words = json.loads(sentence_check.WORDS.read_text("utf-8"))["words"]
    keys = []
    for word in sorted(words, key=lambda w: -w.get("timesInQuran", 0)):
        if word.get("lemmas") and word["meaningKey"] not in keys:
            keys.append(word["meaningKey"])
    return keys[:n]


def test_too_few_learnt_words_says_so():
    learn(common_keys(3))
    response = client.post("/api/practice/checked", headers=NAME)
    assert response.status_code == 409
    assert response.json()["detail"] == "Learn 10 words first"


def test_a_checked_sentence_comes_back_with_its_words(monkeypatch):
    learn(["book", *common_keys(12)])
    fake_ai(monkeypatch, [{"ar": "الكِتَابُ", "en": "the book"}])
    response = client.post("/api/practice/checked", headers=NAME)
    assert response.status_code == 200
    body = response.json()
    assert body["ar"] == "الكِتَابُ" and body["en"] == "the book"
    assert "كِتَاب" in body["words"]


def test_no_passing_sentence_is_a_503(monkeypatch):
    learn(common_keys(12))
    fake_ai(monkeypatch, [{"ar": "زززز", "en": "x"}] * 3)
    response = client.post("/api/practice/checked", headers=NAME)
    assert response.status_code == 503
    assert response.json()["detail"] == "Could not make a checked sentence, try again"
