"""XP rules (services/learner/rewards.py) and the rewards endpoints.

Run: python -m pytest tests/learner/test_rewards.py
"""
from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.learner import progress_db
from backend.services.learner.rewards import level_of, rewards_of
from tests.learner import sign_in

client = TestClient(app)
NAME = "amina"
AS: dict[str, str] = {}  # the name and its device-token cookie, filled by the fixture


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_db, "data_path", lambda _name: target)
    progress_db.reset_connection()
    sign_in.forget_all()
    sign_in.signup(client, NAME)
    AS.clear()
    AS.update(sign_in.as_(NAME))
    yield
    progress_db.reset_connection()


def answer(item="kitab", correct=True, headers=AS, **more):
    return client.post("/api/progress/attempts", json={"module": "quiz", "item": item, "correct": correct, **more},
                       headers=headers).json()


@pytest.mark.parametrize(("xp", "level", "into", "need"), [
    (0, 1, 0, 100),
    (99, 1, 99, 100),
    (100, 2, 0, 200),
    (299, 2, 199, 200),
    (300, 3, 0, 300),
    (650, 4, 50, 400),
])
def test_each_level_takes_a_little_longer(xp, level, into, need):
    assert level_of(xp, 100) == {"level": level, "into": into, "need": need}


def test_xp_today_counts_only_today():
    today = date(2026, 10, 14)
    days = [date(2026, 10, 13), today, today]
    assert rewards_of(days, today, 10, 100) == {"xp": 30, "xpToday": 20, "level": 1, "into": 30, "need": 100}


def test_a_right_answer_earns_and_says_the_new_total():
    saved = answer()
    assert saved["earned"] == 10
    assert saved["rewards"] == {"xp": 10, "xpToday": 10, "level": 1, "into": 10, "need": 100, "streak": 1}


def test_the_same_item_twice_in_a_day_earns_once():
    answer()
    again = answer()
    assert again["earned"] == 0
    assert again["rewards"]["xp"] == 10


def test_a_different_item_earns_again():
    answer("kitab")
    assert answer("qalam")["earned"] == 10


def test_a_wrong_answer_earns_nothing():
    saved = answer(correct=False)
    assert saved["earned"] == 0
    assert saved["rewards"]["xp"] == 0


def test_the_guest_record_earns_nothing():
    saved = answer(headers={})
    assert saved["saved"] is True
    assert saved["earned"] == 0
    assert saved["rewards"] is None


def test_rewards_needs_a_name_or_a_device():
    assert client.get("/api/progress/rewards").status_code == 422


def test_rewards_reads_back_the_total():
    answer("kitab")
    answer("qalam")
    assert client.get("/api/progress/rewards", headers=AS).json()["xp"] == 20


def test_today_is_the_learners_own_day():
    answer(tz=840)
    east = client.get("/api/progress/rewards", params={"tz": 840}, headers=AS).json()
    assert east["xpToday"] == 10


def test_a_zone_past_the_earth_is_refused():
    assert client.get("/api/progress/rewards", params={"tz": 900}, headers=AS).status_code == 422


DAY_MS = 86_400_000


def test_an_answer_that_waited_for_a_signal_lands_on_the_day_it_was_given():
    # Yesterday's answer, sent today: it earns yesterday's XP and keeps yesterday in the streak.
    yesterday = answer("kitab", ago_ms=DAY_MS)
    assert yesterday["earned"] == 10
    assert yesterday["rewards"]["xpToday"] == 0
    today = answer("kitab")
    assert today["earned"] == 10
    assert today["rewards"]["streak"] == 2


def test_an_answer_cannot_be_dated_further_back_than_the_cap():
    # Said to be a week old, it lands two days back (the cap), not a week back.
    answer("kitab", ago_ms=7 * DAY_MS)
    answer("qalam", ago_ms=DAY_MS)
    assert answer("bayt")["rewards"]["streak"] == 3


def test_a_negative_age_is_refused():
    response = client.post("/api/progress/attempts", headers=AS,
                           json={"module": "quiz", "item": "kitab", "correct": True, "ago_ms": -1})
    assert response.status_code == 422


def test_review_follows_the_order_answers_were_given_not_sent():
    # Right just now, then yesterday's wrong answer arrives: the wrong one came first, so the last word is right.
    from backend.services.learner import attempts
    answer("kitab", correct=True)
    answer("kitab", correct=False, ago_ms=DAY_MS)
    rows = list(progress_db.connection().execute(attempts._ANSWERS, (NAME, "quiz")))
    assert [row["correct"] for row in rows] == [0, 1]
