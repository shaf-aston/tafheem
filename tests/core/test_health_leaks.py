"""The public /api/health says that a loader failed, never why: the why holds paths and library text."""
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.services import speech
from backend.services.nahw.syntax import catib_onnx

SECRET = "C:/secret/models/encoder.onnx"


def test_health_shows_no_exception_text_when_loaders_failed(monkeypatch):
    monkeypatch.setattr(catib_onnx, "_parser", None)
    monkeypatch.setattr(catib_onnx, "_load_error", f"OSError: cannot open {SECRET}")
    monkeypatch.setattr(catib_onnx, "files_present", lambda: True)
    voice = speech.order()[0]
    monkeypatch.setattr(voice, "retired_reason", f"no module at {SECRET}")
    for other in speech.order()[1:]:
        monkeypatch.setattr(other, "retired_reason", f"no module at {SECRET}")
    text = TestClient(create_app()).get("/api/health").text
    assert SECRET not in text and "secret" not in text
    assert '"parser":"failed"' in text.replace(" ", "")
