"""A recorded ayah's cards: the treebank names each word (vowelled, tarkeeb_store's shape) and
leaves its case to the card, so the name alone must say what a built word or an unread vowel is."""
import pytest

from backend.services.nahw import iraab
from backend.services.nahw.book import reason, teacher_rules
from backend.services.sarf import morphology


def recorded(sentence: str, *names: str) -> list[dict]:
    return iraab.cards(morphology.analyze_sentence(sentence), [{"role": name, "case": None} for name in names])


def test_a_question_word_named_mubtada_is_built_in_the_place_of_raf():
    # وَمَا أَدْرَاكَ: a question noun keeps one ending whatever its job
    card = recorded("وَمَا يَوْمُ ٱلدِّينِ", "مُبْتَدَأٌ", "خَبَرٌ", "مُضَافٌ إِلَيْهِ")[0]
    assert (card["type"], card["case"]) == ("ism", "mabni")
    assert card["reason"].startswith("مبني في محل رفع")


def test_a_word_whose_vowel_is_not_read_takes_its_names_case():
    # ٱلدِّينِ: CAMeL reads no case on it; مضاف إليه says جر
    card = recorded("وَمَا يَوْمُ ٱلدِّينِ", "مُبْتَدَأٌ", "خَبَرٌ", "مُضَافٌ إِلَيْهِ")[-1]
    assert (card["case"], card["sign"]) == ("jarr", "كسرة")


def test_a_word_whose_vowel_is_read_keeps_it():
    card = recorded("وَمَا يَوْمُ ٱلدِّينِ", "مُبْتَدَأٌ", "خَبَرٌ", "مُضَافٌ إِلَيْهِ")[1]
    assert (card["case"], card["sign"]) == ("raf'", "ضمة")


def test_a_noun_the_treebank_names_a_particle_is_a_particle_built_on_its_own_vowel():
    # لَعَلَّهُ: built on لعلّ's fatha, not the ضمة of the pronoun on it
    card = recorded("لَعَلَّهُ يَزَّكَّىٰ", "حَرْفٌ مُشَبَّهٌ بِالْفِعْلِ", "فِعْلٌ")[0]
    assert (card["type"], card["case"], card["sign"]) == ("harf", "mabni", "مبني على الفتح")
    assert card["reason"] == teacher_rules()["case_said"]["particle"].format(role="حرف مشبه بالفعل")


@pytest.mark.parametrize("written", ["وَمَآ", "عَلَىٰ"])
def test_a_long_letter_with_only_a_reciters_mark_is_built_on_the_sukun(written):
    # the madda on مَآ and the small alef on عَلَىٰ are no vowel
    card = recorded(f"{written} يَوْمُ", "مُبْتَدَأٌ" if written == "وَمَآ" else "حَرْفُ جَرٍّ", "خَبَرٌ")[0]
    assert card["sign"] == "مبني على السكون"


def test_a_past_verbs_reason_keeps_the_books_rule():
    # فعل ماضٍ is the book's own name, tanween and all
    assert "القاعدة" in reason("فعل ماضٍ")
