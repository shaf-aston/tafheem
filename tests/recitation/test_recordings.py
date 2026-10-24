import io
import json
import shutil
import subprocess
import wave

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.config import get_settings
from backend.main import create_app
from backend.services.recitation import recordings

# Tidying a take runs ffmpeg; a machine without it cannot check that part.
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")


def _take(seconds=0.5, quiet=0.6):
    """Quiet, a tone for the word, quiet: what a microphone hands over."""
    import numpy as np
    sr = 22050
    tone = 0.4 * np.sin(2 * np.pi * 220 * np.arange(int(sr * seconds)) / sr)
    pad = np.zeros(int(sr * quiet))
    out = io.BytesIO()
    with wave.open(out, "wb") as f:
        f.setframerate(sr); f.setsampwidth(2); f.setnchannels(1)
        f.writeframes((np.concatenate([pad, tone, pad]) * 32767).astype("<i2").tobytes())
    return out.getvalue()


def _seconds(mp3):
    pcm = subprocess.run(["ffmpeg", "-loglevel", "quiet", "-i", "-", "-f", "s16le", "-ac", "1", "-ar", "22050", "-"],
                         input=mp3, capture_output=True, check=False).stdout
    return len(pcm) / 2 / 22050


@pytest.fixture
def studio(monkeypatch, tmp_path):
    monkeypatch.setattr(recordings, "RECORDINGS", tmp_path)
    monkeypatch.setattr(get_settings(), "recorder_key", SecretStr("sesame"))
    return TestClient(create_app())


def test_the_studio_is_off_without_a_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "recorder_key", SecretStr(""))
    assert TestClient(create_app()).get("/api/recordings/todo").status_code == 404


def test_a_wrong_key_is_refused(studio):
    assert studio.get("/api/recordings/todo", headers={"X-Recorder-Key": "nope"}).status_code == 403


@needs_ffmpeg
def test_a_kept_take_is_trimmed_indexed_and_leaves_the_todo(studio):
    key = {"X-Recorder-Key": "sesame"}
    first = studio.get("/api/recordings/todo", params={"limit": 1}, headers=key).json()
    word = first["words"][0]["ar"]
    sent = studio.post("/api/recordings", data={"text": word}, files={"audio": ("w.wav", _take())}, headers=key)
    assert sent.status_code == 200
    name = sent.json()["file"]
    assert json.loads((recordings.RECORDINGS / "index.json").read_text(encoding="utf-8")) == {word: name}
    # 1.7s sent, 0.5s of it the word: the quiet goes (bar the 0.05s kept at each
    # edge so a soft first letter is not clipped), the phone's lead comes back.
    lead = get_settings().speech_lead_ms / 1000
    assert abs(_seconds((recordings.RECORDINGS / name).read_bytes()) - (0.5 + 2 * lead + 0.1)) < 0.1
    after = studio.get("/api/recordings/todo", params={"limit": 1}, headers=key).json()
    assert after["left"] == first["left"] - 1 and after["done"] == 1
    assert after["words"][0]["ar"] != word


@needs_ffmpeg
def test_what_is_not_sound_is_refused(studio):
    sent = studio.post("/api/recordings", data={"text": "كِتَاب"}, files={"audio": ("w.wav", b"hello")},
                       headers={"X-Recorder-Key": "sesame"})
    assert sent.status_code == 415
