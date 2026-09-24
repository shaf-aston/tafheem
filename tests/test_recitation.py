"""Finding the ayah somebody recited, without needing a microphone.

The listening half is a model on this machine and is not tested here; what is
tested is everything after it, which is where the app can be wrong in ways a
reader would notice. The strings below are not invented: they are what
faster-whisper actually returned when fed recitation of these ayahs, errors and
all, so a change that breaks real recitation breaks these.

Three of these cases were failures before they were tests:

  "قل هو الله"                  the right ayah never reached the scorer, because
                                hundreds of ayahs tie on a short phrase and the
                                shortlist was taking whichever forty came first.
  "الحمد لله رب العالمين"       lost to 6:45, which really does end with those
                                same words, until how much of the ayah was
                                recited began to count.
  part of Ayat al-Kursi         lost to the much shorter 20:8, which shares its
                                opening, until the score stopped marking an ayah
                                down for words the reciter had not reached yet.

Run: python -m pytest tests/test_recitation.py
"""
from __future__ import annotations

import numpy as np
import pytest

from backend.config import get_settings
from backend.services import quran_corpus
from backend.services.recitation import listen, match


@pytest.fixture(autouse=True)
def sound(monkeypatch):
    """Stand in for turning a file into sound.

    The recordings in this file are a few bytes of prose, not audio, because
    what is being tested is the rules above the engine and never the engine.
    Decoding is real work with its own test (an unreadable recording is refused,
    below), so here it is stood in for rather than fed something it cannot read.
    """
    import faster_whisper.audio

    handed = []
    monkeypatch.setattr(
        faster_whisper.audio, "decode_audio",
        lambda path: handed.append(path) or np.zeros(16000, dtype=np.float32),
    )
    # Stood in at the engine's own door rather than at ours, so the temporary
    # file a recording is written to is still really written and really
    # deleted, and a test can still prove none is left on the disk.
    listen._last = None
    yield handed
    listen._last = None



def segment(text, no_speech=0.0, sure=1.0):
    """One stretch as the engine returns it: its words, each with its sureness."""
    words = [type("Word", (), {"word": f" {w}", "probability": sure})() for w in text.split()]
    return type("Seg", (), {"text": f" {text} ", "no_speech_prob": no_speech, "words": words})()

needs_corpus = pytest.mark.skipif(
    not quran_corpus.is_loaded(),
    reason="corpus.db not built, run backend/scripts/build_quran_corpus.py",
)


@pytest.fixture(scope="module")
def quran():
    return match.prepare(
        (surah, ayah, text)
        for surah in range(1, 115)
        for ayah, text in quran_corpus.ayah_texts(surah)
    )


def first(quran, heard):
    hits = match.best(heard, quran)
    assert hits, f"nothing matched {heard!r}"
    return hits[0].surah, hits[0].ayah


# (what was heard, which ayahs would be a right answer, why this case exists)
REAL = [
    ("قل هو الله أحد", {(112, 1)}, "heard exactly"),
    ("ذلك الكتاب لا ريب فيه هدى للمتقين", {(2, 2)}, "heard exactly"),
    ("قل هو الله", {(112, 1)}, "a phrase hundreds of ayahs share"),
    ("الحمد لله رب العالمين", {(1, 2)}, "6:45 ends with these same words"),
    (
        "5 إذ أول فتية إلى الكهف فقالوا ربنا آتنا من لد كرحمة وهيئ لنا من أمرنا رشدا",
        {(18, 10)},
        "two words misheard and a number written in",
    ),
    (
        "17. الله لا إله إلا هو الحي القيوم 18. لا تأخذه سنة ولا نوم 19. لهما في السماوات",
        {(2, 255)},
        "part of the longest ayah, with Whisper's numbering",
    ),
    ("فإن مع العسر يسرا", {(94, 5), (94, 6)}, "the next ayah repeats it word for word"),
    (
        "ولقد يسرنا القرآن للذكر فهل من مدكر",
        {(54, 17), (54, 22), (54, 32), (54, 40)},
        "occurs four times in one surah",
    ),
    ("بسم الله الرحمن الرحيم", {(1, 1), (27, 30)}, "occurs twice as an ayah"),
]


