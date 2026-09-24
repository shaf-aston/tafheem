"""What counts as a word to analyse: the rule, not a list of marks to skip.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
from backend.services.arabic_text import spelled_out, words

AYAH = "يُرِيدُ ٱللَّهُ أَن يُخَفِّفَ عَنكُمْ ۚ وَخُلِقَ ٱلْإِنسَـٰنُ ضَعِيفًۭا ٢٨"


def test_pause_sign_and_ayah_number_are_not_words():
    got = words(AYAH)
    assert len(got) == 8
    assert "ۚ" not in got and "٢٨" not in got


def test_reading_marks_come_off_the_word_they_sit_on():
    # The small meem inside ضَعِيفًۭا made the tagger call it foreign.
    assert words(AYAH)[-1] == "ضَعِيفًا"
    assert "ـ" not in words(AYAH)[-2]


def test_plain_sentence_is_unchanged():
    assert words("ذهب الولد إلى المدرسة") == ["ذهب", "الولد", "إلى", "المدرسة"]


def test_punctuation_glued_to_a_word_comes_off():
    assert words("مَرْحَبًا، كَيْفَ حَالُكَ؟") == ["مَرْحَبًا", "كَيْفَ", "حَالُكَ"]
    assert words("«قال»:نعم.لا") == ["قال", "نعم", "لا"]


def test_marks_alone_leave_nothing():
    assert words("۝ ٢٨ ۚ ،") == []


def test_a_word_spelled_letter_by_letter_is_joined():
    assert spelled_out("ك ت ب") == "كتب"
    assert spelled_out("ك-ت-ب") == "كتب"
    assert spelled_out("  ك  ت  ب  ") == "كتب"
    assert spelled_out("كَ تَ بَ") == "كَتَبَ"


def test_anything_else_is_left_alone():
    assert spelled_out("كتب") == "كتب"
    assert spelled_out("ذهب الولد") == "ذهب الولد"
    assert spelled_out("ك ت ب الولد") == "ك ت ب الولد"   # one longer piece: a phrase
    assert spelled_out("و ب") == "و ب"                    # two letters: two words
    assert spelled_out("a b c") == "a b c"
    assert spelled_out("1 2 3") == "1 2 3"
