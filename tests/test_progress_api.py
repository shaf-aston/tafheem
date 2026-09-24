"""The progress endpoints: the app's first write path, so its edges are checked.

Every other endpoint here computes an answer and forgets it. This one keeps
what it is given, which makes it the one place where an unbounded or malformed
request has a lasting cost, so the caps are tested rather than assumed.

The rule that the server, not the page, decides who is answering is checked
too. It costs nothing today, when there is one learner; it is the whole reason
adding accounts later does not mean auditing this endpoint again.

Run: python -m pytest tests/test_progress_api.py
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import progress_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_store, "data_path", lambda _name: target)
    progress_store.reset_connection()
    yield
    progress_store.reset_connection()


def post(**body):
    return client.post("/api/progress/attempts", json=body)


def test_delete_forgets_every_answer():
    post(module="quiz", item="to-write", correct=False, ms=1500)
    response = client.delete("/api/progress")
    assert response.status_code == 200
    assert response.json() == {"deleted": 1}
    assert client.get("/api/progress/review").json()["items"] == []


def test_an_answer_is_saved_and_says_so():
    response = post(module="quiz", item="to-write", correct=False, ms=1500)
    assert response.status_code == 200
    assert response.json()["saved"] is True
    assert response.json()["id"] > 0


def test_the_summary_reads_back_what_was_written():
    post(module="quiz", item="to-write", correct=False, ms=1000)
    post(module="quiz", item="to-write", correct=True, ms=3000)
    item = client.get("/api/progress/summary", params={"module": "quiz"}).json()["items"][0]
    assert item == {"item": "to-write", "attempts": 2, "wrong": 1,
                    "avgMs": 2000, "inReview": True}


def test_review_lists_what_is_still_owed():
    post(module="quiz", item="to-write", correct=False)
    post(module="quiz", item="to-read", correct=True)
    assert client.get("/api/progress/review", params={"module": "quiz"}).json()["items"] == ["to-write"]


def test_a_module_with_no_answers_is_empty_not_an_error():
    response = client.get("/api/progress/summary", params={"module": "dictation"})
    assert response.status_code == 200
    assert response.json() == {"module": "dictation", "items": []}


@pytest.mark.parametrize("body", [
    {"module": "quiz", "correct": True},                          # no item
    {"item": "to-write", "correct": True},                        # no module
    {"module": "quiz", "item": "to-write"},                       # no verdict
    {"module": "quiz", "item": "to-write", "correct": True, "ms": -1},
    {"module": "quiz", "item": "", "correct": True},
    {"module": "q" * 33, "item": "to-write", "correct": True},
    {"module": "quiz", "item": "i" * 201, "correct": True},
    {"module": "quiz", "item": "to-write", "correct": True, "ms": 86_400_001},
])
def test_a_malformed_answer_is_refused(body):
    assert post(**body).status_code == 422


def test_an_oversized_context_is_refused():
    """The easiest abuse of a write endpoint is a big blob in a free-form field."""
    assert post(module="quiz", item="to-write", correct=True,
                context={"junk": "x" * 600}).status_code == 422


def test_the_page_cannot_choose_whose_record_it_writes():
    post(module="quiz", item="to-write", correct=False, user="someone-else")
    assert progress_store.review_items("quiz", "local") == ["to-write"]
    assert progress_store.review_items("quiz", "someone-else") == []


def test_feedback_is_kept_and_survives_the_wipe():
    ok = client.post("/api/progress/feedback", json={"module": "tamreen", "item": "q1", "message": " wrong harakah "})
    assert ok.status_code == 200 and ok.json()["id"] == 1
    client.delete("/api/progress")
    rows = progress_store._db().execute("SELECT module, item, message FROM feedback").fetchall()
    assert [tuple(r) for r in rows] == [("tamreen", "q1", "wrong harakah")]


@pytest.mark.parametrize("body", [
    {"module": "quiz", "message": "   "},
    {"module": "quiz", "message": "x" * 2001},
    {"module": "quiz"},
])
def test_feedback_rejects_empty_or_oversize(body):
    assert client.post("/api/progress/feedback", json=body).status_code == 422
