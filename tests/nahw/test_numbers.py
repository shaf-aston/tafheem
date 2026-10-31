"""العدد (Tasheel 1.4.3 p10): a compound number takes the one place its sentence gives it on both
parts, built on their fatha; a joined hundred shows its case on the unit; كم asks for the object
only of a verb that takes one, and a jarr noun after it is its مضاف إليه. Each held with and
without vowels where the bare letters still say it."""
from __future__ import annotations

import pytest

from backend.services.text.arabic_text import strip_diacritics
from tests.nahw_helpers import analyze, needs_parser


def _roles(sentence: str) -> list[str | None]:
    return [w.get("role") for w in analyze(sentence)["words"]]


def _both(sentence: str, roles: list[str]) -> None:
    assert _roles(sentence) == roles
    assert _roles(strip_diacritics(sentence)) == roles


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("حَضَرَ أَرْبَعَةَ عَشَرَ طَالِبًا", ["فعل", "فاعل", "فاعل", "تمييز"]),
    ("قَرَأْتُ سَبْعَ عَشْرَةَ صَفْحَةً", ["فعل", "مفعول به", "مفعول به", "تمييز"]),
    ("رَأَيْتُ أَحَدَ عَشَرَ كَوْكَبًا", ["فعل", "مفعول به", "مفعول به", "تمييز"]),
    ("اشْتَرَيْتُ اثْنَيْ عَشَرَ قَلَمًا", ["فعل", "مفعول به", "مفعول به", "تمييز"]),
])
def test_a_compound_number_takes_one_role_on_both_parts(sentence, roles):
    _both(sentence, roles)


@needs_parser
def test_a_compound_number_is_built_on_the_fatha_of_both_parts():
    signs = [w.get("sign") for w in analyze("حَضَرَ أَرْبَعَةَ عَشَرَ طَالِبًا")["words"]]
    assert signs[1] == signs[2] == "مبني على فتح الجزأين في محل رفع"
    # اثنا is ملحق بالمثنى: only its عشر is built
    assert analyze("جَاءَ اثْنَا عَشَرَ رَجُلًا")["words"][2]["sign"] == "مبني على الفتح في محل رفع"


@needs_parser
def test_a_compound_ordinal_describes_its_noun():
    _both("قَرَأْتُ الصَّفْحَةَ الْخَامِسَةَ عَشْرَةَ", ["فعل", "مفعول به", "صفة", "صفة"])


@needs_parser
def test_a_joined_hundred_shows_its_case_on_the_unit():
    _both("حَضَرَ خَمْسُمِائَةِ رَجُلٍ", ["فعل", "فاعل", "مضاف إليه"])


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("كَمْ رَجُلًا جَلَسَ", ["مبتدأ", "تمييز", "فعل"]),
    ("مَاذَا حَدَثَ", ["مبتدأ", "فعل"]),
    ("كَمْ كِتَابًا قَرَأْتَ", ["مفعول به", "تمييز", "فعل"]),
])
def test_a_question_noun_is_the_object_only_of_a_verb_that_takes_one(sentence, roles):
    _both(sentence, roles)

