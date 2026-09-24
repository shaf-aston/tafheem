"""The Qur'anic corpus reader, the grammar it reports must be the corpus's own.

These check the two things that can silently go wrong: reading a word's shorthand
into the wrong words, and picking the wrong piece of a word as its stem (which is
how بِسْمِ lost its root during development).

Run: python -m pytest tests/test_quran_corpus.py
"""
from __future__ import annotations

import pytest

from backend.services import arabic_text, quran_corpus

pytestmark = pytest.mark.skipif(
    not quran_corpus.is_loaded(),
    reason="corpus.db not built, run backend/scripts/build_quran_corpus.py",
)


def grammar_of(surah: int, ayah: int, word: int) -> list[str]:
    return quran_corpus.words_for_ayah(surah, ayah)[word]["grammar"]


def test_prefixed_word_keeps_its_own_root():
    """بِسْمِ is بِ + سْمِ. The root belongs to the stem, not to the preposition."""
    word = quran_corpus.words_for_ayah(1, 1)[0]
    assert word["arabic"] == "بِسْمِ"
    assert word["root"] == "سمو"
    assert word["segments"][0]["grammar"] == ["حرف جر", "بادئة"]


def test_verb_reports_tense_pattern_and_person():
    """نَعْبُدُ, present, Form I, first person plural, indicative."""
    grammar = grammar_of(1, 5, 1)
    assert "فعل" in grammar
    assert "مضارع" in grammar
    assert "وزن فَعَلَ" in grammar
    assert "متكلم" in grammar and "جمع" in grammar


def test_form_ten_verb_names_its_pattern():
    """نَسْتَعِينُ is Form X, the baab a Sarf student would be looking for."""
    grammar = grammar_of(1, 5, 3)
    assert "وزن اسْتَفْعَلَ" in grammar


def test_command_verb_is_not_read_as_a_particle():
    """IMPV means "command" on a verb but "command laam" on a particle. قُلْ is a verb."""
    grammar = grammar_of(112, 1, 0)
    assert "أمر" in grammar
    assert "لام الامر" not in grammar


def test_case_tag_is_not_read_as_a_particle():
    """ACC is the accusative case on a noun, not an accusative particle."""
    grammar = grammar_of(2, 255, 2)   # إِلَٰهَ
    assert "منصوب" in grammar
    assert "حرف نصب" not in grammar


def test_root_lookup_counts_every_occurrence():
    found = quran_corpus.occurrences_of_root("كتب", limit=5)
    assert found["total"] == 319
    assert len(found["occurrences"]) == 5           # capped, and the cap is honest
    assert found["forms"][0]["lemma"] == "كِتاب"    # commonest first


def test_unknown_root_returns_nothing_rather_than_guessing():
    assert quran_corpus.occurrences_of_root("زززز", limit=5)["total"] == 0


@pytest.mark.parametrize("written", [
    "ك-ت-ب",           # hyphen-minus, what the tagger returns
    "كتب",             # the corpus's own spelling
    " ك-ت-ب ",         # and either, typed with stray spaces
    "ك‐ت‐ب",           # U+2010 hyphen
    "ك–ت–ب",           # U+2013 en-dash - what a word processor turns "-" into
    "ك ت ب",           # U+00A0 non-breaking space
    "ك​ت​ب",           # U+200B zero-width space - invisible in every editor
    "ك‍ت‍ب",           # U+200D zero-width joiner
    "﻿كتب",            # U+FEFF byte-order mark, as a pasted file often starts
    "كـتـب",           # U+0640 tatweel - stretches the word, is not a letter
    "كَتَبَ",          # and with harakat on
])
def test_roots_match_however_they_are_written(written):
    """The tagger hyphenates roots and the corpus does not; a link between the
    tabs only works if both spellings find the same three letters.

    The separators below are the point. This used to drop a list of four
    characters, so a root written with an en-dash or a zero-width space kept it
    and was filed under letters no search could produce - including in the
    classical root book, whose index is built with this very function.
    """
    assert arabic_text.normalize_root(written) == "كتب"


def test_a_root_with_no_arabic_in_it_normalises_to_nothing():
    """"ktb" is a question about a root, not a root. Left as Latin it would be
    looked up, miss, and be reported as the book having no entry for it."""
    assert arabic_text.normalize_root("ktb") == ""
    assert arabic_text.normalize_root("") == ""
