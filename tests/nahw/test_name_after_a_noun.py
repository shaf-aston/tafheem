"""A name after a noun: under a verb it names that noun again (بدل: جاء أخوك موسى); with no verb
it is what is said of it (خبر: أخوك موسى). A name ending in ى hides its case like any مقصور
noun, and a noun before ياء المتكلم hides its own (صديقي زيدٌ)."""
import pytest

from backend.services.sarf import morphology
from tests.nahw_helpers import cards, needs_camel, needs_parser


def roles(sentence: str) -> list[str]:
    return [c["role"] for c in cards(sentence)]


@needs_parser
@pytest.mark.parametrize("sentence", ["أَخُوكَ زَيْدٌ", "أَخُوكَ مُوسَى", "صَدِيقِي زَيْدٌ", "كِتَابِي جَدِيدٌ"])
def test_with_no_verb_the_word_after_the_noun_is_its_khabar(sentence):
    assert roles(sentence) == ["مبتدأ", "خبر"]


@needs_parser
@pytest.mark.parametrize("sentence", ["جَاءَ أَخُوكَ مُوسَى", "جَاءَ أَخُوكَ مُحَمَّدٌ", "رَأَيْتُ أَبَاكَ عِيسَى",
                                      "مَرَرْتُ بِأَخِيكَ زَيْدٍ", "جَاءَ أَبِي زَيْدٌ"])
def test_under_a_verb_a_name_after_the_noun_is_its_badal(sentence):
    assert roles(sentence)[-1] == "بدل"


@needs_parser
def test_a_word_the_parser_only_guessed_a_name_is_no_badal():
    assert roles("رَأَيْتُ صَدِيقَكَ مُسْرِعًا")[-1] == "حال"


@needs_parser
def test_a_name_ending_in_alif_maqsura_hides_its_case():
    musa = cards("جَاءَ مُوسَى")[1]
    assert (musa["role"], musa["sign"]) == ("فاعل", "ضمة مقدرة على الألف للتعذر")


@needs_parser
@pytest.mark.parametrize("sentence", ["قَابَلْتُ أَخَاكَ مُحَمَّدًا", "رَأَيْتُ أَخَاكَ زَيْدًا"])
def test_a_name_in_nasb_is_read_as_that_name_though_the_dictionary_lacks_its_alif(sentence):
    words = cards(sentence)
    assert (words[-1]["role"], words[-1]["case"]) == ("بدل", "nasb")


@needs_parser
@pytest.mark.parametrize("sentence", ["ضَرَبَ مُوسَى عِيسَى", "رَأَى مُوسَى عِيسَى", "أَكْرَمَ مُصْطَفَى يَحْيَى"])
def test_two_names_showing_no_case_are_told_apart_by_order_the_doer_first(sentence):
    assert roles(sentence) == ["فعل", "فاعل", "مفعول به"]


@needs_parser
def test_a_name_after_a_name_is_no_badal_and_after_a_bare_six_noun_it_is_mudaf_ilayh():
    assert roles("جَاءَ أَبُو مُوسَى") == ["فعل", "فاعل", "مضاف إليه"]
    assert roles("ضَرَبَ زَيْدٌ عَمْرًا") == ["فعل", "فاعل", "مفعول به"]


@needs_parser
def test_a_damma_before_the_alif_is_no_nasb():
    assert cards("قَابَلْتُ أَخَاكَ مُحَمَّدُا")[-1]["role"] != "بدل"


@needs_parser
def test_a_verb_with_its_doer_already_keeps_it():
    assert roles("ضَرَبَ زَيْدٌ مُوسَى عِيسَى")[:3] == ["فعل", "فاعل", "مفعول به"]


@needs_camel
@pytest.mark.parametrize("sentence, lemma", [
    ("ضَرَبَ زَيْدٌ عَمْرًا", "عمرو"), ("رَأَيْتُ زَيْدًا وَعَمْرًا", "عمرو"),  # the و that tells عمرو from عمر drops in nasb
    ("ضَرَبَ زَيْدٌ عُمَرًا", "عمر"), ("ضرب زيد عمرا", "عمر"),  # its vowels say عُمَر; unmarked, the name as written
])
def test_a_name_whose_telling_waw_drops_in_nasb_is_still_that_name(sentence, lemma):
    assert morphology.analyze_sentence(sentence)[-1]["lemma"] == lemma


@needs_camel
def test_the_telling_waw_is_tried_back_only_on_a_name_the_book_lists(monkeypatch):
    asked = []
    ranked = morphology._ranked
    monkeypatch.setattr(morphology, "_ranked", lambda spelled, *rest: asked.append(spelled[0]) or ranked(spelled, *rest))
    morphology._name_in_nasb("زَيْدًا")
    assert asked == ["زَيْد"]  # no زَيْدو: only عمرو is written with a و it drops in nasb
    amr = morphology.pick(["ضَرَبَ", "زَيْدٌ", "عَمْرًا"])[2]
    assert (amr["diac"], amr["atbtok"]) == ("عَمْرًا", "عَمْرًا")  # read with its و, written without
