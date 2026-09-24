"""Choosing an ear, falling through to the next, and giving up on a dead one.

No network and no engine: both ears are stood in for, so what is tested is the
one thing this file owns, which is the order they are asked in and what happens
when one will not answer. How each ear actually hears is tested next door
(test_recitation_hosted.py for Groq, test_recitation.py for this machine).

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import app
from backend.services import journal
from backend.services.recitation import ears

SOUND = b"pretend this is a recording"


class Rejected(Exception):
    """An SDK error carrying an HTTP status, shaped the way the real ones are."""

    def __init__(self, status: int):
        super().__init__(f"HTTP {status}")
        self.response = type("Response", (), {"status_code": status})()


@pytest.fixture(autouse=True)
def fresh():
    """No ear stays retired or resting from one test into the next."""
    def reset():
        for ear in (ears.named("hosted"), ears.named("letters"), ears.named("here")):
            ear.retired_reason = ""
            ear._resting_until = 0.0
            ear._resting_reason = ""

    reset()
    yield
    reset()


@pytest.fixture
def both(monkeypatch):
    """Both ears, each answering with its own name, and a note of who was asked."""
    asked: list[str] = []

    def install(hosted_fails=None, here_fails=None, available=True):
        def hosted_hears(audio, language, hint):
            asked.append("hosted")
            if hosted_fails:
                raise hosted_fails
            return "hosted heard it"

        def here_hears(audio, language, hint):
            asked.append("here")
            if here_fails:
                raise here_fails
            return "here heard it"

        monkeypatch.setattr(ears.named("hosted"), "transcribe", hosted_hears)
        monkeypatch.setattr(ears.named("here"), "transcribe", here_hears)
        monkeypatch.setattr(ears.named("hosted"), "is_available", lambda: available)
        return asked

    return install


def test_the_quick_ear_is_asked_first_and_the_slow_one_is_not_troubled(both):
    asked = both()
    assert ears.hear(SOUND, None, "") == "hosted heard it"
    assert asked == ["hosted"]


def test_an_ear_that_does_not_answer_falls_through_to_the_next(both):
    """No internet, and the reader never finds out. The whole point of a chain."""
    asked = both(hosted_fails=ConnectionError("getaddrinfo failed"))
    assert ears.hear(SOUND, None, "") == "here heard it"
    assert asked == ["hosted", "here"]


def test_a_rejected_key_is_struck_off_and_not_tried_a_second_time(both):
    """The bug this whole change exists for: three recordings in the log each
    paid a round trip to be told the same 401. Now the first one pays it."""
    asked = both(hosted_fails=Rejected(401))
    assert ears.hear(SOUND, None, "") == "here heard it"
    assert ears.hear(SOUND, None, "") == "here heard it"
    assert asked == ["hosted", "here", "here"]
    assert "key was rejected" in ears.named("hosted").retired_reason


@pytest.mark.parametrize("status, retires", [
    (401, True), (403, True), (404, True),
    # An allowance spent for the hour, or a bad gateway, fixes itself, so
    # these rest instead of being struck off for the rest of the run (see the
    # rest() tests below for what "rests" means for the next call).
    (429, False), (500, False), (503, False),
])
def test_only_a_settled_failure_retires_an_ear(both, status, retires):
    both(hosted_fails=Rejected(status))
    ears.hear(SOUND, None, "")
    assert bool(ears.named("hosted").retired_reason) is retires


def test_a_non_permanent_failure_rests_the_hosted_ear_rather_than_retiring_it(both):
    both(hosted_fails=Rejected(500))
    assert ears.hear(SOUND, None, "") == "here heard it"
    assert ears.named("hosted").retired_reason == ""
    assert ears.named("hosted").resting()


def test_a_resting_ear_is_skipped_like_a_retired_one(both):
    """The bug rest() exists for, one step short of retiring: a 500 that has
    not settled yet must not be asked again on the very next recording."""
    asked = both(hosted_fails=Rejected(500))
    ears.hear(SOUND, None, "")  # fails, starts resting
    asked.clear()
    assert ears.hear(SOUND, None, "") == "here heard it"
    assert asked == ["here"], "a resting hosted ear must not be tried again yet"


def test_a_rest_is_over_at_exactly_its_own_boundary(monkeypatch):
    """resting() reads `now < until`; at now == until the rest must already be
    treated as over, not one tick short of it."""
    ear = ears.named("hosted")
    monkeypatch.setattr("time.monotonic", lambda: 1000.0)
    ear.rest(10.0, "bad gateway")  # _resting_until becomes 1010.0
    monkeypatch.setattr("time.monotonic", lambda: 1010.0)
    assert ear.resting() == ""


def test_a_rest_expires_and_the_ear_is_tried_again(both):
    asked = both(hosted_fails=Rejected(500))
    ears.hear(SOUND, None, "")
    ears.named("hosted").rest(-1, "let the rest already be over")
    asked.clear()
    assert ears.hear(SOUND, None, "") == "here heard it"
    assert asked == ["hosted", "here"], "the rest is over, so hosted is tried again"


def test_a_permanent_failure_is_not_also_left_resting(both):
    both(hosted_fails=Rejected(401))
    ears.hear(SOUND, None, "")
    assert ears.named("hosted").retired_reason
    assert ears.named("hosted").resting() == "", "retired is stronger, nothing left to rest from"


def test_the_order_comes_from_config(both, monkeypatch):
    monkeypatch.setattr(get_settings(), "recitation_ears", "here,hosted")
    asked = both()
    assert ears.hear(SOUND, None, "") == "here heard it"
    assert asked == ["here"]


def test_a_mistyped_ear_name_still_leaves_the_app_able_to_listen(both, monkeypatch, caplog):
    """A typo in a setting must not make the app deaf: this machine is always
    there at the end of the order, whatever the setting says."""
    monkeypatch.setattr(get_settings(), "recitation_ears", "hosted,ear-trumpet")
    asked = both(hosted_fails=ConnectionError("no internet"))
    assert ears.hear(SOUND, None, "") == "here heard it"
    assert asked == ["hosted", "here"]
    assert "ear-trumpet" in caplog.text


def test_an_unreadable_recording_stops_the_chain_rather_than_walking_it(both):
    """Trying the next ear only spends more seconds reaching the same answer:
    no engine can read a recording that has no sound in it."""
    asked = both(hosted_fails=ears.Unreadable("no sound in it"))
    with pytest.raises(ears.Unreadable):
        ears.hear(SOUND, None, "")
    assert asked == ["hosted"]


def test_an_unreadable_recording_is_answered_415_and_not_500(monkeypatch):
    """It reached the reader as "Could not make that out", which blames the
    listening for something the recording did. Record it again is actionable."""
    def unreadable(*a, **k):
        raise ears.Unreadable("That recording could not be read. Record it again.")

    monkeypatch.setattr("backend.routers.listen.recitation.hear", unreadable)
    # A real webm header with nothing playable behind it, which is what the
    # browser sent: is_audio lets it through, only opening it finds out.
    answer = TestClient(app).post(
        "/api/listen", files={"audio": ("r.webm", b"\x1a\x45\xdf\xa3 and then nothing", "audio/webm")},
    )
    assert answer.status_code == 415
    assert "Record it again" in answer.json()["detail"]


def test_the_health_line_says_which_ear_would_answer(both):
    both()
    body = TestClient(app).get("/api/health").json()
    assert body["ear"] == get_settings().recitation_hosted_model

    ears.named("hosted").retire("the API key was rejected")
    assert TestClient(app).get("/api/health").json()["ear"].startswith("local-")


def test_the_health_line_names_recitation_words_and_sureness_separately(both, monkeypatch):
    """Words are heard by whichever ear answers first, same as `ear`; sureness
    is always this machine's model, whatever wrote the words down. With Groq
    gone a recitation is written by the letters ear, a search by the one here."""
    both()
    monkeypatch.setattr(ears.letters, "installed", lambda: True)
    body = TestClient(app).get("/api/health").json()
    assert body["recite_ear"] == get_settings().recitation_hosted_model
    assert body["recite_sure"] == f"local-{get_settings().recitation_model}"

    ears.named("hosted").retire("the API key was rejected")
    body = TestClient(app).get("/api/health").json()
    assert body["recite_ear"] == "letters"
    assert body["ear"].startswith("local-")
    assert body["recite_sure"] == f"local-{get_settings().recitation_model}"


def test_ear_heard_journals_the_ear_that_actually_answered(both, tmp_path, monkeypatch):
    """The router used to log `ears.active()`, the ear that *would* answer, not
    the one that did; a fallen-back-to reading was misnamed. Journalled from
    inside `hear` itself, beside the ear that is actually answering."""
    path = tmp_path / "journal.jsonl"
    monkeypatch.setattr(get_settings(), "journal_path", str(path))
    monkeypatch.setattr(journal, "_built_from", None)
    asked = both(hosted_fails=ConnectionError("no internet"))

    assert ears.hear(SOUND, None, "") == "here heard it"
    assert asked == ["hosted", "here"]

    lines = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines() if row]
    heard = [row for row in lines if row["kind"] == "ear.heard"]
    assert len(heard) == 1
    assert heard[0]["ear"] == ears.named("here").name()
    assert heard[0]["ms"] >= 0
    assert heard[0]["chars"] == len("here heard it")


def test_when_no_ear_answers_the_last_failure_is_raised_not_swallowed(both):
    """Every recording coming back as "nothing heard" would read as the app
    working and the reader being unclear. It must fail, and say what failed."""
    asked = both(hosted_fails=ConnectionError("no internet"),
                 here_fails=RuntimeError("the model is not installed"))
    with pytest.raises(RuntimeError, match="not installed"):
        ears.hear(SOUND, None, "")
    assert asked == ["hosted", "here"]


def test_an_ear_that_hears_nothing_is_believed_rather_than_asked_again(both, monkeypatch):
    """A quiet room is an answer. Walking on to the next ear would spend three
    more seconds reaching the same silence, on every recording with a pause."""
    asked = both()
    monkeypatch.setattr(ears.named("hosted"), "transcribe",
                        lambda audio, language, hint: asked.append("hosted") or "")
    assert ears.hear(SOUND, None, "") == ""
    assert asked == ["hosted"]
