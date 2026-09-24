"""The case a typed word shows is read off its last mark, whatever sits beside it.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import pytest

from backend.services import morphology


@pytest.mark.parametrize("word, case", [
    ("كِتَابٌ", "raf'"),
    ("الجَوُّ", "raf'"),       # damma beside a shadda
    ("رَبِّ", "jarr"),         # kasra beside a shadda
    ("كِتَابًا", "nasb"),      # tanween written before the closing alef
    ("حَقًّا", "nasb"),        # both at once
    ("كتاباً", "nasb"),        # tanween written on the alef
])
def test_the_last_mark_gives_the_case(word, case):
    assert morphology._harakat_case(word) == case


@pytest.mark.parametrize("word", ["كتاب", "هذا", "دَعَا", "قَلَمْ"])
def test_no_mark_means_no_case(word):
    # دَعَا ends in a plain alef, not a tanween seat; قَلَمْ shows a sukun.
    assert morphology._harakat_case(word) is None
