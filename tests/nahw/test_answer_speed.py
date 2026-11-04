"""An answer says how long each step took (Server-Timing), and a sentence read lately is not
read again: the Analyse page and its practice questions ask for the same one back to back."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.nahw import iraab
from backend.utils import Timings
from tests.nahw_helpers import needs_parser

client = TestClient(app)
SENTENCE = "ذَهَبَ الطَّالِبُ إِلَى الْمَدْرَسَةِ"


def test_timings_name_each_step_in_the_header_shape():
    timings = Timings()
    with timings.step("analyze"):
        pass
    with timings.step("questions"):
        pass
    name_a, name_b = (part.split(";")[0] for part in timings.header().split(", "))
    assert (name_a, name_b) == ("analyze", "questions")
    assert all(part.split(";dur=")[1].replace(".", "").isdigit() for part in timings.header().split(", "))


def test_a_sentence_read_lately_is_answered_from_memory(monkeypatch):
    iraab._kept.cache_clear()
    reads = []
    monkeypatch.setattr(iraab, "_read", lambda sentence, recorded: reads.append(sentence) or {"words": [{"role": "x"}], "read_failed": False})
    first = iraab.analyze("كَتَبَ")
    first["words"][0]["role"] = "changed by a caller"
    second = iraab.analyze("كَتَبَ")
    iraab._kept.cache_clear()
    assert reads == ["كَتَبَ"]
    assert second["words"][0]["role"] == "x"  # each caller gets its own copy


@needs_parser
def test_practice_and_analyze_say_their_timings():
    for path in ("/api/analyze", "/api/practice"):
        response = client.post(path, json={"sentence": SENTENCE})
        assert response.status_code == 200
        assert "analyze;dur=" in response.headers["server-timing"]
    assert "questions;dur=" in response.headers["server-timing"]
