"""Profiles: a learner signs up with a username and gets their own record.

No password, which is agreed. What is checked is that a username is signed up
once, that two names never mix, that one spelling is one person, and that
wiping or claiming touches only the name asking.

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
    if name is not None:
        signup(name)  # a second sign-up of the same name is a harmless 409
    return client.post("/api/progress/attempts", headers=as_(name),
                       json={"module": "quiz", "item": item, "correct": correct})


def items(name):
    if name is not None:
        signup(name)
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
    ("Straße", "strasse"),
    ("مهر\u200cناز", "مهر\u200cناز"),
])
def test_clean_name_folds_one_person_to_one_spelling(raw, clean):
    assert clean_name(raw) == clean


@pytest.mark.parametrize("raw", ["", "   ", "x" * 41, "ß" * 21, "<x>", "a/b", "local", " LOCAL ", "...", "-"])
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


def signup(name, keep=False):
    return client.post("/api/progress/signup", json={"keep": keep}, headers=as_(name))


def login(name):
    return client.post("/api/progress/login", headers=as_(name))


def test_signup_hands_back_the_one_spelling():
    assert signup("  Amina ").json() == {"name": "amina", "moved": 0}


def test_a_taken_username_cannot_sign_up_again():
    signup("Amina")
    response = signup("AMINA")
    assert response.status_code == 409
    assert response.json()["detail"] == "That username is taken"


def test_login_finds_a_signed_up_name_only():
    assert login("Amina").status_code == 404
    signup("Amina")
    assert login(" amina ").json() == {"name": "amina", "moved": 0}


def test_names_used_before_signup_existed_can_log_in():
    progress_store.record(module="quiz", item="to-go", correct=True, user="bilal")  # from before accounts
    progress_store.leave_feedback(module="quiz", message="x", user="cyra")  # reported, never answered
    progress_store.reset_connection()  # a restart, where the old names become accounts
    assert login("Bilal").status_code == 200
    assert login("Cyra").status_code == 200
    assert signup("Bilal").status_code == 409


def test_a_name_without_an_account_cannot_read_or_write():
    """A deleted account in another tab must not keep filing answers."""
    body = {"module": "quiz", "item": "to-write", "correct": True}
    response = client.post("/api/progress/attempts", headers=as_("ghost"), json=body)
    assert response.status_code == 401
    assert response.json()["detail"] == "Log in again: no account with that username"
    assert client.get("/api/progress/summary", headers=as_("ghost")).status_code == 401


def test_signup_with_a_bad_name_says_why():
    response = signup("<x>")
    assert response.status_code == 422
    assert response.json()["detail"] == "Names use letters, numbers, spaces, - _ ."


def test_keep_moves_this_devices_old_answers_to_the_name():
    answer(None, "to-write")
    answer(None, "to-read", correct=False)
    answer("Bilal", "to-go")
    assert signup("Amina", keep=True).json() == {"name": "amina", "moved": 2}
    assert items("Amina") == ["to-read", "to-write"]
    assert items(None) == []
    assert items("Bilal") == ["to-go"]


def test_without_keep_old_answers_stay_unnamed():
    answer(None, "to-write")
    signup("Amina")
    assert items(None) == ["to-write"]


def test_keep_leaves_the_shared_ai_question_cache_alone():
    progress_store.keep_questions(module="meaning", sentence="s", source="ai",
                                  questions=[{"question": "q", "answer": "a"}])
    signup("Amina", keep=True)
    assert len(progress_store.kept_questions("meaning")) == 1


def test_signup_and_login_need_a_name():
    assert client.post("/api/progress/signup", json={}).status_code == 422
    assert client.post("/api/progress/login").status_code == 422


def test_the_account_says_who_since_when_and_how_many_answers():
    signup("Amina")
    answer("Amina", "to-write")
    answer("Amina", "to-read", correct=False)
    body = client.get("/api/progress/account", headers=as_("Amina")).json()
    assert (body["name"], body["answers"]) == ("amina", 2)
    assert body["joined"].endswith("+00:00")
    assert client.get("/api/progress/account", headers=as_("Bilal")).status_code == 401
    assert client.get("/api/progress/account").status_code == 422


def test_deleting_the_account_frees_the_name_and_wipes_only_its_answers():
    signup("Amina")
    answer("Amina", "to-write")
    answer("Bilal", "to-read")
    client.post("/api/progress/feedback", headers=as_("Amina"), json={"module": "quiz", "message": "typo"})
    assert client.delete("/api/progress/account", headers=as_("Amina")).json() == {"deleted": 1}
    progress_store.reset_connection()  # a restart must not bring the name back from its reports
    assert login("Amina").status_code == 404
    assert progress_store.summary("quiz", "amina") == []
    assert items("Bilal") == ["to-read"]
    assert signup("Amina").status_code == 200


def test_the_leaderboard_ranks_accounts_by_words_learnt_and_finds_you():
    db_answer = lambda name, item, days: progress_store._db().execute(  # noqa: E731
        "INSERT INTO attempts (user, module, item, correct, at) VALUES (?, 'quiz', ?, 1, datetime('now', ?))",
        (name, item, f"-{days} days"))
    for name in ("Amina", "Bilal", "Cyra"):
        signup(name)
    for item in ("a", "b"):  # right on two separate days: learnt
        db_answer("bilal", item, 3), db_answer("bilal", item, 2)
    db_answer("amina", "a", 3), db_answer("amina", "a", 2)
    progress_store._db().commit()
    answer(None, "a")  # the guest record is nobody's, so it is not ranked
    body = client.get("/api/progress/leaderboard", params={"module": "quiz"}, headers=as_("Cyra")).json()
    assert [(r["rank"], r["name"], r["learnt"]) for r in body["rows"]] == [
        (1, "bilal", 2), (2, "amina", 1), (3, "cyra", 0)]
    assert body["you"]["rank"] == 3
    assert client.get("/api/progress/leaderboard").json()["you"] is None


# The shelf: what the page keeps for one account (settings, Grow steps, favourites),
# saved whole on the server so it follows the name to another device.

def shelf(name, data=None):
    if data is None:
        return client.get("/api/progress/saved", headers=as_(name))
    return client.put("/api/progress/saved", headers=as_(name), json={"data": data})


def test_the_shelf_is_kept_per_account_and_replaced_whole():
    signup("Amina"), signup("Bilal")
    assert shelf("Amina").json() == {"data": {}}
    assert shelf("Amina", {"settings": '{"size":"large"}', "progress:grow": "{}"}).status_code == 200
    shelf("Bilal", {"settings": '{"size":"small"}'})
    shelf("Amina", {"settings": '{"size":"medium"}'})
    assert shelf("Amina").json() == {"data": {"settings": '{"size":"medium"}'}}
    assert shelf("Bilal").json() == {"data": {"settings": '{"size":"small"}'}}


def test_the_guest_and_strangers_have_no_shelf():
    assert shelf(None).status_code == 422
    assert shelf(None, {"k": "v"}).status_code == 422
    assert shelf("Nobody").status_code == 401


def test_a_shelf_too_big_is_refused(monkeypatch):
    from backend.config import get_settings
    monkeypatch.setattr(get_settings(), "saved_max_bytes", 50)
    signup("Amina")
    assert shelf("Amina", {"k": "x" * 100}).status_code == 413
    assert shelf("Amina").json() == {"data": {}}


def test_start_over_and_delete_empty_the_shelf():
    signup("Amina")
    shelf("Amina", {"k": "v"})
    client.delete("/api/progress", headers=as_("Amina"))
    assert shelf("Amina").json() == {"data": {}}
    shelf("Amina", {"k": "v"})
    client.delete("/api/progress/account", headers=as_("Amina"))
    signup("Amina")
    assert shelf("Amina").json() == {"data": {}}
