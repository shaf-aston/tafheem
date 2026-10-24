"""A guest's record is their device's own (docs/plans/2026-10-24-device-guest.md).

The page makes a random id once and sends it in X-Tafheem-Guest while nobody is logged in. What is
checked: two devices never mix, sign-up's keep and the Start over wipe touch only this device, a
guest id can never act as an account, a bad id is refused, no header is still the old shared record,
and idle device records are swept.

Run: python -m pytest tests/learner/test_device_guest.py
"""
from __future__ import annotations

from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.learner import progress_store
from backend.services.learner.username import GUEST, clean_name, device_key, is_guest

client = TestClient(app)

PHONE = "0" * 31 + "1"
LAPTOP = "ab" * 16


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_store, "data_path", lambda _name: target)
    progress_store.reset_connection()
    yield
    progress_store.reset_connection()


def on(device=None, name=None):
    """The headers the page sends: the device's id while nobody is logged in, the name once someone is."""
    headers = {"X-Tafheem-Guest": device} if device is not None else {}
    return {**headers, "X-Tafheem-Profile": quote(name)} if name is not None else headers


def answer(headers, item, correct=True):
    return client.post("/api/progress/attempts", headers=headers,
                       json={"module": "quiz", "item": item, "correct": correct})


def items(headers):
    response = client.get("/api/progress/summary", params={"module": "quiz"}, headers=headers)
    assert response.status_code == 200
    return [row["item"] for row in response.json()["items"]]


def signup(name, device=None, keep=False):
    return client.post("/api/progress/signup", json={"keep": keep}, headers=on(device, name))


# The key

def test_a_device_key_is_its_id_under_a_prefix_no_name_can_have():
    assert device_key(LAPTOP) == f"guest:{LAPTOP}"
    with pytest.raises(ValueError):
        clean_name(device_key(LAPTOP))


@pytest.mark.parametrize("bad", ["", "0" * 31, "0" * 33, "G" * 32, "AB" * 16, f" {LAPTOP}", "../" + "0" * 29,
                                 "0" * 31 + "\n"])
def test_a_device_id_is_32_lowercase_hex_and_nothing_else(bad):
    with pytest.raises(ValueError):
        device_key(bad)


def test_the_guests_are_the_shared_record_and_device_keys_only():
    assert is_guest(GUEST)
    assert is_guest(device_key(PHONE))
    assert not is_guest("amina")
    assert not is_guest("guest")


# Two devices, two records (G1)

def test_two_devices_keep_two_records():
    answer(on(PHONE), "to-write")
    answer(on(LAPTOP), "to-read")
    assert items(on(PHONE)) == ["to-write"]
    assert items(on(LAPTOP)) == ["to-read"]
    assert items(on()) == []


def test_review_and_overview_are_the_devices_own():
    answer(on(PHONE), "to-write", correct=False)
    review = lambda device: client.get("/api/progress/review", params={"module": "quiz"}, headers=on(device))
    assert review(PHONE).json()["items"] == ["to-write"]
    assert review(LAPTOP).json()["items"] == []
    overview = lambda device: client.get("/api/progress/overview", headers=on(device)).json()["attempts"]
    assert (overview(PHONE), overview(LAPTOP)) == (1, 0)


def test_no_header_is_still_the_old_shared_record():
    """A page cached before devices had ids keeps working (G7)."""
    answer(on(), "to-write")
    assert items(on()) == ["to-write"]
    assert items(on(PHONE)) == []


def test_a_bad_device_id_is_refused_not_filed():
    response = answer(on("not-an-id"), "to-write")
    assert response.status_code == 422
    assert response.json()["detail"] == "Not a device id"
    assert progress_store._db().execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0


def test_a_logged_in_name_wins_over_the_device():
    signup("Amina")
    answer(on(PHONE, "Amina"), "to-write")
    assert items(on(name="Amina")) == ["to-write"]
    assert items(on(PHONE)) == []


def test_a_bad_device_id_beside_a_name_is_not_read():
    signup("Amina")
    assert answer(on("not-an-id", "Amina"), "to-write").status_code == 200
    assert items(on(name="Amina")) == ["to-write"]


def test_checked_practice_reads_the_devices_record(monkeypatch):
    asked = []
    monkeypatch.setattr(progress_store, "summary", lambda module, user: asked.append(user) or [])
    client.post("/api/practice/checked", headers=on(PHONE))
    assert asked == [device_key(PHONE)]


