"""A few huge or piled-up uploads must not keep the CPU busy: a full queue is refused 503 and a recording
past listen_max_seconds 413, both before any model runs."""
import numpy as np
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.main import app
from backend.routers import listen as listen_router
from backend.services import recitation
from backend.services.recitation import loudness, whisper

client = TestClient(app)
WEBM = bytes([0x1A, 0x45, 0xDF, 0xA3]) + bytes(8)


def _model_must_not_run(*a, **k):
    raise AssertionError("the model ran")


def test_a_full_queue_is_503_and_runs_no_model(monkeypatch):
    monkeypatch.setattr(listen_router, "_waiting", get_settings().listen_queue_max)
    monkeypatch.setattr(recitation, "would_answer_locally", lambda *a, **k: True)
    monkeypatch.setattr(recitation, "hear", _model_must_not_run)
    monkeypatch.setattr(recitation, "check", _model_must_not_run)
    heard = client.post("/api/listen?recite=true", files={"audio": ("r.webm", WEBM)})
    checked = client.post("/api/listen/check", params={"heard": "قل", "check": "112:1"}, files={"audio": ("r.webm", WEBM)})
    assert (heard.status_code, checked.status_code) == (503, 503)
    assert heard.json()["detail"] == "Busy, try again in a moment."


def test_a_recording_past_the_cap_is_413_before_the_model(monkeypatch):
    import faster_whisper.audio
    longer = get_settings().listen_max_seconds + 1
    monkeypatch.setattr(faster_whisper.audio, "decode_audio", lambda *a, **k: np.zeros(int(longer * loudness.SAMPLE_RATE), dtype=np.float32))
    monkeypatch.setattr(whisper, "_last", None)
    monkeypatch.setattr(whisper, "engine", _model_must_not_run)
    resp = client.post("/api/listen", files={"audio": ("r.webm", WEBM)})
    assert resp.status_code == 413
