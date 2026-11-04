"""Two readings the books settle by rule.

A وصف with ال after a definite noun, agreeing with it, is its صفة (الطالبُ المجتهدُ, Tasheel 3.10.1),
even when the parser tags it a noun; one that cannot agree (الدينُ النصيحةُ) is the khabar.
After لولا the noun is a مبتدأ whose khabar is always left out (Alfiyya: وبعد لولا غالبًا حذف الخبر
حتم): it is drawn hidden as موجود, محذوف وجوبًا."""
import pytest

from tests.nahw_helpers import analyze, cards, needs_parser


def roles(sentence: str) -> list[str]:
    return [c["role"] for c in cards(sentence)]


def leaves(node: dict) -> list[dict]:
    if "word" in node:
        return [node]
    return [leaf for kid in node.get("children", []) for leaf in leaves(kid)]


@needs_parser
@pytest.mark.parametrize("sentence", ["الطَّالِبُ الْمُجْتَهِدُ", "الطالب المجتهد", "الطَّالِبَةُ الْمُجْتَهِدَةُ", "الْكُتُبُ الْجَدِيدَةُ"])
def test_an_agreeing_wasf_after_a_definite_noun_is_its_sifah(sentence):
    assert roles(sentence) == ["خبر", "صفة"]  # the pair alone: the khabar of an unwritten هذا
    assert analyze(sentence)["tree"]["words"][0] == "هَذَا"


@needs_parser
@pytest.mark.parametrize("sentence, expected", [
    ("الدِّينُ النَّصِيحَةُ", ["مبتدأ", "خبر"]),  # a feminine word cannot describe a masculine one
    ("اللَّهُ الصَّمَدُ", ["مبتدأ", "خبر"]),  # no وصف's shape
    ("زَيْدٌ صَاحِبُ الْمَالِ", ["مبتدأ", "خبر", "مضاف إليه"]),  # made definite by its مضاف إليه
    ("الطَّالِبُ الْمُجْتَهِدُ نَاجِحٌ", ["مبتدأ", "صفة", "خبر"]),
])
def test_a_khabar_that_cannot_be_a_sifah_stays_the_khabar(sentence, expected):
    assert roles(sentence) == expected


@needs_parser
@pytest.mark.parametrize("sentence, noun", [
    ("لَوْلَا زَيْدٌ لَهَلَكَ عَمْرٌو", ["زَيْدٌ"]),
    ("لولا الله ما اهتدينا", ["الله"]),
    ("لَوْلَا رَحْمَةُ اللَّهِ لَهَلَكْنَا", ["رَحْمَةُ", "اللَّهِ"]),
])
def test_the_khabar_after_lawla_is_drawn_hidden(sentence, noun):
    assert roles(sentence)[1] == "مبتدأ"
    tree = analyze(sentence)["tree"]
    words = tree["words"]
    assert words[1:len(noun) + 2] == [*noun, "مَوْجُودٌ"]
    hidden = next(leaf for leaf in leaves(tree["tree"]) if words[leaf["word"]] == "مَوْجُودٌ")
    assert hidden["role"] == "خبر" and hidden["detail"] == "محذوف وجوبًا"


@needs_parser
def test_lawla_before_a_verb_urges_and_has_no_khabar():
    assert "مَوْجُودٌ" not in analyze("لَوْلَا تَسْتَغْفِرُونَ اللَّهَ")["tree"]["words"]
