"""GET /api/speak: only Arabic phrases reach the voice, and the same phrase costs one synthesis."""
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.config import get_settings
from backend.routers import speak as speak_route
from backend.services import speech


def client(monkeypatch, tmp_path):
    calls = []
    speak_route._asks.clear()
    monkeypatch.setattr(speech, "CACHE", tmp_path)
    monkeypatch.setattr(speech.FastPitchVoice, "say", lambda self, text: calls.append(text) or b"RIFF-fake")
    return TestClient(create_app()), calls


def test_rejects_what_is_not_short_arabic(monkeypatch, tmp_path):
    app, calls = client(monkeypatch, tmp_path)
    assert app.get("/api/speak", params={"text": ""}).status_code == 422
    assert app.get("/api/speak", params={"text": "hello"}).status_code == 422
    assert app.get("/api/speak", params={"text": "../../etc"}).status_code == 422
    assert app.get("/api/speak", params={"text": "ك" * (get_settings().speech_max_chars + 1)}).status_code == 413
    assert app.get("/api/speak", params={"text": "كيفك؟؟"}).status_code == 422
    assert calls == []


def test_same_word_twice_is_one_synthesis(monkeypatch, tmp_path):
    app, calls = client(monkeypatch, tmp_path)
    first = app.get("/api/speak", params={"text": "كِتَاب"})
    second = app.get("/api/speak", params={"text": "كِتَاب"})
    assert first.status_code == second.status_code == 200
    assert first.content == second.content
    assert first.headers["content-type"] == "audio/wav"
    assert calls == ["كِتَاب"]


def test_a_phrase_with_its_marks_is_said(monkeypatch, tmp_path):
    app, calls = client(monkeypatch, tmp_path)
    assert app.get("/api/speak", params={"text": " أنا  منيح ، الحمدلله. "}).status_code == 200
    assert app.get("/api/speak", params={"text": "أنا منيح، الحمدلله."}).status_code == 200
    assert calls == ["أنا منيح، الحمدلله."]  # spacing apart, one phrase: one synthesis


def test_a_failing_voice_rests_instead_of_retiring(monkeypatch, tmp_path):
    voice = speech._VOICES["fastpitch"]
    monkeypatch.setattr(voice, "_resting_until", 0.0)
    monkeypatch.setattr(voice, "retired_reason", "")
    monkeypatch.setattr(speech, "CACHE", tmp_path)

    def broken(self, text):
        raise OSError("offline")

    monkeypatch.setattr(speech.FastPitchVoice, "say", broken)
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


def test_a_long_phrase_counts_as_several_asks(monkeypatch, tmp_path):
    app, _ = client(monkeypatch, tmp_path)
    monkeypatch.setattr(get_settings(), "speech_per_minute", 3)
    monkeypatch.setattr(get_settings(), "speech_chars_per_ask", 10)
    ask = lambda text: app.get("/api/speak", params={"text": text}).status_code
    assert ask("ك" * 30) == 200  # three asks' worth
    assert ask("كتب") == 429


def test_the_store_keeps_only_the_newest_words(monkeypatch, tmp_path):
    app, _ = client(monkeypatch, tmp_path)
    monkeypatch.setattr(get_settings(), "speech_cache_max_mb", 2 * len(b"RIFF-fake") / 1_000_000)
    for word in ["كتب", "قلم", "باب"]:
        assert app.get("/api/speak", params={"text": word}).status_code == 200
    assert len(list(tmp_path.glob("*.wav"))) == 2


class _Model:
    """Stands in for FastPitch: a quarter second of quiet, as float samples."""

    heard = []

    def infer(self, text, speaker, pace):
        import numpy as np
        self.heard.append(text)
        self.pace = pace
        return np.zeros(22050 // 4, dtype="float32")


def test_the_voice_hands_back_a_playable_wav(monkeypatch):
    import io, wave
    voice, model = speech.FastPitchVoice(), _Model()
    monkeypatch.setattr(voice, "_model", model)
    with wave.open(io.BytesIO(voice.say("كِتَاب"))) as file:
        assert (file.getframerate(), file.getsampwidth(), file.getnchannels()) == (22050, 2, 1)
        assert file.getnframes() == 22050 // 4
    assert model.pace == get_settings().speech_fastpitch_pace  # the slower pace reaches the engine


def test_arabic_marks_reach_the_engine_as_pauses(monkeypatch):
    voice, model = speech.FastPitchVoice(), _Model()
    monkeypatch.setattr(voice, "_model", model)
    voice.say("كيفك؟ منيح، الحمدلله")
    assert model.heard[-1] == "كيفك ? منيح , الحمدلله"


def test_name_of_allah_is_spelt_out_wherever_it_falls():
    from backend.services.speech import name_spelt_out as said
    assert said("اللَّهُ أَكْبَر") == "اللَّهُ أَكْبَر"  # first word: the engine already knows it
    assert said("بِسْمِ اللَّهِ") == "بِسْمِ اللَّاهِ"
    assert said("الْحَمْدُ لِلَّهِ،") == "الْحَمْدُ لِلَّاهِ،"
    assert said("وَاللَّهِ") == "وَاللَّاهِ"
    assert said("والله") == "وَاللَّاه"
    assert said("ولله") == "وَلِلَّاه"
    assert said("سبحان الله؟") == "سبحان اللَّاه؟"
    assert said("ظلله اللهو") == "ظلله اللهو"  # look-alikes untouched
