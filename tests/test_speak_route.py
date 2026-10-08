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
    monkeypatch.setattr(speech, "_stored", None)
    monkeypatch.setattr(speech.FastPitchVoice, "say", lambda self, text: calls.append(text) or b"RIFF-fake")
    return TestClient(create_app()), calls


def test_rejects_what_is_not_short_arabic(monkeypatch, tmp_path):
    app, calls = client(monkeypatch, tmp_path)
    assert app.get("/api/speak", params={"text": ""}).status_code == 422
    assert app.get("/api/speak", params={"text": "hello"}).status_code == 422
    assert app.get("/api/speak", params={"text": "../../etc"}).status_code == 422
    assert app.get("/api/speak", params={"text": "ك" * (get_settings().speech_max_chars + 1)}).status_code == 413
    assert app.get("/api/speak", params={"text": "كيفك؟ x"}).status_code == 422
    assert calls == []
    assert app.get("/api/speak", params={"text": "كيفك؟؟"}).status_code == 200  # a run of marks is its last
    assert calls == ["كيفك؟"]


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


def test_the_store_is_counted_once_not_on_every_word(monkeypatch, tmp_path):
    app, _ = client(monkeypatch, tmp_path)
    counted = []
    real_glob = type(tmp_path).glob
    monkeypatch.setattr(type(tmp_path), "glob", lambda self, pattern: counted.append(pattern) or real_glob(self, pattern))
    for word in ["كتب", "قلم", "باب"]:
        assert app.get("/api/speak", params={"text": word}).status_code == 200
    assert len(counted) == 1


def test_a_pressed_word_goes_before_words_made_ahead(monkeypatch, tmp_path):
    import threading, time
    monkeypatch.setattr(speech, "CACHE", tmp_path)
    monkeypatch.setattr(speech, "_stored", None)
    order, first_started = [], threading.Event()

    def slow(self, text):
        first_started.set()
        time.sleep(0.15)
        order.append(text)
        return b"RIFF-fake"

    monkeypatch.setattr(speech.FastPitchVoice, "say", slow)
    ahead = [threading.Thread(target=speech.say, args=(word, False)) for word in ["أ", "ب", "ت"]]
    ahead[0].start()
    first_started.wait()  # the engine is busy with the first word made ahead
    for t in ahead[1:]:
        t.start()
    time.sleep(0.05)  # both are waiting their turn
    pressed = threading.Thread(target=speech.say, args=("ث",))
    pressed.start()
    for t in [*ahead, pressed]:
        t.join()
    assert order[:2] == ["أ", "ث"]  # the press waits only for the word already being made


def test_a_word_readied_then_pressed_is_made_once(monkeypatch, tmp_path):
    import threading, time
    monkeypatch.setattr(speech, "CACHE", tmp_path)
    monkeypatch.setattr(speech, "_stored", None)
    made = []
    monkeypatch.setattr(speech.FastPitchVoice, "say", lambda self, text: time.sleep(0.1) or made.append(text) or b"RIFF-fake")
    readied = threading.Thread(target=speech.say, args=("كتاب", False))
    readied.start()
    time.sleep(0.03)
    assert speech.say("كتاب") == b"RIFF-fake"
    readied.join()
    assert made == ["كتاب"]


def test_the_page_marks_a_word_made_ahead(monkeypatch, tmp_path):
    app, _ = client(monkeypatch, tmp_path)
    heard = []
    monkeypatch.setattr(speech, "say", lambda text, pressed=True: heard.append(pressed) or b"RIFF-fake")
    app.get("/api/speak", params={"text": "كتب"}, headers={"x-speak-ahead": "1"})
    app.get("/api/speak", params={"text": "كتب"})
    assert heard == [False, True]


def test_premade_lines_cover_the_quiz_too():
    from backend.scripts.premake_speech import WORDS, lines, spoken_sentence
    import json
    todo = set(lines())
    sentences = json.loads((WORDS / "sentences.json").read_text(encoding="utf-8"))["sentences"]
    arabic = next(iter(sentences.values()))[0]
    assert speech.tidy(spoken_sentence(arabic)) in todo
    recorded = json.loads((WORDS / "word_audio.json").read_text(encoding="utf-8"))
    words = json.loads((WORDS / "words.json").read_text(encoding="utf-8"))["words"]
    assert next(w["ar"] for w in words if w["ar"] not in recorded) in todo
    assert not todo & set(recorded)  # a reciter says those


def test_what_is_only_written_is_not_said():
    assert speech.tidy("(بعد شوية) هذا مضبوط عليّ.") == "هذا مضبوط عليّ."  # a stage note
    assert speech.tidy("آسِف / آسِفَة") == speech.tidy("آسِف|آسِفَة") == "آسِف، آسِفَة"  # both forms
    assert speech.tidy("سِتَّةُ أَفْرَاد: أَبِي") == "سِتَّةُ أَفْرَاد، أَبِي"
    assert speech.tidy("لَقَبُهُ \"الْبَطَلُ\".") == "لَقَبُهُ الْبَطَلُ."
    assert speech.tidy("بِتَوَصِّلْنِي عـِ...؟") == "بِتَوَصِّلْنِي عِ؟"


def test_every_line_the_app_speaks_is_one_the_voice_takes():
    from backend.routers.speak import ARABIC
    from backend.scripts.premake_speech import lines
    assert [text for text in lines() if not ARABIC.fullmatch(text)] == []


def test_letters_the_engine_lacks_become_the_nearest_it_has(monkeypatch):
    voice, model = speech.FastPitchVoice(), _Model()
    monkeypatch.setattr(voice, "_model", model)
    voice.say("گال چبير")
    assert model.heard[-1] == "كال تشبير"
    voice.say("هٰذَا الرَّحْمَٰنُ")
    assert model.heard[-1] == "هَاذَا الرَّحْمَانُ"


def test_dialect_letters_reach_the_voice(monkeypatch, tmp_path):
    app, calls = client(monkeypatch, tmp_path)
    assert app.get("/api/speak", params={"text": "هذا چبير"}).status_code == 200
    assert calls == ["هذا چبير"]


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
