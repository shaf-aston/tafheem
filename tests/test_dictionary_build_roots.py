"""A rootless Wiktionary entry takes the root of the word it says it comes from.

Run: python -m pytest tests/test_dictionary_build_roots.py
"""
from __future__ import annotations

from backend.scripts.build_dictionary import fits, inherit_roots, source_words


def test_the_word_named_in_the_etymology_is_read_bare():
    entry = {"etymology_text": "Derived from the active participle of اِشْتَاقَ (ištāqa, “to long for”)."}
    assert source_words(entry) == ["اشتاق"]


def test_a_rootless_entry_takes_its_source_words_root():
    by_word = {"مشتاق": {"root": ""}, "اشتاق": {"root": "ش و ق"}}
    assert inherit_roots(by_word, {"مشتاق": ["اشتاق"]}) == 1
    assert by_word["مشتاق"]["root"] == "ش و ق"


def test_a_root_not_in_the_words_letters_is_not_taken():
    """إله is "a variant of" a word on another root: that root is not its own."""
    assert not fits("ن ف ق", "إحراق")
    assert fits("ق و ل", "قال")
    by_word = {"إحراق": {"root": ""}, "إنفاق": {"root": "ن ف ق"}}
    assert inherit_roots(by_word, {"إحراق": ["إنفاق"]}) == 0
