"""GET /api/speak: only Arabic phrases reach the voice, and the same phrase costs one synthesis."""
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.config import get_settings
from backend.routers import speak as speak_route
from backend.services import speech


def client(monkeypatch, tmp_path):
    calls = []
    speak_route._limit.asks.clear()
    monkeypatch.setattr(speech, "CACHE", tmp_path)
    monkeypatch.setattr(speech, "_stored", None)
    monkeypatch.setattr(speech.FastPitchVoice, "say", lambda self, text, speed=1.0: calls.append(text) or b"RIFF-fake")
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

    def broken(self, text, speed=1.0):
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

    def slow(self, text, speed=1.0):
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
    monkeypatch.setattr(speech.FastPitchVoice, "say", lambda self, text, speed=1.0: time.sleep(0.1) or made.append(text) or b"RIFF-fake")
    readied = threading.Thread(target=speech.say, args=("كتاب", False))
    readied.start()
    time.sleep(0.03)
    assert speech.say("كتاب") == b"RIFF-fake"
    readied.join()
    assert made == ["كتاب"]


def test_the_page_marks_a_word_made_ahead(monkeypatch, tmp_path):
    app, _ = client(monkeypatch, tmp_path)
    heard = []
    monkeypatch.setattr(speech, "say", lambda text, pressed=True, first=None, speed=1.0: heard.append(pressed) or b"RIFF-fake")
    app.get("/api/speak", params={"text": "كتب"}, headers={"x-speak-ahead": "1"})
    app.get("/api/speak", params={"text": "كتب"})
    assert heard == [False, True]


def test_premade_lines_cover_the_quiz_too():
    from backend.scripts.premake_speech import WORDS, said, spoken_sentence
    import json
    todo = {text for text, voice in said() if voice is None}
    sentences = json.loads((WORDS / "sentences.json").read_text(encoding="utf-8"))["sentences"]
    arabic = next(iter(sentences.values()))[0]
    assert speech.tidy(spoken_sentence(arabic)) in todo
    recorded = json.loads((WORDS / "word_audio.json").read_text(encoding="utf-8"))
    words = json.loads((WORDS / "words.json").read_text(encoding="utf-8"))["words"]
    assert next(w["ar"] for w in words if w["ar"] not in recorded) in todo
    assert not todo & set(recorded)  # a reciter says those
    assert ("كِيفَك؟", "edge:ar-SY-LaithNeural") in said()  # a dialect's line, by its own speaker


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
        # The word, with the quiet a phone's speaker needs to wake on each side.
        assert file.getnframes() == 22050 // 4 + 2 * (22050 * get_settings().speech_lead_ms // 1000)
    assert model.pace == speech.PACE


def test_slow_reaches_the_engine_and_is_kept_apart(monkeypatch, tmp_path):
    model = _Model()
    monkeypatch.setattr(speech, "CACHE", tmp_path)
    monkeypatch.setattr(speech, "_stored", None)
    monkeypatch.setattr(speech._VOICES["fastpitch"], "_model", model)
    slow = speech.SPEEDS["slow"]
    client = TestClient(create_app())
    assert client.get("/api/speak", params={"text": "قَطَاة", "speed": "slow"}).status_code == 200
    assert model.pace == speech.PACE * slow
    voice = speech._VOICES["fastpitch"]
    assert speech.stored(voice, "قَطَاة", slow) != speech.stored(voice, "قَطَاة")
    # A speed the config does not name is refused, so no file is made per decimal place.
    assert client.get("/api/speak", params={"text": "قَطَاة", "speed": "0.123"}).status_code == 422


def test_edge_rate_is_the_shared_pace():
    assert speech.edge_rate(0.9) == "-10%"
    assert speech.edge_rate(0.63) == "-37%"
    assert speech.edge_rate(1.0) == "+0%"


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


def test_a_dialect_is_said_by_its_own_speaker_first(monkeypatch, tmp_path):
    app, calls = client(monkeypatch, tmp_path)
    heard = []
    monkeypatch.setattr(speech.EdgeVoice, "say", lambda self, text, speed=1.0: heard.append((self.speaker, text)) or b"ID3-fake")
    reply = app.get("/api/speak", params={"text": "كيفك", "accent": "damascene"})
    assert reply.status_code == 200
    assert reply.headers["content-type"] == "audio/mpeg"
    assert heard == [("ar-SY-LaithNeural", "كيفك")] and calls == []
    assert app.get("/api/speak", params={"text": "كيفك", "accent": "fusha"}).status_code == 200
    assert calls == ["كيفك"]  # a dialect with no speaker of its own keeps the Fusha voice
    assert app.get("/api/speak", params={"text": "كيفك", "accent": "martian"}).status_code == 422


def test_a_dialect_speaker_out_of_reach_falls_back_to_the_fusha_voice(monkeypatch, tmp_path):
    app, calls = client(monkeypatch, tmp_path)

    def offline(self, text, speed=1.0):
        raise OSError("offline")

    monkeypatch.setattr(speech.EdgeVoice, "say", offline)
    voice = speech.voice_named("edge:ar-EG-ShakirNeural")
    monkeypatch.setattr(voice, "_resting_until", 0.0)
    assert app.get("/api/speak", params={"text": "إزيك", "accent": "egyptian"}).status_code == 200
    assert calls == ["إزيك"] and voice.resting()


def test_every_dialect_voice_named_in_the_data_is_a_voice():
    from backend.services.colloquial import loader

    for dialect in loader.catalogue()["dialects"]:
        name = loader.voice_of(dialect["key"])
        assert name is None or speech.voice_named(name).name


def test_a_made_word_is_evened_out_and_soft_at_both_ends():
    import numpy as np

    settings = get_settings()
    lead = speech.RATE * settings.speech_lead_ms // 1000
    quiet = np.full(speech.RATE // 10, 0.2, dtype=np.float32)
    out = speech.shaped(quiet.copy())
    word = out[lead:len(out) - lead]
    assert len(out) == len(quiet) + 2 * lead and not out[:lead].any()
    assert abs(np.abs(word).max() - settings.speech_peak) < 1e-6
    assert word[0] == 0 and word[-1] == 0