def test_a_guest_earns_nothing_yet():
    body = answer(on(PHONE), "to-write").json()
    assert (body["earned"], body["rewards"]) == (0, None)


# A guest is never an account (G6)

def test_a_device_cannot_sign_up_log_in_or_use_account_routes():
    assert client.post("/api/progress/signup", json={}, headers=on(PHONE)).status_code == 422
    assert client.post("/api/progress/login", headers=on(PHONE)).status_code == 422
    for path in ("/api/progress/account", "/api/progress/saved", "/api/progress/rewards", "/api/progress/circles"):
        assert client.get(path, headers=on(PHONE)).status_code == 422, path


def test_a_device_never_becomes_an_account():
    """Opening the file turns names from before sign-up into accounts; a device's record is not one."""
    answer(on(PHONE), "a")
    client.post("/api/progress/feedback", headers=on(LAPTOP), json={"module": "quiz", "message": "typo"})
    progress_store.reset_connection()
    assert progress_store.account_names() == []


def test_a_device_is_not_ranked():
    answer(on(PHONE), "a")
    body = client.get("/api/progress/leaderboard", params={"module": "quiz"}, headers=on(PHONE)).json()
    assert (body["rows"], body["you"]) == ([], None)


# Keep and Start over touch this device only (G2, G3)

def test_keep_moves_only_this_devices_answers_and_reports():
    answer(on(PHONE), "to-write")
    answer(on(PHONE), "to-read", correct=False)
    client.post("/api/progress/feedback", headers=on(PHONE), json={"module": "quiz", "message": "typo"})
    answer(on(LAPTOP), "to-go")
    answer(on(), "to-sit")
    assert signup("Amina", PHONE, keep=True).json()["answers"] == 2
    assert items(on(name="Amina")) == ["to-read", "to-write"]
    assert items(on(PHONE)) == []
    assert items(on(LAPTOP)) == ["to-go"]
    assert items(on()) == ["to-sit"]
    assert [row[0] for row in progress_store._db().execute("SELECT user FROM feedback")] == ["amina"]


def test_keep_from_a_page_with_no_device_takes_nothing():
    """The shared record holds every old page's answers, so no one sign-up may take them all."""
    answer(on(), "to-sit")
    assert signup("Amina", keep=True).json()["answers"] == 0
    assert items(on()) == ["to-sit"]


def test_without_keep_the_device_keeps_its_answers():
    answer(on(PHONE), "to-write")
    signup("Amina", PHONE)
    assert items(on(PHONE)) == ["to-write"]
    assert items(on(name="Amina")) == []


def test_start_over_wipes_only_this_device():
    answer(on(PHONE), "to-write")
    answer(on(LAPTOP), "to-read")
    answer(on(), "to-sit")
    assert client.delete("/api/progress", headers=on(PHONE)).json() == {"deleted": 1}
    assert items(on(PHONE)) == []
    assert items(on(LAPTOP)) == ["to-read"]
    assert items(on()) == ["to-sit"]


# The sweep (G8)

def aged(user, days, item="a"):
    progress_store._db().execute(
        "INSERT INTO attempts (user, module, item, correct, at) VALUES (?, 'quiz', ?, 1, datetime('now', ?))",
        (user, item, f"-{days} days"))


def test_the_sweep_drops_idle_devices_only():
    idle, fresh = device_key(PHONE), device_key(LAPTOP)
    db = progress_store._db()
    with db:
        aged(idle, 200), aged(idle, 181, "b")
        aged(fresh, 300), aged(fresh, 10, "b")  # an old answer, but used lately: kept whole
        aged("amina", 400)
        aged(GUEST, 400)
    progress_store.leave_feedback(module="quiz", message="typo", user=idle)
    assert progress_store.sweep_guests(180) == 2
    users = {row[0] for row in db.execute("SELECT user FROM attempts")}
    assert users == {fresh, "amina", GUEST}
    assert len(progress_store.summary("quiz", fresh)) == 2
    assert [row[0] for row in db.execute("SELECT user FROM feedback")] == [""]


def test_the_sweep_never_reaches_past_the_prefix():
    """The range stops at "guest;", so a name sorting just after the prefix is never swept."""
    with progress_store._db():
        aged("guest;x", 400), aged("guest", 400), aged("guests", 400)
    assert progress_store.sweep_guests(180) == 0


def test_the_sweep_keeps_a_device_answering_at_the_edge():
    with progress_store._db():
        aged(device_key(PHONE), 179)
    assert progress_store.sweep_guests(180) == 0
