"""More than one word in the dictionary: the sense, then word by word.

The outcome a reader sees: a sentence named a sentence and a phrase a phrase,
CAMeL's word-by-word read as English, and the word-by-word still there when the
model is not. CAMeL and the model are stood in for, so this tests the module's
own decisions and runs anywhere.

Run: python -m pytest tests/test_sentence_meaning.py
"""
from __future__ import annotations

import pytest

from backend.services import ai, dictionary_service, iraab, morphology, progress_store, sentence_meaning
from backend.services.quran_search import local


def _word(word, pos, state="na", gloss=""):
    return {"word": word, "pos": pos, "state": state, "gloss": gloss}


def test_camel_gloss_reads_as_english() -> None:
    assert sentence_meaning.literal("and+write+he;it_<verb>") == "and write he/it"
    assert sentence_meaning.literal("the+child;son;boy+[def.gen.]") == "the child/son"


@pytest.mark.parametrize("summary, read, kind", [
    ("جُمْلَةٌ إِنْشَائِيَّةٌ اِسْتِفْهَامِيَّةٌ", [_word("هل", "part"), _word("أنت", "pron"), _word("جائع", "adj", "i")], "sentence"),
    ("جُمْلَةٌ اِسْمِيَّةٌ", [_word("محمد", "noun_prop", "i"), _word("رسول", "noun", "c"), _word("الله", "noun_prop", "i")], "sentence"),
    ("جَارٌّ وَمَجْرُوْرٌ", [_word("الحمد", "noun", "d"), _word("لله", "noun_prop", "i")], "sentence"),
    ("جَارٌّ وَمَجْرُوْرٌ", [_word("الولد", "noun", "d"), _word("في", "prep"), _word("البيت", "noun", "d")], "sentence"),
    ("مُرَكَّبٌ تَوْصِيْفِيٌّ", [_word("البيت", "noun", "d"), _word("الكبير", "adj", "d")], "phrase"),
    ("مُرَكَّبٌ إِضَافِيٌّ", [_word("رب", "noun", "c"), _word("العالمين", "noun", "d")], "phrase"),
    (None, [_word("في", "prep"), _word("البيت", "noun", "d")], "phrase"),
    ("جُمْلَةٌ اِسْمِيَّةٌ", [_word("كتاب", "noun", "i")], "word"),
])
def test_a_sentence_says_something_and_a_phrase_does_not(summary, read, kind) -> None:
    assert sentence_meaning.kind_of(summary, read) == kind


@pytest.fixture
def typed(monkeypatch, tmp_path):
    """A two-word text no ayah is, read by a stand-in CAMeL, a fresh store, and a count of model calls."""
    monkeypatch.setattr(morphology, "analyze_sentence", lambda text: [
        _word("البيت", "noun", "d", "the+house"), _word("كبير", "adj", "i", "large;great")])
    monkeypatch.setattr(morphology, "glosses_of", lambda w: {"كبير": ["large;great", "old;aged"]}.get(w, []))
    monkeypatch.setattr(dictionary_service, "meanings_of", lambda w: {"البيت": ["home"]}.get(w, []))
    monkeypatch.setattr(local, "whole_ayah", lambda text: None)
    monkeypatch.setattr(iraab, "analyze", lambda text: {"summary": "جُمْلَةٌ اِسْمِيَّةٌ"})
    monkeypatch.setattr(progress_store, "data_path", lambda _name: tmp_path / "progress.db")
    progress_store.reset_connection()
    asked = []
    yield asked
    progress_store.reset_connection()


