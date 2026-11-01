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
def test_a_describing_word_after_its_known_noun_stays_its_sifa():
    assert "صفة" in _roles("الرَّجُلُ الْكَرِيمُ")
