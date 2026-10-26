"""The case a typed word shows is read off its last mark, whatever sits beside it.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import pytest

from backend.services.text.harakat import CASE_NAME, plural_alef, typed_case


@pytest.mark.parametrize("word, case", [
    ("كِتَابٌ", "raf'"),
    ("الجَوُّ", "raf'"),       # damma beside a shadda
    ("رَبِّ", "jarr"),         # kasra beside a shadda
    ("كِتَابًا", "nasb"),      # tanween written before the closing alef
    ("حَقًّا", "nasb"),        # both at once
    ("كتاباً", "nasb"),        # tanween written on the alef
])
def test_the_last_mark_gives_the_case(word, case):
    assert CASE_NAME.get(typed_case(word)) == case


@pytest.mark.parametrize("word", ["كتاب", "هذا", "دَعَا", "قَلَمْ"])
def test_no_mark_means_no_case(word):
    # دَعَا ends in a plain alef, not a tanween seat; قَلَمْ shows a sukun.
    assert CASE_NAME.get(typed_case(word)) is None


@pytest.mark.parametrize("verb, whole", [
    ("ضَرَبُو", "ضَرَبُوا"),    # ضَرَبُوهُ less its pronoun: the plural's alef comes back
    ("رَمَوْ", "رَمَوْا"),      # the و after a fatha is the plural's too
    ("سَرُوَ", "سَرُوَ"),      # nearest case: a vowel on the و makes it the verb's own
    ("ضَرَبَ", "ضَرَبَ"),      # nearest case: no و
])
def test_the_alef_after_the_plurals_waw_comes_back(verb, whole):
    assert plural_alef(verb) == whole
