"""A noun the dictionary lacks, read off its shape: a sound plural's or a dual's ending tells its number
and its case (Ibn Aqil V1 p59: وارفع بواو وبيا اجرر وانصب سالم جمع; V1 p55: بالألف ارفع المثنى)."""
from __future__ import annotations

import pytest

from backend.services.sarf import noun_reader


@pytest.mark.parametrize("word, number, case", [
    ("مُسْرِعُونَ", "p", "n"),   # ـونَ: raf'
    ("مُسْرِعِينَ", "p", "u"),   # ـينَ: nasb or jarr alike, so the case is left open
    ("مُسْرِعَانِ", "d", "n"),   # ـانِ: raf'
    ("مُسْرِعَيْنِ", "d", "u"),  # ـيْنِ: nasb or jarr alike
    ("مُسْرِعًا", "s", "a"),     # the written alif of nasb tanween
    ("مُسْرِعٌ", "s", "n"),      # nearest case: no ending peeled, the vowel says it
])
def test_a_sound_ending_is_peeled_for_its_number_and_case(word: str, number: str, case: str):
    found = noun_reader.reading_of(word)
    assert (found["lex"], found["num"], found["cas"], found["atbtok"]) == ("مسرع", number, case, word)


def test_an_ending_with_the_wrong_vowel_on_its_nun_is_no_sound_plural():
    assert noun_reader.reading_of("مُسْرِعِينِ") is None  # a plural's nun takes a fatha, never a kasra


@pytest.mark.parametrize("word, lex", [
    ("إِقَامِ", "إقام"),       # إِفْعَال of a hollow root: its middle letter gone, its ة fallen before a مضاف إليه (21:73)
    ("إِقَامَةِ", "إقام"),     # the same with the ة that stands in for that letter
    ("اِسْتِقَامُ", "استقام"),  # اِسْتِفْعَال the same way
])
def test_a_hollow_roots_masdar_is_read_off_its_shape(word: str, lex: str):
    found = noun_reader.reading_of(word)
    assert (found["pos"], found["lex"]) == ("noun", lex)
