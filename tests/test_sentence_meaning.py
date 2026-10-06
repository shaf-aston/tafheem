"""More than one word in the dictionary: the sense, then word by word.

The outcome a reader sees: a sentence named a sentence and a phrase a phrase,
CAMeL's word-by-word read as English, and the word-by-word still there when the
model is not. CAMeL and the model are stood in for, so this tests the module's
own decisions and runs anywhere.

Run: python -m pytest tests/test_sentence_meaning.py
"""
from __future__ import annotations

import pytest

from backend.services import ai, morphology, sentence_meaning
from backend.services.quran_search import local


def _word(word, pos, state="na", gloss=""):
    return {"word": word, "pos": pos, "state": state, "gloss": gloss}


def test_camel_gloss_reads_as_english() -> None:
    assert sentence_meaning.literal("and+write+he;it_<verb>") == "and write he/it"
    assert sentence_meaning.literal("the+child;son;boy+[def.gen.]") == "the child/son"


@pytest.mark.parametrize("read, kind", [
    ([_word("ذهب", "verb"), _word("الولد", "noun", "d")], "sentence"),
    ([_word("البيت", "noun", "d"), _word("كبير", "adj", "i")], "sentence"),
    ([_word("الحمد", "noun", "d"), _word("لله", "noun_prop", "i")], "sentence"),
    ([_word("البيت", "noun", "d"), _word("الكبير", "adj", "d")], "phrase"),
    ([_word("رب", "noun", "c"), _word("العالمين", "noun", "d")], "phrase"),
])
def test_a_sentence_says_something_and_a_phrase_does_not(read, kind) -> None:
    assert sentence_meaning.kind_of("x", read) == kind


def test_a_closing_mark_makes_a_sentence() -> None:
    assert sentence_meaning.kind_of("رب العالمين؟", [_word("رب", "noun", "c"), _word("العالمين", "noun", "d")]) == "sentence"


@pytest.fixture
def typed(monkeypatch):
    """A two-word text no ayah is, read by a stand-in CAMeL, and a count of model calls."""
    monkeypatch.setattr(morphology, "analyze_sentence", lambda text: [
        _word("البيت", "noun", "d", "the+house"), _word("كبير", "adj", "i", "large;great")])
    monkeypatch.setattr(local, "whole_ayah", lambda text: None)
    sentence_meaning._asked.cache_clear()
    asked = []
    yield asked
    sentence_meaning._asked.cache_clear()


def test_the_model_gives_the_sense_once_per_text(typed, monkeypatch) -> None:
    monkeypatch.setattr(ai, "translate_sentence", lambda text, wbw: typed.append(wbw) or {"english": " The house is big. "})
    first = sentence_meaning.translate("البيت كبير")
    assert sentence_meaning.translate("البيت كبير") == first
    assert first["meaning"] == "The house is big." and first["source"] == "ai" and len(typed) == 1
    assert typed[0] == "البيت = the house | كبير = large/great"


def test_no_model_still_gives_the_words(typed, monkeypatch) -> None:
    def down(*args):
        raise RuntimeError("No AI backend available")

    monkeypatch.setattr(ai, "translate_sentence", down)
    found = sentence_meaning.translate("البيت كبير")
    assert found["meaning"] is None and found["source"] is None
    assert [w["english"] for w in found["words"]] == ["the house", "large/great"]
