"""ما read by what stands around it, and the باء زائدة after كفى and ليس (data: particle_tree, closed_words extra_ba).
The sentences are not the hadith the rules were drawn from."""
from __future__ import annotations

import pytest

from backend.services.nahw import iraab
from tests.nahw_helpers import needs_parser

pytestmark = needs_parser


def card(sentence: str, word: str) -> dict:
    return next(w for w in iraab.analyze(sentence)["words"] if w["word"] == word)


@pytest.mark.parametrize("sentence", ["سَأَبْقَى هُنَا مَا لَمْ تَرْجِعْ", "لَا أَتْرُكُكَ مَا دُمْتُ حَيًّا"])
def test_ma_before_lam_or_dama_is_a_timed_masdar(sentence):
    assert "الظرفية" in (card(sentence, "مَا").get("name") or "")


@pytest.mark.parametrize("sentence, said", [
    ("مَا نَقَصَتْ صَدَقَةٌ مِنْ مَالٍ", "النافية"),   # a past verb after it: never in jazm
    ("مَا تَفْعَلُوا مِنْ خَيْرٍ يَعْلَمْهُ اللَّهُ", "شرط"),
    ("مَا أَصَابَكَ مِنْ حَسَنَةٍ فَمِنَ اللَّهِ", "شرط"),  # the ف answers it
])
def test_ma_at_the_start_is_read_by_what_follows(sentence, said):
    found = card(sentence, "مَا")
    assert said in (found.get("name") or found.get("role") or "") + (found.get("reason") or "")


@pytest.mark.parametrize("sentence, word, role, place", [
    ("لَيْسَ الطَّالِبُ بِكَسُولٍ", "بِكَسُولٍ", "خبر ليس", "منصوب محلًا"),
    ("أَلَيْسَ اللَّهُ بِكَافٍ عَبْدَهُ", "بِكَافٍ", "خبر ليس", "منصوب محلًا"),  # the parser hung the باء under its noun
    ("كَفَى بِالْمَوْتِ وَاعِظًا", "بِالْمَوْتِ", "فاعل", "مرفوع محلًا"),
])
def test_a_word_after_an_extra_ba_holds_its_place(sentence, word, role, place):
    found = card(sentence, word)
    assert (found.get("name") or found["role"]) == role and found["case"] == "jarr" and place in found["reason"] and "زائد" in found["reason"]


@pytest.mark.parametrize("sentence, word", [("مَرَرْتُ بِزَيْدٍ", "بِزَيْدٍ"),
                                            ("كَفَى بِالْمَرْءِ إِثْمًا أَنْ يُضَيِّعَ", "بِالْمَرْءِ")])
def test_a_plain_ba_or_one_with_another_doer_stays_majroor(sentence, word):
    assert card(sentence, word)["role"] == "مجرور"


@pytest.mark.parametrize("sentence, word", [("إِنَّمَا الْعِلْمُ بِالتَّعَلُّمِ", "إِنَّمَا"), ("كَأَنَّمَا يُسَاقُونَ إِلَى الْمَوْتِ", "كَأَنَّمَا")])
def test_ma_on_an_inna_sister_stops_its_work(sentence, word):
    assert card(sentence, word)["name"] == "كافة ومكفوفة"


def test_a_bare_inna_keeps_its_own_name():
    assert card("إِنَّ زَيْدًا قَائِمٌ", "إِنَّ")["name"] != "كافة ومكفوفة"


@pytest.mark.parametrize("sentence, word, role", [
    ("مَا اللَّهُ بِغَافِلٍ", "بِغَافِلٍ", "خبر ما"),
    ("وَمَا رَبُّكَ بِظَلَّامٍ لِلْعَبِيدِ", "بِظَلَّامٍ", "خبر ما"),
    ("مَا أَنْتَ بِمُؤْمِنٍ", "بِمُؤْمِنٍ", "خبر ما"),
    ("مَا أَنْتَ بِالْكَاذِبِ", "بِالْكَاذِبِ", "خبر ما"),  # a participle keeps its ال and is the khabar still
    ("لَسْتُ بِغَافِلٍ", "بِغَافِلٍ", "خبر ليس"),
    ("أَلَسْتُ بِرَبِّكُمْ", "بِرَبِّكُمْ", "خبر ليس"),
])
def test_the_khabar_of_ma_and_laysa_behind_an_extra_ba(sentence, word, role):
    found = card(sentence, word)
    assert (found.get("name") or found["role"]) == role and "منصوب محلًا" in found["reason"] and "زائد" in found["reason"]


@pytest.mark.parametrize("sentence, word, role", [("مَا زَيْدٌ بِالْبَيْتِ", "بِالْبَيْتِ", "مجرور"),
                                                  ("مَا زَيْدٌ كَأَسَدٍ", "كَأَسَدٍ", "مجرور"),  # the كاف is no extra باء
                                                  ("مَا أَنْتَ إِلَّا بَشَرٌ", "أَنْتَ", "مبتدأ"),
                                                  ("مَا أَحْسَنَ زَيْدًا", "زَيْدًا", "مفعول به")])
def test_ma_governs_nothing_without_its_khabar(sentence, word, role):
    assert card(sentence, word)["role"] == role


@pytest.mark.parametrize("sentence, word", [("إِنَّ هَذَا لَسِحْرٌ", "لَسِحْرٌ"), ("إِنَّ اللَّهَ لَغَفُورٌ", "لَغَفُورٌ")])
def test_the_word_under_an_emphasis_lam_is_the_khabar_of_inna(sentence, word):
    assert card(sentence, word)["role"] == "خبر إن"


def test_a_lam_the_sentence_rests_on_leaves_its_word_the_mubtada():
    # لَزَيْدٌ قَائِمٌ: the لام heads the sentence and took no other word's place
    assert card("لَزَيْدٌ قَائِمٌ", "لَزَيْدٌ")["role"] == "مبتدأ"