@needs_corpus
@pytest.mark.parametrize("heard,allowed,why", REAL, ids=[case[2] for case in REAL])
def test_the_right_ayah_comes_first(quran, heard, allowed, why):
    assert first(quran, heard) in allowed


@needs_corpus
def test_the_whole_ayah_beats_one_that_merely_ends_the_same_way(quran):
    """1:2 and 6:45 both contain الحمد لله رب العالمين; only one of them is it."""
    hits = match.best("الحمد لله رب العالمين", quran)
    assert (hits[0].surah, hits[0].ayah) == (1, 2)
    assert hits[0].score > next(h.score for h in hits if (h.surah, h.ayah) == (6, 45))


@needs_corpus
def test_reciting_part_of_an_ayah_says_it_was_part(quran):
    """The score must not hide that only a fragment was matched."""
    part = match.best("الله لا إله إلا هو الحي القيوم لا تأخذه سنة ولا نوم", quran)[0]
    whole = match.best(
        "الله لا إله إلا هو الحي القيوم لا تأخذه سنة ولا نوم له ما في السماوات وما في "
        "الأرض من ذا الذي يشفع عنده إلا بإذنه يعلم ما بين أيديهم وما خلفهم",
        quran,
    )[0]
    assert (part.surah, part.ayah) == (whole.surah, whole.ayah) == (2, 255)
    assert part.heard_of_ayah < whole.heard_of_ayah, "reciting more must show as more"


@needs_corpus
def test_silence_and_noise_match_nothing(quran):
    """A mic that picked up a room is an ordinary event, not an error."""
    for nothing in ("", "   ", "...", "hello there", "12345"):
        assert match.best(nothing, quran) == []


@needs_corpus
def test_never_more_than_asked_for(quran):
    assert len(match.best("قل هو الله أحد", quran, limit=3)) == 3


def test_the_quran_s_spelling_and_a_plain_one_meet_somewhere():
    """The corpus writes ذَٰلِكَ ٱلْكِتَٰبُ; anybody transcribing writes ذلك الكتاب.

    No single folding turns one into the other, and that is not a gap to be
    patched: the small alef must be dropped for ذَٰلِكَ and written out for
    ٱلْكِتَٰبُ, and both words are in that one phrase. So both spellings are kept,
    and each word matches under one of them.
    """
    plain, written = match.spellings("ذَٰلِكَ ٱلْكِتَٰبُ")
    assert "ذلك" in plain
    assert "الكتاب" in written


def test_whisper_s_numbering_is_not_part_of_the_words():
    """Long recitations come back as "17. الله لا إله إلا هو"."""
    assert match.folded("17. الله لا إله") == match.folded("الله لا إله")


class FakeEngine:
    """Stands in for the model, and remembers exactly how it was asked."""

    def __init__(self):
        self.asked = None
        self.reads = 0

    def transcribe(self, path, **how):
        self.reads += 1
        self.asked = {"path": path, **how}
        return [segment("قل هو الله أحد")], None


@pytest.fixture
def engine(monkeypatch):
    fake = FakeEngine()
    monkeypatch.setattr(listen, "_engine", lambda name: fake)
    return fake


def test_the_settings_that_make_it_quick_reach_the_engine(engine):
    """The whole speed change is these four, and nothing else guards them.

    Each was measured, not guessed: one reading rather than five, silence cut
    rather than transcribed, no word timing because no word floor is set (it
    halved the wait and placed better), and every stretch of sound read on its
    own so the model does not finish the ayah for you.
    """
    listen.transcribe(b"pretend this is a recording", language="ar")
    asked = engine.asked
    assert asked["beam_size"] == 1
    assert asked["repetition_penalty"] > 1, "a cut word sent the model looping"
    assert asked["vad_filter"] is True
    assert asked["word_timestamps"] is False
    assert asked["condition_on_previous_text"] is False
    assert asked["language"] == "ar"


