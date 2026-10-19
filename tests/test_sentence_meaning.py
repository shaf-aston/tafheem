"""More than one word in the dictionary: the sense, then word by word.

The outcome a reader sees: a sentence named a sentence and a phrase a phrase,
CAMeL's word-by-word read as English, and the word-by-word still there when the
model is not. CAMeL and the model are stood in for, so this tests the module's
own decisions and runs anywhere.

Run: python -m pytest tests/test_sentence_meaning.py
"""
from __future__ import annotations

import pytest

from backend.services import ai, iraab, morphology, progress_store, sentence_meaning
from backend.services import quran_search


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


_CARDS = [
    {"word": "البيت", "role": "مبتدأ", "role_key": "mubtada", "case": "raf'", "type": "ism",
     "camel": {"gloss": "the+house", "base": "بيت", "lemma": "بَيْت", "pos": "noun", "state": "d"}},
    {"word": "كبير", "role": "خبر", "role_key": "khabar", "case": "raf'", "type": "ism",
     "camel": {"gloss": "large;great", "base": "كبير", "lemma": "كَبِير", "pos": "adj", "state": "i"}},
]


@pytest.fixture
def typed(monkeypatch, tmp_path):
    """A two-word text no ayah is, read by a stand-in i'rab reading, a fresh store, and a count of model calls."""
    monkeypatch.setattr(iraab, "analyze", lambda text: {"words": _CARDS, "summary": "جُمْلَةٌ اِسْمِيَّةٌ"})
    monkeypatch.setattr(morphology, "analyze_sentence", lambda text: [
        {**_word("البيت", "noun", "d", "the+house"), "lemma": "بَيْت"}, _word("كبير", "adj", "i", "large;great")])
    monkeypatch.setattr(quran_search, "whole_ayah", lambda text: None)
    monkeypatch.setattr(progress_store, "data_path", lambda _name: tmp_path / "progress.db")
    progress_store.reset_connection()
    asked = []
    yield asked
    progress_store.reset_connection()


def _model(typed, reply):
    return lambda text, facts: typed.append(facts) or reply


def test_words_come_from_the_iraab_cards(typed, monkeypatch) -> None:
    monkeypatch.setattr(ai, "translate_sentence", _model(typed, {"english": "x"}))
    found = sentence_meaning.translate("البيت كبير")
    assert [(w["english"], w["role"], w["case"]) for w in found["words"]] == [
        ("the house", "مبتدأ", "raf'"), ("large/great", "خبر", "raf'")]
    assert found["kind"] == "sentence" and found["words_source"] == "camel"


def test_without_the_parser_camel_reads_alone(typed, monkeypatch) -> None:
    def missing(text):
        raise RuntimeError("parser model files are missing")

    monkeypatch.setattr(iraab, "analyze", missing)
    monkeypatch.setattr(ai, "translate_sentence", _model(typed, {"english": "x"}))
    found = sentence_meaning.translate("البيت كبير")
    assert [(w["english"], w["role"]) for w in found["words"]] == [("the house", None), ("large/great", None)]
    assert found["kind"] == "sentence"  # no summary, but a definite noun told about is still read


def test_the_model_gets_the_grammars_facts_and_gives_the_sense_once(typed, monkeypatch) -> None:
    monkeypatch.setattr(ai, "translate_sentence", _model(typed, {"english": " The house is big. "}))
    first = sentence_meaning.translate("البيت كبير")
    assert first["meaning"] == "The house is big." and first["source"] == "ai"
    assert typed[0].splitlines() == [
        "1. البيت — بَيْت (noun, مبتدأ, raf'): the house", "2. كبير — كَبِير (adj, خبر, raf'): large/great"]
    # Another server process: nothing in memory, the same store on disk.
    progress_store.reset_connection()
    monkeypatch.setattr(ai, "translate_sentence", _model(typed, {"english": "The house is large"}))
    assert sentence_meaning.translate("البيت كبير") == first and len(typed) == 1


def test_no_model_still_gives_the_words(typed, monkeypatch) -> None:
    def down(*args):
        raise RuntimeError("No AI backend available")

    monkeypatch.setattr(ai, "translate_sentence", down)
    found = sentence_meaning.translate("البيت كبير")
    assert found["meaning"] is None and found["source"] is None
    assert [w["english"] for w in found["words"]] == ["the house", "large/great"]


def test_an_empty_answer_is_not_filed(typed, monkeypatch) -> None:
    monkeypatch.setattr(ai, "translate_sentence", _model(typed, {"english": "  "}))
    assert sentence_meaning.translate("البيت كبير")["meaning"] is None
    monkeypatch.setattr(ai, "translate_sentence", _model(typed, {"english": "The house is big"}))
    assert sentence_meaning.translate("البيت كبير")["meaning"] == "The house is big" and len(typed) == 2


def test_an_old_filing_with_picks_is_not_reused(typed, monkeypatch) -> None:
    progress_store.keep_questions(module="dict", sentence="البيت كبير", source="ai",
                                  questions=[{"question": "meaning", "answer": "Old wording"}, {"question": "senses", "answer": "2,2"}])
    monkeypatch.setattr(ai, "translate_sentence", _model(typed, {"english": "The house is big"}))
    assert sentence_meaning.translate("البيت كبير")["meaning"] == "The house is big"


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
