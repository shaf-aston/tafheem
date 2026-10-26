"""A number added to a time word stands in for it (ما ينوب عن الظرف): لَبِثْتُ عَشْرَ سِنِينَ.
One of the six nouns before a name is its مضاف by its case letter: أَبُو مُوسَى."""
import pytest

from tests.nahw_helpers import cards, needs_parser


def role(sentence: str, index: int) -> str:
    return cards(sentence)[index]["role"]


@needs_parser
def test_a_number_counting_a_time_is_mafool_fihi_and_counting_men_is_not():
    assert role("لَبِثْتُ عَشْرَ سِنِينَ", 1) == "مفعول فيه"
    assert role("رَأَيْتُ ثَلَاثَةَ رِجَالٍ", 1) == "مفعول به"


@needs_parser
@pytest.mark.parametrize("sentence, expected", [
    ("نِمْتُ اللَّيْلَ", "مفعول فيه"),
    ("نِمْتُ كُلَّ اللَّيْلِ", "مفعول فيه"),
    ("أَحْبَبْتُ النَّهَارَ", "مفعول به"),  # loved, not in: the day is what is loved
])
def test_night_and_day_are_times_when_the_verb_happens_in_them(sentence, expected):
    assert role(sentence, 1) == expected


@needs_parser
def test_a_plural_spelled_without_its_ta_is_still_the_listed_word_but_bakr_is_no_bukra():
    assert role("لَبِثْتُ عَشْرَ سِنِينَ", 1) == "مفعول فيه"  # سنين is listed as سنة
    assert role("رَأَيْتُ بَكْرًا", 1) == "مفعول به"  # بكرا is a name, not بكرة (early morning)


@needs_parser
@pytest.mark.parametrize("sentence", ["جَاءَ أَبُو مُوسَى", "رَأَيْتُ أَبَا مُوسَى", "مَرَرْتُ بِأَبِي مُوسَى",
                                      "جَاءَ أَبِي مُوسَى"])  # mis-cased: still أبو موسى, not "my father"
def test_a_name_after_one_of_the_six_nouns_is_mudaf_ilayh(sentence):
    assert cards(sentence)[-1]["role"] == "مضاف إليه"


@needs_parser
def test_my_father_and_his_father_stay_what_they_are():
    assert role("أَبُوهُ مُوسَى", 1) == "خبر"  # added to ه already: no مضاف to موسى
    father = cards("جَاءَ أَبِي زَيْدٌ")[1]  # زيد shows its case: أبي is my father, not أبو زيد
    assert father["role"] == "فاعل" and "«ي» ضمير متصل" in father["reason"]
