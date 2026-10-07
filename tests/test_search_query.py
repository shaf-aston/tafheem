"""Every search box reads what was typed one way: punctuation is a break between
words, never part of one. A full stop at the end used to ride into the
matching as a letter, so "القيامة." was a different word from القيامة.

Run: python -m pytest tests/test_search_query.py
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.services.arabic_text import unpunctuated, words
from backend.utils import search_query


@pytest.mark.parametrize("typed, read", [
    ("فالله يحكم بينهم يوم القيامة.", "فالله يحكم بينهم يوم القيامة"),
    ("مالك،يوم الدين؟", "مالك يوم الدين"),
    ("...mercy!", "mercy"),
    ("ك-ت-ب", "ك ت ب"),
    ("bukhari:52", "bukhari 52"),
    ("ذَٰلِكَ ٱلْكِتَٰبُ ۛ لَا رَيْبَ ۛ", "ذَٰلِكَ ٱلْكِتَٰبُ لَا رَيْبَ"),
    # An apostrophe inside a word is part of it; at its edge, a quote mark.
    ("don't 'patience'", "don't patience"),
    ("Mu’adh", "Mu’adh"),
])
def test_punctuation_is_a_break_between_words(typed, read):
    assert unpunctuated(typed) == read
    assert search_query(typed) == read


def test_a_query_of_punctuation_alone_is_empty():
    assert search_query(" .،؟ ") == ""
    with pytest.raises(HTTPException) as raised:
        search_query(" .،؟ ", required=True)
    assert raised.value.status_code == 400


def test_words_still_reads_an_ayah_the_same_way():
    assert words("مَرْحَبًا، ۞ يا ٢٥٥") == ["مَرْحَبًا", "يا"]