def test_a_word_floor_is_what_turns_word_timing_on(engine, monkeypatch):
    """Timing costs about half the wait, so it is asked for only if it is used."""
    monkeypatch.setattr(get_settings(), "recitation_word_min", 0.94)
    listen.transcribe(b"pretend this is a recording", language="ar")
    assert engine.asked["word_timestamps"] is True


class SilenceEater:
    """A model whose silence trimmer eats a short recording whole.

    Not invented: a real 0.9 second search was logged as 0.9 seconds removed,
    and the reader was told nothing was heard.
    """

    def __init__(self):
        self.reads = []

    def transcribe(self, path, **how):
        self.reads.append(how["vad_filter"])
        if how["vad_filter"]:
            return [], None
        return [segment("تحاول")], None


def test_a_word_the_silence_trimmer_ate_is_read_again_without_it(monkeypatch):
    fake = SilenceEater()
    monkeypatch.setattr(listen, "_engine", lambda name: fake)
    assert listen.transcribe(b"one word, said quickly", language="ar") == "تحاول"
    assert fake.reads == [True, False], "trimmed first, untrimmed only on failure"


class RoomFiller:
    """A model that writes a word over silence, as the real one does.

    Not invented: three seconds of nothing, read untrimmed after the trimmer
    had rightly removed all of it, came back as وَالْمُؤْمِنِينَ and matched
    an ayah. The model's own no-speech estimate was 0.25; on speech it is 0.00.
    """

    def transcribe(self, path, **how):
        if how["vad_filter"]:
            return [], None
        return [segment("والمؤمنين", no_speech=0.25)], None


def test_silence_the_model_fills_in_is_still_silence(monkeypatch):
    monkeypatch.setattr(listen, "_engine", lambda name: RoomFiller())
    assert listen.transcribe(b"a quiet room", language="ar") == ""


class Mumbler:
    """A model that hears a mumbled word as the nearest real one, unsurely.

    Measured: نعبد with its middle muffled came back as نَعْمَلُ at 0.91,
    beside clean words at 1.00.
    """

    def transcribe(self, path, **how):
        stretch = segment("إياك نعمل وإياك نستعين")
        stretch.words[1].probability = 0.91
        return [stretch], None


def test_a_word_the_model_is_unsure_of_is_still_written_down(monkeypatch):
    """The transcript only says which part of the page this is, and a run of
    words is what finds it, so a doubted word is kept rather than thrown away."""
    monkeypatch.setattr(listen, "_engine", lambda name: Mumbler())
    assert listen.transcribe(b"a mumble", language="ar") == "إياك نعمل وإياك نستعين"


def test_a_word_floor_drops_the_word_the_model_doubted(monkeypatch):
    monkeypatch.setattr(get_settings(), "recitation_word_min", 0.94)
    monkeypatch.setattr(listen, "_engine", lambda name: Mumbler())
    assert listen.transcribe(b"a mumble", language="ar") == "إياك وإياك نستعين"


def test_the_general_model_is_trusted_about_silence(monkeypatch):
    """Dictation: base rates real speech up to 0.13 not-speech and returns
    nothing on silence by itself, so the Qur'an ear's floor must not touch it.
    Rated above that floor here, so the test fails if the floor were applied."""
    fake = Named(sure=1.0)
    monkeypatch.setattr(listen, "_engine", fake)
    monkeypatch.setattr(get_settings(), "dictation_languages", "en")
    fake.no_speech = get_settings().recitation_no_speech_max + 0.05
    assert listen.transcribe(b"a search") == "mercy"


class Named:
    """Remembers which model each read asked for, and answers with a sureness."""

    def __init__(self, sure):
        self.sure = sure
        self.no_speech = 0.0
        self.models = []

    def __call__(self, name):
        self.models.append(name)
        return self

    def transcribe(self, path, **how):
        self.how = how
        return [segment("mercy", no_speech=self.no_speech, sure=self.sure)], None


