"""Nahw practice questions are filed in progress.db the moment they are made.

Each is kept under the source the page's badge showed, the same question for the same sentence is
kept once, and a database that will not take them never costs the learner the
questions themselves.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
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


def kept(sentence=None):
    params = {"sentence": sentence} if sentence else {}
    response = client.get("/api/practice/kept", params=params)
    assert response.status_code == 200
    return response.json()["questions"]


def test_offline_questions_are_kept_as_shown():
    shown = client.post("/api/practice", json={"sentence": SENTENCE}).json()
    rows = kept(SENTENCE)
    assert [(r["question"], r["answer"], r["hint"]) for r in rows] == [
        (q["question"], q["answer"], q["hint"]) for q in shown["questions"]
    ]
    assert {r["source"] for r in rows} == {shown["source"]["key"]} == {"nahw"}


def test_asking_twice_keeps_one_copy():
    client.post("/api/practice", json={"sentence": SENTENCE})
    first = len(kept())
    client.post("/api/practice", json={"sentence": SENTENCE})
    assert len(kept()) == first > 0


def test_kept_filters_by_sentence():
    client.post("/api/practice", json={"sentence": SENTENCE})
    client.post("/api/practice", json={"sentence": "الكِتَابُ مُفِيدٌ"})
    assert {r["sentence"] for r in kept(SENTENCE)} == {SENTENCE}
    assert len({r["sentence"] for r in kept()}) == 2


def test_a_broken_database_still_answers(monkeypatch):
    def refuse(**_):
        raise OSError("disk full")

    monkeypatch.setattr(progress_store, "keep_questions", refuse)
    response = client.post("/api/practice", json={"sentence": SENTENCE})
    assert response.status_code == 200
    assert response.json()["questions"]


def test_forgetting_answers_keeps_the_questions():
    client.post("/api/practice", json={"sentence": SENTENCE})
    client.delete("/api/progress")
    assert kept(SENTENCE)
