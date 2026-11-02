"""Questions read straight: the hamza written onto a verb, a question word joined to a preposition, a
question noun that is the khabar or name of a كان-sister, كم with a time word, أنّى, and the noun after a
preposition in a question (Tasheel 1.5 istifham)."""
from __future__ import annotations

import pytest

from tests.nahw_helpers import analyze, needs_parser


def _roles(sentence: str) -> list[str | None]:
    return [w.get("role") for w in analyze(sentence)["words"]]


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("أَذَهَبَ زَيْدٌ؟", ["فعل", "فاعل"]),
    ("أَكَتَبْتَ الدَّرْسَ؟", ["فعل", "مفعول به"]),
    ("مَاذَا كَتَبْتُمْ فِي الدَّفْتَرِ؟", ["مفعول به", "فعل", "حرف جر", "مجرور"]),
])
def test_hamza_and_madha_read_straight(sentence, roles):
    assert _roles(sentence) == roles


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("لِمَاذَا تَأَخَّرْتَ؟", ["مجرور", "فعل"]),
    ("بِمَ تَشْعُرُ؟", ["مجرور", "فعل"]),
    ("فِيمَ تُفَكِّرُ؟", ["حرف جر", "فعل"]),
    ("عَمَّ يَتَسَاءَلُونَ؟", ["حرف جر", "فعل"]),
    ("إِلَامَ تَنْتَظِرُ؟", ["حرف جر", "فعل"]),
])
def test_question_word_joined_to_a_preposition(sentence, roles):
    assert _roles(sentence) == roles


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("كَيْفَ أَصْبَحْتَ؟", ["خبر كان", "فعل"]),
    ("أَيْنَ كُنْتَ؟", ["خبر كان", "فعل"]),
    ("مَاذَا كَانَ الْجَوَابُ؟", ["خبر كان", "فعل", "اسم كان"]),
    ("مَنْ كَانَ مَعَكَ؟", ["اسم كان", "فعل", "خبر كان"]),
])
def test_question_word_with_a_kana_sister(sentence, roles):
    assert _roles(sentence) == roles


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("كَمْ يَوْمًا سَافَرْتَ؟", ["مفعول فيه", "تمييز", "فعل"]),
    ("أَنَّى لَكَ هَذَا؟", ["خبر", "حرف جر", "مبتدأ"]),
    ("هَلْ مِنْ مُجِيبٍ؟", ["حرف", "حرف جر", "مجرور"]),
    ("مَا لَنَا مِنْ شَافِعٍ", ["–", "حرف جر", "حرف جر", "مجرور"]),
])
def test_kam_time_anna_and_noun_after_min(sentence, roles):
    assert _roles(sentence) == roles
