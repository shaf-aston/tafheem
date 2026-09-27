"""Nahw practice questions are filed in progress.db the moment they are made.

Whichever path wrote them, the AI or the offline templates, each is kept under
the source the page's badge showed, the same question for the same sentence is
kept once, and a database that will not take them never costs the learner the
questions themselves.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import ai as ai_service
from backend.services import progress_store

client = TestClient(app)
SENTENCE = "ذَهَبَ الطَّالِبُ إِلَى الْمَدْرَسَةِ"


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_store, "data_path", lambda _name: target)
    progress_store.reset_connection()
    yield
    progress_store.reset_connection()


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(ai_service, "is_ai_available", lambda: False)


@pytest.fixture
def online(monkeypatch):
    monkeypatch.setattr(ai_service, "is_ai_available", lambda: True)
    monkeypatch.setattr(ai_service, "analyze_iraab", lambda *_: {"words": []})
    monkeypatch.setattr(ai_service, "generate_practice", lambda *_: {"questions": [
        {"question": "ما إعراب الطالب؟", "answer": "فاعل مرفوع", "hint": "من فعل؟"},
        {"question": "ما نوع الجملة؟", "answer": "فعلية"},
    ]})


def kept(sentence=None):
    params = {"sentence": sentence} if sentence else {}
    response = client.get("/api/practice/kept", params=params)
    assert response.status_code == 200
    return response.json()["questions"]


def test_offline_questions_are_kept_as_shown(offline):
    shown = client.post("/api/practice", json={"sentence": SENTENCE}).json()
    rows = kept(SENTENCE)
    assert [(r["question"], r["answer"], r["hint"]) for r in rows] == [
        (q["question"], q["answer"], q["hint"]) for q in shown["questions"]
    ]
    assert {r["source"] for r in rows} == {shown["source"]["key"]} == {"nahw"}


def test_ai_questions_are_kept_under_the_ai_badge(online):
    shown = client.post("/api/practice", json={"sentence": SENTENCE}).json()
    assert shown["source"]["key"] == "ai"
    rows = kept(SENTENCE)
    assert [r["question"] for r in rows] == ["ما إعراب الطالب؟", "ما نوع الجملة؟"]
    assert rows[1]["hint"] is None
    assert {r["source"] for r in rows} == {"ai"}


def test_asking_twice_keeps_one_copy(offline):
    client.post("/api/practice", json={"sentence": SENTENCE})
    first = len(kept())
    client.post("/api/practice", json={"sentence": SENTENCE})
    assert len(kept()) == first > 0


def test_kept_filters_by_sentence(offline):
    client.post("/api/practice", json={"sentence": SENTENCE})
    client.post("/api/practice", json={"sentence": "الكِتَابُ مُفِيدٌ"})
    assert {r["sentence"] for r in kept(SENTENCE)} == {SENTENCE}
    assert len({r["sentence"] for r in kept()}) == 2


def test_a_broken_database_still_answers(offline, monkeypatch):
    def refuse(**_):
        raise OSError("disk full")

    monkeypatch.setattr(progress_store, "keep_questions", refuse)
    response = client.post("/api/practice", json={"sentence": SENTENCE})
    assert response.status_code == 200
    assert response.json()["questions"]


def test_forgetting_answers_keeps_the_questions(offline):
    client.post("/api/practice", json={"sentence": SENTENCE})
    client.delete("/api/progress")
    assert kept(SENTENCE)
