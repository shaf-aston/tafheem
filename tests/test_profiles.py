"""Profiles: a learner types a name and gets their own record.

No password: anyone typing the same name sees the same record, which is agreed.
What is checked is that two names never mix, that one spelling of a name is one
person, and that wiping or claiming touches only the name asking.

Run: python -m pytest tests/test_profiles.py
"""
from __future__ import annotations

from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import progress_store
from backend.services.profile import clean_name

client = TestClient(app)


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_store, "data_path", lambda _name: target)
    progress_store.reset_connection()
    yield
    progress_store.reset_connection()


def as_(name):
    """The header the page sends: percent-encoded, since headers cannot carry Arabic."""
    return {"X-Tafheem-Profile": quote(name)} if name is not None else {}


def answer(name, item, correct=True):
    return client.post("/api/progress/attempts", headers=as_(name),
                       json={"module": "quiz", "item": item, "correct": correct})


def items(name):
    response = client.get("/api/progress/summary", params={"module": "quiz"}, headers=as_(name))
    assert response.status_code == 200
    return [row["item"] for row in response.json()["items"]]


@pytest.mark.parametrize("raw, clean", [
    (" Amina ", "amina"),
    ("AMINA", "amina"),
    ("a  b", "a b"),
    ("عائشة", "عائشة"),
    ("عَائِشَة", "عَائِشَة"),          # tashkeel kept: a different spelling is a different name
    ("Amina-2_b.c", "amina-2_b.c"),
    ("x" * 40, "x" * 40),
])
def test_clean_name_folds_one_person_to_one_spelling(raw, clean):
    assert clean_name(raw) == clean


@pytest.mark.parametrize("raw", ["", "   ", "x" * 41, "<x>", "a/b", "local", " LOCAL "])
def test_clean_name_refuses_what_is_not_a_name(raw):
    with pytest.raises(ValueError):
        clean_name(raw)


def test_two_names_keep_two_records():
    answer("Amina", "to-write")
    answer("Bilal", "to-read")
    assert items("Amina") == ["to-write"]
    assert items("bilal ") == ["to-read"]


def test_an_arabic_name_travels_and_is_its_own_record():
    answer("عائشة", "to-write")
    assert items("عائشة") == ["to-write"]
    assert items("Amina") == []


def test_no_name_is_the_old_shared_record():
    answer(None, "to-write")
    assert items(None) == ["to-write"]
    assert items("Amina") == []


@pytest.mark.parametrize("bad", ["<x>", "local", "x" * 41])
def test_a_bad_name_is_refused_not_filed(bad):
    assert answer(bad, "to-write").status_code == 422
    assert progress_store._db().execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0


def test_forget_wipes_only_the_name_asking():
    answer("Amina", "to-write")
    answer("Bilal", "to-read")
    response = client.delete("/api/progress", headers=as_("Amina"))
    assert response.json() == {"deleted": 1}
    assert items("Amina") == []
    assert items("Bilal") == ["to-read"]


def test_claim_moves_this_devices_old_answers_to_the_name():
    answer(None, "to-write")
    answer(None, "to-read", correct=False)
    answer("Bilal", "to-go")
    response = client.post("/api/progress/claim", json={}, headers=as_("Amina"))
    assert response.status_code == 200
    assert response.json() == {"moved": 2}
    assert items("Amina") == ["to-read", "to-write"]
    assert items(None) == []
    assert items("Bilal") == ["to-go"]


def test_claim_leaves_the_shared_ai_question_cache_alone():
    progress_store.keep_questions(module="meaning", sentence="s", source="ai",
                                  questions=[{"question": "q", "answer": "a"}])
    client.post("/api/progress/claim", json={}, headers=as_("Amina"))
    assert len(progress_store.kept_questions("meaning")) == 1


def test_claim_needs_a_name():
    assert client.post("/api/progress/claim", json={}).status_code == 422
