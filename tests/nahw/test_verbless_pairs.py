"""A verbless pair keeps its order: a صفة never leads its موصوف, so a word with ال before an indefinite one
is the مبتدأ and that one its خبر; and لا النافية للجنس heads its pair, whatever the parser hung it under."""
from __future__ import annotations

import pytest

from tests.nahw_helpers import analyze, needs_parser


def _roles(sentence: str) -> list[str | None]:
    return [w.get("role") for w in analyze(sentence)["words"]]


@needs_parser
@pytest.mark.parametrize("sentence", ["الخياطون حاذقون", "الخَيَّاطُونَ حَاذِقُونَ", "المعلمون مجتهدون", "الرجل كريم"])
def test_a_known_word_before_an_indefinite_one_is_the_mubtada(sentence):
    assert _roles(sentence) == ["مبتدأ", "خبر"]


@needs_parser
@pytest.mark.parametrize("sentence", ["لَا مُتْقِنًا صَنْعَتَهُ فَقِيرٌ", "لَا طَالِبًا عِلْمًا مُهْمِلٌ"])
def test_la_governs_its_name_and_its_khabar(sentence):
    assert _roles(sentence) == ["حرف", "اسم لا", "مفعول به", "خبر لا"]


@needs_parser
def test_a_second_known_word_stays_a_sifa_of_the_first():
    assert _roles("الرَّجُلُ الطَّبِيبُ مَاهِرٌ") == ["مبتدأ", "صفة", "خبر"]


@needs_parser
@pytest.mark.parametrize("sentence", ["عِنْدَنَا ضَيْفٌ", "الْيَوْمَ خَمْرٌ", "غَدًا سَفَرٌ", "عِنْدِي كِتَابٌ"])
def test_a_fronted_place_or_time_word_is_the_khabars_zarf(sentence):
    assert _roles(sentence) == ["مفعول فيه", "مبتدأ"]


@needs_parser
def test_a_time_word_in_raf_is_a_noun_not_a_zarf():
    assert _roles("الْيَوْمُ جَمِيلٌ") == ["مبتدأ", "خبر"]


@needs_parser
@pytest.mark.parametrize("sentence", ["إِنَّ عِنْدَنَا ضَيْفًا", "أَنَّ عِنْدَنَا ضَيْفًا", "إِنَّ لَدَيْنَا أَنْكَالًا", "إنّ عندنا ضيفا"])
def test_a_place_word_in_nasb_is_the_khabar_of_inna_said_first(sentence):
    assert _roles(sentence) == ["حرف", "خبر إن", "اسم إن"]


@needs_parser
def test_a_bare_time_word_before_a_known_noun_keeps_the_old_reading():
    assert _roles("اليوم عيد") == ["مبتدأ", "خبر"]


@needs_parser
def test_two_adjective_khabars_of_inna_stay_two_khabars():
    assert _roles("إِنَّ اللَّهَ غَفُورٌ رَحِيمٌ") == ["حرف", "اسم إن", "خبر إن", "خبر إن"]
