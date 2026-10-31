"""A noun phrase typed alone (a title, a label, an answer) is no sentence of its own: its head is
the khabar of a مبتدأ no one writes, هذا (بابُ الفاعلِ: هذا بابُ الفاعلِ). مِن after an indefinite
measure brings what it measures (كوبٌ من القهوة as كوبُ قهوةٍ), so it is not the khabar either."""
import pytest

from tests.nahw_helpers import analyze, cards, needs_parser


def roles(sentence: str) -> list[str]:
    return [c["role"] for c in cards(sentence)]


@needs_parser
@pytest.mark.parametrize("sentence, expected", [
    ("كِتَابُ الطَّالِبِ", ["خبر", "مضاف إليه"]),
    ("كتاب الطالب", ["خبر", "مضاف إليه"]),
    ("بَيْتٌ جَمِيلٌ", ["خبر", "صفة"]),
    ("بَابُ الْفَاعِلِ", ["خبر", "مضاف إليه"]),
    ("كُوبٌ كَبِيرٌ مِنَ الْقَهْوَةِ", ["خبر", "صفة", "حرف جر", "مجرور"]),
    ("كُوب كَبِير مِنَ الْقَهْوَة", ["خبر", "صفة", "حرف جر", "مجرور"]),
    ("رطل من عسل", ["خبر", "حرف جر", "مجرور"]),
])
def test_a_phrase_alone_is_the_khabar_of_an_unwritten_hadha(sentence, expected):
    assert roles(sentence) == expected
    tree = analyze(sentence)["tree"]
    assert tree["words"][0] == "هَذَا"
    assert "ثَابِتٌ" not in tree["words"]


@needs_parser
@pytest.mark.parametrize("sentence, expected", [
    ("زَيْدٌ قَائِمٌ", ["مبتدأ", "خبر"]),
    ("مُحَمَّدٌ رَسُولُ اللَّهِ", ["مبتدأ", "خبر", "مضاف إليه"]),
    ("شُكْرًا لَكَ", ["مفعول مطلق", "حرف جر"]),
])
def test_a_whole_sentence_keeps_its_own_mubtada(sentence, expected):
    assert roles(sentence) == expected
    assert analyze(sentence)["tree"]["words"][0] != "هَذَا"


@needs_parser
@pytest.mark.parametrize("sentence", ["زَيْدٌ فِي الدَّارِ", "رجل من القرية", "ثلاثة من الرجال", "الْحَمْدُ لِلَّهِ"])
def test_a_jar_after_a_noun_that_is_no_measure_still_hangs_on_thabit(sentence):
    assert roles(sentence)[0] == "مبتدأ"
    assert "ثَابِتٌ" in analyze(sentence)["tree"]["words"]
