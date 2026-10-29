"""The sounds ear: which letters and vowels were heard against the expected ones.

The comparison and the check's wiring run anywhere. The two model tests run a
real recitation through the int8 model and skip where the model, the expected
sounds or the marked recordings are not on this machine (GitHub has none).

Run: python -m pytest tests/recitation/test_recitation_sounds.py
"""
from __future__ import annotations

import json

import pytest

from backend.config import data_path, get_settings
from backend.services import recitation
from backend.services.recitation import checker, sounds

# 85:6 recited without a mistake, from the recitation-errors download (see score_recitation_checker.recordings).
CLEAN_CLIP = "errors/05ca0e304b329a00caf01b964952c3d360a0db5bef4a2fa21a1d32836c2f4258"
CLEAN_AYAH = "85:6"

# بِسْمِ اللَّهِ: b i s m i | ll a: h i
BISMI, ALLAH = ["b", "i", "s", "m", "i"], ["ll", "a:", "h", "i"]


def test_a_word_said_right_passes_and_files_what_was_heard_under_it():
    out = sounds.compare([BISMI, ALLAH], BISMI + ALLAH)
    assert out == [
        {"heard": BISMI, "expected": BISMI, "letter_ok": True, "vowel_ok": True},
        {"heard": ALLAH, "expected": ALLAH, "letter_ok": True, "vowel_ok": True},
    ]


def test_a_dropped_letter_and_a_long_vowel_said_short_fail_their_own_word_only():
    out = sounds.compare([BISMI, ALLAH], ["b", "i", "m", "i", "ll", "a", "h", "i"])
    assert [(w["letter_ok"], w["vowel_ok"]) for w in out] == [(False, True), (True, False)]
    assert out[0]["heard"] == ["b", "i", "m", "i"] and out[1]["heard"] == ["ll", "a", "h", "i"]


def test_an_extra_sound_between_words_goes_to_the_word_before_and_outside_ones_are_left_out():
    heard = ["ʔ"] + BISMI + ["n"] + ALLAH + ["z"]
    out = sounds.compare([BISMI, ALLAH], heard)
    assert out[0]["heard"] == BISMI + ["n"] and out[1]["heard"] == ALLAH
    assert out[0]["letter_ok"] and out[1]["letter_ok"]


def test_tajweed_symbols_are_judged_on_neither_side_and_a_word_without_sounds_is_none():
    # An ikhfaa m̃ in the expected sounds; the model's decode has it dropped too.
    out = sounds.compare([["b", "m̃", "a"], ()], ["b", "a"])
    assert out[0]["letter_ok"] and out[0]["expected"] == ["b", "a"]
    assert out[1] is None
    ids = {3: "a", 28: "m̃", 7: "b"}
    assert sounds.collapse([0, 7, 7, 28, 0, 3, 3, 3], ids) == (["b", "a"], [2, 3])


def test_the_reference_of_an_ayah_with_another_word_count_is_not_guessed(monkeypatch):
    monkeypatch.setattr(sounds, "_reference", lambda: {"1:1": [BISMI, ALLAH]})
    assert sounds.expected_for("1:1", 2) == [BISMI, ALLAH]
    assert sounds.expected_for("1:1", 3) is None
    assert sounds.expected_for("9:9", 2) is None


def fake_words(monkeypatch, plain):
    monkeypatch.setattr(recitation, "_plain", lambda: plain)
    monkeypatch.setattr(checker, "weigh", lambda audio, words, model=None: [
        {"sure": 0.9, "weak": None, "at": None} for _ in words])


def test_each_words_sounds_go_to_its_own_word_and_never_change_the_sureness(monkeypatch):
    fake_words(monkeypatch, {"112:1": "قُلْ هُوَ اللَّهُ أَحَدٌ", "112:2": "اللَّهُ الصَّمَدُ"})
    monkeypatch.setattr(sounds, "_reference", lambda: {"112:1": [["q", "u", "l"]] * 4, "112:2": [["a"]] * 2})
    asked = []

    def hear(audio, expected):
        asked.append(expected)
        return [None if i == 0 else {"heard": [str(i)], "expected": expected[i], "letter_ok": i != 2, "vowel_ok": True}
                for i in range(len(expected))]

    monkeypatch.setattr(sounds, "hear_sounds", hear)
    sure, detail = recitation.check(b"sound", "أحد الله الصمد", ["112:1", "112:2"])
    assert sure == {"112:1": [None, None, None, 0.9], "112:2": [0.9, 0.9]}
    assert asked == [[["q", "u", "l"], ["a"], ["a"]]]
    assert [d and d["sounds"] for d in detail["112:1"]] == [None, None, None, None]
    assert detail["112:2"][0]["sounds"]["heard"] == ["1"] and detail["112:2"][0]["sounds"]["letter_ok"]
    assert not detail["112:2"][1]["sounds"]["letter_ok"]


def test_a_check_still_answers_when_the_sounds_cannot_be_heard(monkeypatch):
    fake_words(monkeypatch, {"112:1": "قُلْ هُوَ اللَّهُ أَحَدٌ"})
    monkeypatch.setattr(get_settings(), "recitation_sounds", True)
    monkeypatch.setattr(sounds, "_reference", lambda: {"112:1": [["q"]] * 4})
    monkeypatch.setattr(sounds, "installed", lambda: True)
    monkeypatch.setattr(sounds, "_engine", lambda: (_ for _ in ()).throw(sounds.NotInstalled("gone")))
    monkeypatch.setattr(sounds.whisper, "sound_of", lambda audio: [0.0] * 1600)
    sure, detail = recitation.check(b"sound", "قل هو الله أحد", ["112:1"])
    assert sure == {"112:1": [0.9] * 4}
    assert all(d["sounds"] is None for d in detail["112:1"])


on_this_machine = pytest.mark.skipif(
    not (sounds.installed() and data_path("recitation_sounds_reference_path").is_file()
         and (data_path("quran_imlaei_path").parent / "downloads").is_dir()),
    reason="the sounds model, its reference and the marked recordings are built on this machine only",
)


@pytest.fixture
def clean_recitation(monkeypatch):
    """(wav bytes, the ayah's expected sounds) of a recitation with no mistake."""
    from backend.scripts.recitation.score_recitation_checker import recordings

    monkeypatch.setattr(get_settings(), "recitation_sounds", True)
    plain = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    audio = next(a for rid, a, _, _ in recordings(plain) if rid == CLEAN_CLIP)
    return audio, sounds._reference()[CLEAN_AYAH]


@on_this_machine
def test_a_correct_recitation_is_heard_as_the_expected_sounds(clean_recitation):
    audio, expected = clean_recitation
    out = sounds.hear_sounds(audio, expected)
    assert len(out) == len(expected)
    assert all(w["letter_ok"] and w["vowel_ok"] for w in out)
    assert all(w["heard"] for w in out)


@on_this_machine
def test_the_same_recitation_against_altered_expected_sounds_fails_those_words(clean_recitation):
    audio, expected = clean_recitation
    altered = [list(w) for w in expected]
    consonant = next(i for i, p in enumerate(altered[1]) if p not in sounds.VOWELS)
    altered[1][consonant] = "ʒʒ"
    vowel = next(i for i, p in enumerate(altered[2]) if p in sounds.VOWELS)
    altered[2][vowel] = "u:" if altered[2][vowel] != "u:" else "i:"
    out = sounds.hear_sounds(audio, altered)
    assert not out[1]["letter_ok"] and not out[2]["vowel_ok"]
    assert out[0]["letter_ok"] and out[0]["vowel_ok"]