def test_a_named_language_is_a_recitation_on_the_quran_model(monkeypatch):
    """Reciting: the Qur'an model, and no register hint."""
    fake = Named(sure=0.5)
    monkeypatch.setattr(listen, "_engine", fake)
    assert listen.transcribe(b"reciting", language="ar", hint="fusha") == "mercy"
    assert set(fake.models) == {get_settings().recitation_model}
    assert fake.how["initial_prompt"] is None


def test_no_language_named_is_dictation_on_the_general_model(monkeypatch):
    """A search box: the general model, the hint, and an unsure word kept.

    Base hears "mercy" right at 0.33 sure, so doubt cannot be a reason to drop
    it here, and the Qur'an model hears it as مَسْكُوبُ. No word timing is
    asked for either: it costs a second and invents words on a quiet tail.
    """
    fake = Named(sure=0.33)
    monkeypatch.setattr(listen, "_engine", fake)
    monkeypatch.setattr(get_settings(), "dictation_languages", "en")
    assert listen.transcribe(b"a search", hint="fusha") == "mercy"
    assert fake.models == [get_settings().dictation_model]
    assert fake.how["initial_prompt"] == "fusha"
    assert fake.how["word_timestamps"] is False


def test_a_recording_that_worked_is_only_read_once(engine):
    """The second read is for the failure, not for every recitation."""
    assert listen.transcribe(b"pretend this is a recording", language="ar")
    assert engine.reads == 1
    assert engine.asked["vad_filter"] is True


def test_the_recording_is_gone_once_the_answer_is_given(engine, sound):
    """A microphone's output must not be left lying on the disk."""
    from pathlib import Path

    assert listen.transcribe(b"pretend this is a recording", language="ar") == "قل هو الله أحد"
    assert sound and not any(Path(path).exists() for path in sound)


def test_nothing_recorded_is_never_sent_to_the_engine(engine):
    assert listen.transcribe(b"", language="ar") == ""
    assert engine.asked is None


def test_warming_up_a_machine_that_cannot_listen_is_not_an_error(monkeypatch):
    """No engine installed is an ordinary machine, not a broken startup."""
    def refuse(name):
        raise listen.NotInstalled("faster-whisper is not installed")

    monkeypatch.setattr(listen, "_engine", refuse)
    listen.warm()  # must not raise


class Bilingual(FakeEngine):
    """A model that also says how likely each language is, as detection does."""

    def __init__(self, chances):
        super().__init__()
        self.chances = chances
        self.detections = 0

    def detect_language(self, audio):
        self.detections += 1
        best = max(self.chances.items(), key=lambda pair: pair[1])
        return best[0], best[1], list(self.chances.items())


@pytest.fixture
def bilingual(monkeypatch):
    """A fake model plus a decoder, so no real sound file is needed.

    Real sound, not a stand-in string: what comes back from decoding is
    levelled before anything hears it, and levelling is arithmetic on samples.
    """
    monkeypatch.setattr("faster_whisper.audio.decode_audio",
                        lambda path: np.zeros(16000, dtype=np.float32))

    def install(chances):
        fake = Bilingual(chances)
        monkeypatch.setattr(listen, "_engine", lambda name: fake)
        return fake

    return install


def test_an_english_word_is_heard_as_english(bilingual):
    """The defect this exists for: "knowledge" pinned to Arabic came back نالج."""
    fake = bilingual({"en": 0.91, "ar": 0.04})
    listen.transcribe(b"knowledge, said out loud")
    assert fake.asked["language"] == "en"


def test_an_arabic_word_is_still_heard_as_arabic(bilingual):
    fake = bilingual({"ar": 0.88, "en": 0.05})
    listen.transcribe(b"an Arabic word, said out loud")
    assert fake.asked["language"] == "ar"


def test_a_language_that_is_not_offered_never_wins(bilingual):
    """The nearest case nobody asks for: one English word read as Urdu.

    Left free the model does exactly this, and the word comes back in Urdu
    letters. Only the offered languages may be chosen between.
    """
    fake = bilingual({"ur": 0.72, "fa": 0.19, "en": 0.06, "ar": 0.02})
    listen.transcribe(b"one word, ambiguous")
    assert fake.asked["language"] == "en"


