"""XP rules (services/rewards.py) and the rewards endpoints.

Run: python -m pytest tests/test_rewards.py
"""
from __future__ import annotations

from datetime import date
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import progress_store
from backend.services.rewards import level_of, rewards_of

client = TestClient(app)
NAME = "amina"
AS = {"X-Tafheem-Profile": quote(NAME)}


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_store, "data_path", lambda _name: target)
    progress_store.reset_connection()
    client.post("/api/progress/signup", json={"keep": False}, headers=AS)
    yield
    progress_store.reset_connection()


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


def test_rewards_needs_a_name():
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
