"""GET /api/speak: only short Arabic reaches the voice, and the same word costs one synthesis."""
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.config import get_settings
from backend.routers import speak as speak_route
from backend.services import speech


def client(monkeypatch, tmp_path):
    calls = []
    speak_route._asks.clear()
    monkeypatch.setattr(speech, "CACHE", tmp_path)
    monkeypatch.setattr(speech.PiperVoice, "say", lambda self, text: calls.append(text) or b"RIFF-fake")
    return TestClient(create_app()), calls


def test_rejects_what_is_not_short_arabic(monkeypatch, tmp_path):
    app, calls = client(monkeypatch, tmp_path)
    assert app.get("/api/speak", params={"text": ""}).status_code == 422
    assert app.get("/api/speak", params={"text": "hello"}).status_code == 422
    assert app.get("/api/speak", params={"text": "../../etc"}).status_code == 422
    assert app.get("/api/speak", params={"text": "كتاب" * 20}).status_code == 413
    assert calls == []


def test_same_word_twice_is_one_synthesis(monkeypatch, tmp_path):
    app, calls = client(monkeypatch, tmp_path)
    first = app.get("/api/speak", params={"text": "كِتَاب"})
    second = app.get("/api/speak", params={"text": "كِتَاب"})
    assert first.status_code == second.status_code == 200
    assert first.content == second.content
    assert first.headers["content-type"] == "audio/wav"
    assert calls == ["كِتَاب"]


def test_a_failing_voice_rests_instead_of_retiring(monkeypatch, tmp_path):
    voice = speech._VOICES["piper"]
    monkeypatch.setattr(voice, "_resting_until", 0.0)
    monkeypatch.setattr(voice, "retired_reason", "")
    monkeypatch.setattr(speech, "CACHE", tmp_path)

    def broken(self, text):
        raise OSError("offline")

    monkeypatch.setattr(speech.PiperVoice, "say", broken)
    app = TestClient(create_app())
    assert app.get("/api/speak", params={"text": "كِتَاب"}).status_code == 503
    assert voice.resting() and not voice.retired_reason
    assert list(tmp_path.iterdir()) == []  # nothing half-written left behind


def test_one_visitor_is_slowed_after_the_limit(monkeypatch, tmp_path):
    app, _ = client(monkeypatch, tmp_path)
    monkeypatch.setattr(get_settings(), "speech_per_minute", 2)
    ask = lambda who: app.get("/api/speak", params={"text": "كتب"}, headers={"x-forwarded-for": who}).status_code
    assert [ask("1.1.1.1"), ask("1.1.1.1"), ask("1.1.1.1")] == [200, 200, 429]
    assert ask("2.2.2.2") == 200  # someone else is not held up


def test_the_store_keeps_only_the_newest_words(monkeypatch, tmp_path):
    app, _ = client(monkeypatch, tmp_path)
    monkeypatch.setattr(get_settings(), "speech_cache_max_files", 2)
    for word in ["كتب", "قلم", "باب"]:
        assert app.get("/api/speak", params={"text": word}).status_code == 200
    assert len(list(tmp_path.glob("*.wav"))) == 2


class _Model:
    """Stands in for Piper's phonemizer: ظ as ð (its fault), ض as d ˤ."""

    def phonemize(self, text):
        sounds = {"ظ": ["ð"], "ض": ["d", "ˤ"], "ذ": ["ð"]}
        return [[p for ch in text for p in sounds.get(ch, [ch])]]


def test_zaa_is_not_said_as_dhaal():
    assert speech._phonemes(_Model(), "ظل") == [["ð", "ˤ", "ل"]]
    assert speech._phonemes(_Model(), "ذل") == [["ð", "ل"]]
    # A real ض beside it would be changed too, so that text is left alone.
    assert speech._phonemes(_Model(), "ظض") == [["ð", "d", "ˤ"]]