def test_naming_the_language_spends_nothing_on_choosing_it(bilingual):
    """A recitation is Arabic and known to be, so it pays for no detection."""
    fake = bilingual({"en": 0.91, "ar": 0.04})
    listen.transcribe(b"pretend this is a recitation", language="ar")
    assert fake.asked["language"] == "ar"
    assert fake.detections == 0


def test_one_dictation_language_is_nothing_to_choose_between(bilingual, monkeypatch):
    """Pinning the setting back to one language must also stop the extra pass."""
    from backend.config import get_settings

    monkeypatch.setattr(get_settings(), "dictation_languages", "ar")
    fake = bilingual({"en": 0.91, "ar": 0.04})
    listen.transcribe(b"pretend this is a recording")
    assert fake.asked["language"] == "ar"
    assert fake.detections == 0


def test_startup_freezes_the_loaded_dictionaries_from_the_collector(monkeypatch):
    """decode_audio's per-recording gc.collect() must not sweep the app's own data.

    Not the model, which needs no proving here: recitation_warm is turned off
    so the test costs nothing beyond the real dictionary loaders main.py always
    runs at startup.
    """
    import gc

    from fastapi.testclient import TestClient

    from backend.config import get_settings
    from backend.main import app

    monkeypatch.setattr(get_settings(), "recitation_warm", False)
    before = gc.get_freeze_count()
    with TestClient(app):
        pass
    assert gc.get_freeze_count() > before


def test_letter_report_blames_the_ear_for_swaps_and_drops_only():
    """The counting behind letters-report.txt, on a pair with a known answer.

    Two things it would be easy to get wrong and never notice in a table of
    thirty rows: a run that changed length has no one-to-one pairing, so it
    must not invent letter-for-letter swaps; and a byte-written vocabulary
    must be read back into Arabic before being searched for Arabic.
    """
    from collections import Counter

    from backend.scripts.letters_missed import _as_arabic, compare

    swaps, seen, dropped, added = Counter(), Counter(), Counter(), Counter()
    # Said "دار", heard "تار": one letter swapped, nothing else.
    compare("دار", "تار", swaps, seen, dropped, added)
    assert swaps[("د", "ت")] == 1
    assert seen["د"] == 1 and not dropped and not added

    # Said "قلب", heard "قب": the lam is gone, and no swap is invented for it.
    compare("قلب", "قب", swaps, seen, dropped, added)
    assert dropped["ل"] == 1
    assert swaps[("ل", "ب")] == 0

    # Whisper's vocabulary prints each byte as a stand-in sign; "Ġال" is the
    # two bytes of alef and the two of lam, behind a leading space.
    assert _as_arabic("\u0120\u00d8\u00a7\u00d9\u0126") == " ال"


def test_the_ear_is_handed_the_recording_and_not_thirty_seconds_of_silence():
    """The sureness window is the sound's own length, rounded up to a block.

    It was always the full thirty seconds, whatever was recorded, and silence
    costs the ear what sound costs: 571ms to listen against 98ms on a six
    second recording, measured on this machine. Rounding up rather than exact
    keeps the ear being asked for a handful of sizes rather than a new one
    every time.
    """
    from backend.services.recitation.listen import _WINDOW_FRAMES, window_of

    # Six seconds of sound, asked for in whole seconds, is six seconds.
    assert window_of(601, 100) == 700
    assert window_of(600, 100) == 600
    # Never longer than the thirty seconds the ear can hold, however it rounds.
    assert window_of(2950, 100) == _WINDOW_FRAMES
    assert window_of(_WINDOW_FRAMES, 100) == _WINDOW_FRAMES
    # A recording shorter than one block still fills one, never none.
    assert window_of(1, 100) == 100
    assert window_of(0, 100) == 100
    # And the block that turns the saving off again is the old behaviour exactly.
    assert window_of(601, _WINDOW_FRAMES) == _WINDOW_FRAMES