def test_the_model_gives_the_sense_once_per_text(typed, monkeypatch) -> None:
    monkeypatch.setattr(ai, "translate_sentence", lambda text, wbw: typed.append(wbw) or {"english": " The house is big. "})
    first = sentence_meaning.translate("البيت كبير")
    assert first["meaning"] == "The house is big." and first["source"] == "ai" and first["kind"] == "sentence"
    assert typed[0].splitlines() == ["1. البيت: 1) the house | 2) home", "2. كبير: 1) large/great | 2) old/aged"]
    # Another server process: nothing in memory, the same store on disk.
    progress_store.reset_connection()
    monkeypatch.setattr(ai, "translate_sentence", lambda text, wbw: typed.append(wbw) or {"english": "The house is large"})
    assert sentence_meaning.translate("البيت كبير") == first and len(typed) == 1


def test_no_model_still_gives_the_words(typed, monkeypatch) -> None:
    def down(*args):
        raise RuntimeError("No AI backend available")

    monkeypatch.setattr(ai, "translate_sentence", down)
    found = sentence_meaning.translate("البيت كبير")
    assert found["meaning"] is None and found["source"] is None
    assert [w["english"] for w in found["words"]] == ["the house", "large/great"]


def test_the_model_picks_each_words_sense_and_it_is_filed(typed, monkeypatch) -> None:
    monkeypatch.setattr(ai, "translate_sentence", lambda text, wbw: typed.append(wbw) or {"english": "The house is old", "senses": [2, 2]})
    first = sentence_meaning.translate("البيت كبير")
    assert [w["english"] for w in first["words"]] == ["home", "old/aged"] and first["words_source"] == "ai"
    progress_store.reset_connection()
    monkeypatch.setattr(ai, "translate_sentence", lambda text, wbw: typed.append(wbw) or {"english": "x", "senses": [1, 1]})
    assert sentence_meaning.translate("البيت كبير") == first and len(typed) == 1


@pytest.mark.parametrize("senses", [[2], [1, 2, 1], [1, 3], [0, 1], ["2", 1], [True, 1], None, "1,2"])
def test_bad_picks_leave_camels_senses(typed, monkeypatch, senses) -> None:
    monkeypatch.setattr(ai, "translate_sentence", lambda text, wbw: {"english": "The house is big", "senses": senses})
    found = sentence_meaning.translate("البيت كبير")
    assert found["meaning"] == "The house is big"
    assert [w["english"] for w in found["words"]] == ["the house", "large/great"] and found["words_source"] == "camel"
    monkeypatch.setattr(ai, "translate_sentence", lambda text, wbw: pytest.fail("asked twice"))
    assert sentence_meaning.translate("البيت كبير") == found


def test_a_sense_filed_before_picks_keeps_its_wording_and_gains_picks(typed, monkeypatch) -> None:
    progress_store.keep_questions(module="dict", sentence="البيت كبير", source="ai",
                                  questions=[{"question": "meaning", "answer": "The house is big"}])
    monkeypatch.setattr(ai, "translate_sentence", lambda text, wbw: typed.append(wbw) or {"english": "x", "senses": [2, 2]})
    found = sentence_meaning.translate("البيت كبير")
    assert found["meaning"] == "The house is big" and [w["english"] for w in found["words"]] == ["home", "old/aged"]
    assert sentence_meaning.translate("البيت كبير") == found and len(typed) == 1


@pytest.mark.parametrize("cut, shown", [
    ("[All] praise is [due] to Allāh, Lord of the worlds -", "[All] praise is [due] to Allāh, Lord of the worlds"),
    ('Say, "He is Allāh, [who is] One,', 'Say, "He is Allāh, [who is] One"'),
    ('Nor is there to Him any equivalent."', '"Nor is there to Him any equivalent."'),
    ("and the captive, (saying)", "And the captive, (saying)"),
])
def test_an_ayah_slice_stands_on_its_own(cut, shown) -> None:
    assert sentence_meaning.standing(cut) == shown


def test_words_with_no_arabic_are_named_not_dropped() -> None:
    from backend.services.arabic_text import not_arabic, words
    typed = "x كتاب hello، ١٢ ۖ"
    assert words(typed) == ["كتاب"] and not_arabic(typed) == ["x", "hello"]
