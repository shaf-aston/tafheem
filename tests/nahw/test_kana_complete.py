"""كان وأخواتها ناقصة or تامة, told by what follows (Ibn Aqil on كان التامة; Tasheel pp. 38-39)."""
from __future__ import annotations

import pytest

from backend.services.nahw.book import book_spelling, is_one
from tests.nahw_helpers import cards, needs_parser


def _names(sentence: str) -> list[str]:
    return [c.get("name") or c["role"] for c in cards(sentence)]


@needs_parser
@pytest.mark.parametrize("sentence, names", [
    # ناقصة: a خبر follows, each sister names its own pair
    ("كَانَ الْبَيْتُ نَظِيفًا", ["فعل ناقص", "اسم كان", "خبر كان"]),
    ("صَارَ الْمَاءُ ثَلْجًا", ["فعل ناقص", "اسم صار", "خبر صار"]),
    ("أَصْبَحَ الْجَوُّ بَارِدًا", ["فعل ناقص", "اسم أصبح", "خبر أصبح"]),
    ("مَا انْفَكَّ زَيْدٌ قَائِمًا", ["ما النافية", "فعل ناقص", "اسم انفك", "خبر انفك"]),
    ("كَانَ فِي الدَّارِ رَجُلٌ", ["فعل ناقص", "حرف جر", "مجرور", "اسم كان"]),  # its خبر a phrase, put first
    ("لَيْسَ زَيْدٌ", ["فعل ناقص", "اسم ليس"]),  # ليس is never تامة
    # تامة: no خبر, a plain verb and its فاعل
    ("أَصْبَحَ زَيْدٌ", ["فعل", "فاعل"]),
    ("مَا دَامَتِ السَّمَاوَاتُ وَالْأَرْضُ", ["ما النافية", "فعل", "فاعل", "معطوف"]),
])
def test_kana_and_sisters_are_defective_only_with_a_khabar(sentence, names):
    assert _names(sentence) == names


@pytest.mark.parametrize("lemma, spelled", [("ٱنفك", "انفك"), ("+كان", "كان"), ("كان", "كان")])
def test_book_spelling_writes_the_wasl_alif_plain(lemma, spelled):
    assert book_spelling(lemma) == spelled


def test_the_parsers_wasl_spelling_is_on_the_list():
    assert is_one("ٱنفك", "kana", "needs_negation")
