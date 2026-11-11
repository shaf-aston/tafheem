"""T9 (docs/plans/2026-11-11-security.md §3): the page grades its own answers, so a quiz answer must at least
name a real word of the quiz, and the ranking counts only those. A script can no longer file made-up ids
into "words learnt", the ranking's measure."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import app
from backend.services.learner import attempts, progress_db, quiz_words
from tests.learner import sign_in
from tests.learner.sign_in import as_

client = TestClient(app)
REAL = quiz_words._keys  # the conftest swaps it out per test; this is the one read from words.json


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(progress_db, "data_path", lambda _name: tmp_path / "progress.db")
    monkeypatch.setattr(quiz_words, "_keys", REAL)
    progress_db.reset_connection()
    sign_in.forget_all()
    yield
    progress_db.reset_connection()


def answer(module, item, name="Amina"):
    return client.post("/api/progress/attempts", headers=as_(name),
                       json={"module": module, "item": item, "correct": True})


def test_the_real_list_is_read():
    keys = REAL()
    assert keys and "train" in keys and len(keys) > 5000


@pytest.mark.parametrize("module", ["quiz", "quiz:ur"])
def test_a_quiz_answer_must_name_a_quiz_word(module):
    sign_in.signup(client, "Amina")
    assert answer(module, "train").status_code == 200
    refused = answer(module, "made-up-1")
    assert refused.status_code == 422 and refused.json()["detail"] == "Not a word of the quiz"


def test_other_panels_name_their_own_items():
    sign_in.signup(client, "Amina")
    assert answer("voice", "any-id-of-its-own").status_code == 200
    assert answer("quizzes", "x").status_code == 200  # only "quiz" and "quiz:<language>" are the quiz


def test_the_ranking_counts_only_quiz_words_whatever_was_filed_before(monkeypatch):
    sign_in.signup(client, "Amina")
    monkeypatch.setattr(attempts.review_schedule, "is_known", lambda _card, _now: True)  # the filter, not the schedule
    for item in ("train", "made-up-1", "made-up-2"):  # filed straight in, as before the rule
        attempts.record(module="quiz", item=item, correct=True, user="amina")
    monkeypatch.setattr(quiz_words, "_keys", lambda: None)
    unchecked = attempts.learnt("quiz", "amina")
    monkeypatch.setattr(quiz_words, "_keys", REAL)
    checked = attempts.learnt("quiz", "amina")
    assert (unchecked, checked) == (3, 1)  # only "train" is a word of the quiz
    overview = client.get("/api/progress/overview", headers=as_("Amina")).json()
    assert overview["learnt"] == checked


def test_a_missing_list_refuses_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(quiz_words, "WORDS", tmp_path / "gone.json")
    REAL.cache_clear()
    try:
        assert REAL() is None and quiz_words.allowed("quiz", "anything")
    finally:
        monkeypatch.undo()
        REAL.cache_clear()


def test_answers_have_a_per_visitor_limit(monkeypatch):
    sign_in.signup(client, "Amina")
    monkeypatch.setattr(get_settings(), "answer_per_minute", 2)
    from backend.services.core import ratelimit
    monkeypatch.setattr(ratelimit.ANSWER.each, "asks", {})
    codes = [answer("quiz", "train").status_code for _ in range(4)]
    assert codes.count(429) >= 1 and codes[0] == 200


def test_the_answer_limit_is_per_account_so_a_class_behind_one_address_is_many(monkeypatch):
    from backend.services.core import ratelimit
    monkeypatch.setattr(get_settings(), "answer_per_minute", 2)
    monkeypatch.setattr(ratelimit.ANSWER.each, "asks", {})
    for name in ("Amina", "Bilal"):
        sign_in.signup(client, name)
    same_address = {"X-Real-IP": "203.0.113.9"}
    codes = [client.post("/api/progress/attempts", headers={**as_(name), **same_address},
                         json={"module": "quiz", "item": "train", "correct": True}).status_code
             for name in ("Amina", "Bilal", "Amina", "Bilal", "Amina")]
    assert codes == [200, 200, 200, 200, 429]
