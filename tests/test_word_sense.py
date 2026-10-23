"""A small word's English is the job the grammar gave it, not CAMeL's first guess.

CAMeL picks one reading of each word before the grammar runs, so إنّ could show the
condition's "if" while its card said إنّ وأخواتها. The particle tree's leaf names the
dictionary class its job reads in (`sense`), and the sentence's word-by-word takes that
reading's English, the joined letters' own English kept (فَإِنَّ "so indeed").

Run: python -m pytest tests/test_word_sense.py
"""
from __future__ import annotations

import pytest

from backend.services import morphology, sentence_meaning
from backend.services.harakat import NO_ANALYSIS
from tests.nahw_helpers import cards, needs_parser

# What CAMeL lists for إن, likeliest first: أَنَّ comes before both readings spelled إن.
_IN = [
    {"diac": "أَنَّ", "pos": "conj_sub", "stemgloss": "that"},
    {"diac": "إِنَّ", "pos": "verb_pseudo", "stemgloss": "that;indeed"},
    {"diac": "إِن", "pos": "conj_sub", "stemgloss": "if;whether"},
]


@pytest.fixture
def camel_in(monkeypatch):
    monkeypatch.setattr(morphology, "_analyses", lambda word: _IN if word == "إن" else [])


@pytest.mark.parametrize("reading, sense, english", [
    # the job's class: إنّ reads "indeed", its joined ف keeps its own English
    ({"gloss": "and;so+if;whether", "stemgloss": "if;whether", "pos": "conj_sub", "base": "إن"}, "verb_pseudo",
     "and;so+that;indeed"),
    # the class's reading spelled with the word's own letters, not أَنَّ's "that"
    ({"gloss": "that;indeed", "stemgloss": "that;indeed", "pos": "verb_pseudo", "base": "إن"}, "conj_sub", "if;whether"),
    # no job named, or CAMeL already read the word so: its gloss stands
    ({"gloss": "if;whether", "stemgloss": "if;whether", "pos": "conj_sub", "base": "إن"}, None, "if;whether"),
    ({"gloss": "if;whether", "stemgloss": "if;whether", "pos": "conj_sub", "base": "إن"}, "conj_sub", "if;whether"),
    # already that class: CAMeL's own sense of it stands, not another reading's of the class
    ({"gloss": "whether", "stemgloss": "whether", "pos": "conj_sub", "base": "إن"}, "conj_sub", "whether"),
    # CAMeL has no reading of that class for the word: its gloss stands
    ({"gloss": "if;whether", "stemgloss": "if;whether", "pos": "conj_sub", "base": "إن"}, "part_neg", "if;whether"),
])
def test_the_word_reads_in_its_jobs_class(camel_in, reading, sense, english) -> None:
    assert morphology.gloss_as(reading, sense) == english


def test_the_card_names_the_class_the_english_is_read_in(camel_in, monkeypatch) -> None:
    card = {"word": "فإن", "role": "حرف", "role_key": "harf", "case": "mabni", "sense": "verb_pseudo",
            "camel": {"gloss": "and;so+if;whether", "stemgloss": "if;whether", "pos": "conj_sub", "base": "إن"}}
    monkeypatch.setattr(sentence_meaning.iraab, "analyze", lambda text: {"words": [card], "summary": None})
    assert [w["english"] for w in sentence_meaning.read_words("فإن")[0]] == ["and/so that/indeed"]


def test_a_word_camel_cannot_read_has_no_english() -> None:
    """Its gloss is CAMeL's mark for that, which the reader saw and the model was told as English."""
    reading = morphology._analysis_dict_from_camel(
        "لننزعن", {"atbtok": NO_ANALYSIS, "gloss": "NO_ANALYSIS", "stemgloss": "NO_ANALYSIS", "pos": "noun_prop"})
    assert (reading["gloss"], reading["stemgloss"]) == ("", "")


@needs_parser
@pytest.mark.parametrize("sentence, english", [
    ("إِنَّ اللَّهَ غَفُورٌ رَحِيمٌ", "indeed"),  # إنّ وأخواتها
    ("إن تنصروا الله ينصركم", "if"),  # the condition, before its verb
    ("فلما جاءهم الحق قالوا هذا سحر", "when"),  # لمّا before a past verb
    ("مَا أَحْسَنَ السَّمَاءَ", "how"),  # the wonder
    ("ما هذا إلا سحر", "not"),  # a leaf that writes its class over the parser's reads in that class
])
def test_a_small_words_english_follows_the_grammar(sentence, english) -> None:
    assert english in sentence_meaning.read_words(sentence)[0][0]["english"]


@needs_parser
def test_lamma_before_a_past_verb_is_read_as_lamma() -> None:
    """CAMeL files the negation لَمّا under ما, so فلما was read as ما النافية."""
    first = cards("فلما جاءهم الحق قالوا هذا سحر")[0]
    assert (first["family"], first["named"]) == ("ghair_amila_other", "حرف وجود لوجود")


@pytest.mark.parametrize("written, word", [
    ("لما", "لما"),  # a word of the book's own: its lemma ما is CAMeL's filing, not the word
    ("عما", "ما"), ("كلما", "ما"),  # joined letters the book has no word for: the ما stands
])
def test_a_word_is_the_books_word_it_is_written_as(written, word) -> None:
    from backend.services.syntax import particles
    assert particles._lemma({"lemma": "ما", "form": written}) == word


@needs_parser
def test_no_word_shows_camels_mark_as_english() -> None:
    assert sentence_meaning.read_words("لننزعن من كل شيعة")[0][0]["english"] == ""


@pytest.mark.skipif(not morphology._CAMEL_AVAILABLE, reason="CAMeL data not installed")
def test_a_lone_words_meaning_is_its_own_not_its_joined_letters(monkeypatch) -> None:
    """The Sarf page's meaning, when the dictionary has none: وَكَتَبَ means "write", not "and"."""
    from backend.services import dictionary_service, sarf_word
    monkeypatch.setattr(dictionary_service, "meaning_of", lambda word: None)
    assert "write" in sarf_word.analyze("وَكَتَبَ", None).meaning
