"""A جار takes no جار after it: a لام written onto a حرف جر after إنّ is the لام of emphasis on
its khabar (Alfiyya: وبعد ذات الكسر تصحب الخبر لام ابتداء), not a second حرف جر, though the
dictionary never writes it so and reads لعلى as لِعَلِيّ or a verb."""
import pytest

from backend.services.sarf.morphology import _emphasis_lam
from tests.nahw_helpers import analyze, cards, needs_parser, tree_roles


def roles(sentence: str) -> list[str]:
    return [c["role"] for c in cards(sentence)]


@needs_parser
@pytest.mark.parametrize("sentence", ["وَإِنَّكَ لَعَلَى خُلُقٍ عَظِيمٍ", "وإنك لعلى خلق عظيم"])
def test_the_lam_on_a_harf_jarr_is_the_lam_of_emphasis(sentence):
    assert roles(sentence)[1:] == ["حرف جر", "مجرور", "صفة"]
    drawn = tree_roles(analyze(sentence)["tree"]["tree"])
    assert "لام التوكيد" in drawn and "خبر إن" in drawn and drawn.count("حرف جر") == 1


@needs_parser
@pytest.mark.parametrize("sentence", ["إِنَّهُ لَمِنَ الصَّالِحِينَ", "إِنَّ زَيْدًا لَفِي الدَّارِ"])
def test_after_the_lam_the_preposition_governs_its_noun(sentence):
    assert roles(sentence)[-2:] == ["حرف جر", "مجرور"]


@needs_parser
def test_a_verb_spelled_with_the_same_letters_stays_a_verb():
    assert roles("إِنَّ اللَّهَ لَعَنَ الْكَافِرِينَ")[2] == "فعل"


@needs_parser
def test_without_inna_a_lam_with_kasra_is_the_jarr_lam():
    assert roles("لِعَلِيٍّ كِتَابٌ") == ["مجرور", "مبتدأ"]


@needs_parser
@pytest.mark.parametrize("sentence", ["وَاللَّهِ لَعَلَى الْحَقِّ أَنْتَ", "لَعَلَى الْبَابِ رَجُلٌ"])
def test_a_typed_fatha_makes_it_the_lam_of_emphasis_without_inna(sentence):
    words = cards(sentence)
    lam = next(i for i, c in enumerate(words) if c["word"].startswith("لَعَلَى"))
    assert [c["role"] for c in words[lam:lam + 2]] == ["حرف جر", "مجرور"]


@needs_parser
def test_a_lam_on_a_pronoun_is_the_jarr_lam():
    assert roles("إِنَّ لَهُمْ أَجْرًا") == ["حرف", "حرف جر", "اسم إن"]


@needs_parser
def test_bare_lam_on_man_without_inna_is_the_jarr_lam():
    assert roles("لمن تكتب") == ["مجرور", "فعل"]


@needs_parser
def test_a_typed_kasra_keeps_the_jarr_lam():
    assert roles("لِمَنْ تَكْتُبُ") == ["مجرور", "فعل"]


@needs_parser
def test_bare_letters_without_inna_are_the_lam_of_emphasis_too():
    assert roles("لفي الدار رجل") == ["حرف جر", "مجرور", "مبتدأ"]


@pytest.mark.parametrize("typed", ["لِمَنْ", "لَعُلَى", "لَكَ", "لَ", ""])
def test_no_lam_of_emphasis_against_a_typed_vowel_or_onto_no_particle(typed):
    assert _emphasis_lam(typed) is None


def test_a_lam_with_a_fatha_on_a_pronoun_the_dictionary_never_writes_is_the_lam_of_emphasis():
    assert _emphasis_lam("لَأَنْتُمْ") is not None


@needs_parser
@pytest.mark.parametrize("sentence, expected", [
    ("لَزَيْدٌ قَائِمٌ", ["مبتدأ", "خبر"]),
    ("لَهُوَ الْحَقُّ", ["مبتدأ", "خبر"]),
    ("وَلَلْآخِرَةُ خَيْرٌ لَكَ مِنَ الْأُولَى", ["مبتدأ", "خبر", "حرف جر", "حرف جر", "مجرور"]),
    # the parser hangs the word with the لام as the صفة of the khabar after it: لام الابتداء heads the sentence
    ("لَزَيْدٌ أَفْضَلُ مِنْ عَمْرٍو", ["مبتدأ", "خبر", "حرف جر", "مجرور"]),
    ("لَأَنْتُمْ أَشَدُّ رَهْبَةً", ["مبتدأ", "خبر"]),
])
def test_the_lam_of_emphasis_on_a_noun_leaves_it_the_mubtada(sentence, expected):
    assert roles(sentence)[:len(expected)] == expected


@needs_parser
@pytest.mark.parametrize("sentence", ["لَكَ الْحَمْدُ", "لَهُ الْمُلْكُ"])
def test_a_lam_on_a_pronoun_heading_the_sentence_keeps_its_jarr(sentence):
    assert roles(sentence) == ["حرف جر", "مبتدأ"]
