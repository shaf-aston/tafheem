"""ما read by what stands around it, and the باء زائدة after كفى and ليس (data: particle_tree, closed_words extra_ba).
The sentences are not the hadith the rules were drawn from."""
from __future__ import annotations

import pytest

from backend.services.nahw import iraab
from tests.nahw_helpers import needs_parser, tree_roles

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
                                            ("كَفَى بِالْمَرْءِ إِثْمًا أَنْ يُضَيِّعَ", "بِالْمَرْءِ"),
                                            # a place with ال after ليس is its khabar said first, a plain jar-majrur
                                            ("لَيْسَ بِالْبَيْتِ أَحَدٌ", "بِالْبَيْتِ")])
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
    # a describing word with ال keeps its measure under the باء: البخيل is فعيل, العالم فاعل
    ("لَسْتُ بِالْبَخِيلِ", "بِالْبَخِيلِ", "خبر ليس"),
    ("لَسْتُ بِالْعَالِمِ", "بِالْعَالِمِ", "خبر ليس"),
    ("أَلَسْتُ بِرَبِّكُمْ", "بِرَبِّكُمْ", "خبر ليس"),
])
def test_the_khabar_of_ma_and_laysa_behind_an_extra_ba(sentence, word, role):
    found = card(sentence, word)
    assert (found.get("name") or found["role"]) == role and "منصوب محلًا" in found["reason"] and "زائد" in found["reason"]


@pytest.mark.parametrize("sentence, word, role", [("مَا زَيْدٌ بِالْبَيْتِ", "بِالْبَيْتِ", "مجرور"),
                                                  ("مَا زَيْدٌ كَأَسَدٍ", "كَأَسَدٍ", "مجرور"),  # the كاف is no extra باء
                                                  ("مَا أَنْتَ إِلَّا بَشَرٌ", "أَنْتَ", "مبتدأ"),
                                                  ("مَا أَحْسَنَ زَيْدًا", "زَيْدًا", "مفعول به"),
                                                  # a name in jarr by its fatha after a مضاف is no khabar in nasb
                                                  ("مَا عِقَابُ إِبْرَاهِيمَ", "إِبْرَاهِيمَ", "مضاف إليه"),
                                                  ("مَا ابْنُ زَيْدٍ قَائِمًا", "قَائِمًا", "خبر كان")])
def test_ma_governs_nothing_without_its_khabar(sentence, word, role):
    assert card(sentence, word)["role"] == role


@pytest.mark.parametrize("sentence, word", [("إِنَّ هَذَا لَسِحْرٌ", "لَسِحْرٌ"), ("إِنَّ اللَّهَ لَغَفُورٌ", "لَغَفُورٌ")])
def test_the_word_under_an_emphasis_lam_is_the_khabar_of_inna(sentence, word):
    assert card(sentence, word)["role"] == "خبر إن"


def test_a_lam_the_sentence_rests_on_leaves_its_word_the_mubtada():
    # لَزَيْدٌ قَائِمٌ: the لام heads the sentence and took no other word's place
    assert card("لَزَيْدٌ قَائِمٌ", "لَزَيْدٌ")["role"] == "مبتدأ"


@pytest.mark.parametrize("sentence, word, role", [
    # after a negation or هل, a مِن before an indefinite noun is زائدة: the noun holds the place it stands in
    ("مَا لَكُمْ مِنْ إِلَهٍ غَيْرُهُ", "إِلَهٍ", "مبتدأ مؤخر"),
    ("مَا فِي الدَّارِ مِنْ رَجُلٍ", "رَجُلٍ", "مبتدأ مؤخر"),
    ("مَا عِنْدَنَا مِنْ طَعَامٍ", "طَعَامٍ", "مبتدأ مؤخر"),
    ("هَلْ مِنْ خَالِقٍ غَيْرُ اللَّهِ", "خَالِقٍ", "مبتدأ"),
    ("هَلْ مِنْ مَزِيدٍ", "مَزِيدٍ", "مبتدأ"),
    ("مَا جَاءَنَا مِنْ بَشِيرٍ", "بَشِيرٍ", "فاعل"),
    ("مَا أَتَاهُمْ مِنْ نَذِيرٍ", "نَذِيرٍ", "فاعل"),  # a verb of coming: what comes is its doer
    ("مَا لِي مِنْ صَدِيقٍ فِي الْمَدِينَةِ", "صَدِيقٍ", "مبتدأ مؤخر"),  # a jar-majrur after it changes nothing
    ("وَمَا تَسْقُطُ مِنْ وَرَقَةٍ إِلَّا يَعْلَمُهَا", "وَرَقَةٍ", "فاعل"),  # a verb of coming or falling, no object said
    # كان and its sisters say their اسم there; ليس is the negation itself
    ("مَا كَانَ لَهُ مِنْ وَلِيٍّ", "وَلِيٍّ", "اسم كان"),
    ("لَيْسَ لِي مِنْ مَالٍ", "مَالٍ", "اسم ليس"),
    # a مبتدأ before the verb with a pronoun on it going back: the noun after مِن is still the doer
    ("زَيْدٌ مَا جَاءَهُ مِنْ أَحَدٍ", "أَحَدٍ", "فاعل"),
    # إنْ with an إلا after it negates, a verb right after it or not
    ("إِنْ يَأْتِيهِمْ مِنْ رَسُولٍ إِلَّا كَانُوا بِهِ يَسْتَهْزِئُونَ", "رَسُولٍ", "فاعل"),
])
def test_a_noun_after_an_extra_min_holds_its_place(sentence, word, role):
    found = card(sentence, word)
    assert (found.get("name") or found["role"]) == role and found["case"] == "jarr" and "مرفوع محلًا" in found["reason"] \
        and "زائد" in found["reason"]


@pytest.mark.parametrize("sentence, word", [
    # a verb taking an object, its doer said and its object not: the noun after مِن is that object
    ("مَا اتَّخَذَ اللَّهُ مِنْ وَلَدٍ", "وَلَدٍ"), ("مَا وَجَدْتُ مِنْ أَحَدٍ", "أَحَدٍ"),
])
def test_a_noun_after_an_extra_min_holds_the_object_place(sentence, word):
    found = card(sentence, word)
    assert found["role"] == "مفعول به" and found["case"] == "jarr" and "منصوب محلًا" in found["reason"]


@pytest.mark.parametrize("sentence, word", [
    ("لَمْ يَخْرُجْ مِنْ بَيْتٍ", "بَيْتٍ"), ("أَكَلْتُ مِنْ طَعَامٍ", "طَعَامٍ"),
    # any verb but one of coming, its object said, keeps its doer hidden: the مِن is its own
    ("مَا حَذَّرَنِي مِنْ خَطَرٍ", "خَطَرٍ"), ("لَمْ يُخْرِجْهُ مِنْ بَيْتٍ", "بَيْتٍ"),
    # the negation or هل over another verb's clause, or a relative's, does not reach the مِن
    ("لَا أَعْرِفُ مَا فِي الدَّارِ مِنْ مَتَاعٍ", "مَتَاعٍ"), ("هَلْ تَعْلَمُ مَا عِنْدَهُ مِنْ مَالٍ", "مَالٍ"),
    # كان or ليس with its اسم said: the مِن is its own
    ("لَيْسَ زَيْدٌ مِنْ أَهْلِهَا", "أَهْلِهَا"), ("مَا كَانَ زَيْدٌ مِنْ بَلَدٍ بَعِيدٍ", "بَلَدٍ"),
    # its hidden doer goes back to the مبتدأ the verb tells of
    ("زَيْدٌ لَمْ يَكُنْ مِنْ قَرْيَةٍ", "قَرْيَةٍ"),
    # a built word or adverb after it takes no case of its own: never a زائدة مِن's noun
    ("لَمْ يَأْتِ مِنْ قَبْلُ", "قَبْلُ"), ("لَمْ يَأْتِ مِنْ هُنَاكَ", "هُنَاكَ"),
    # إنْ the شرط is no negation
    ("إِنْ جَاءَكَ مِنْ رَجُلٍ فَأَكْرِمْهُ", "رَجُلٍ"),
    # a verb of coming or taking whose doer is said: مِن is its own, where from
    ("مَا نَزَلَ مِنْ سَمَاءٍ مَطَرٌ", "سَمَاءٍ"), ("مَا أَخَذْتُ مِنْ صَدِيقٍ", "صَدِيقٍ"), ("مَا سَمِعْتُ مِنْ شَيْخٍ", "شَيْخٍ"),
])
def test_a_min_with_no_negation_or_a_verb_it_hangs_on_stays_a_plain_jar(sentence, word):
    assert card(sentence, word)["role"] == "مجرور"


@pytest.mark.parametrize("sentence, word", [
    # the noun after a زائدة مِن is in raf' by its place, and its صفة may wear that raf' (هل من خالقٍ غيرُ الله)
    ("هَلْ مِنْ خَالِقٍ غَيْرُ اللَّهِ", "غَيْرُ"),
    ("مَا لَكُمْ مِنْ إِلَهٍ غَيْرُهُ", "غَيْرُهُ"),
    ("مَا فِي الدَّارِ مِنْ رَجُلٍ غَيْرُكَ", "غَيْرُكَ"),
    # siblings: or the jarr it wears; after a plain مِن the jarr only
    ("مَا جَاءَنَا مِنْ رَجُلٍ كَرِيمٍ", "كَرِيمٍ"),
    ("أَكَلْتُ مِنْ طَعَامٍ طَيِّبٍ", "طَيِّبٍ"),
])
def test_the_sifa_of_a_noun_behind_an_extra_min_wears_either_case(sentence, word):
    assert card(sentence, word)["role"] == "صفة"


@pytest.mark.parametrize("sentence, roles", [
    # a زائد letter is no unit of its own: its noun stands where the letter stands, the doer of the verb (no hidden
    # هو), the مبتدأ said last, or the khabar of ليس; nothing else is drawn as the khabar
    ("مَا جَاءَنَا مِنْ بَشِيرٍ", ["ما النافية", "فعل", "حرف جر", "فاعل"]),
    ("كَفَى بِاللَّهِ وَكِيلًا", ["فعل", "حرف جر", "فاعل", "تمييز"]),
    ("مَا فِي الدَّارِ مِنْ رَجُلٍ", ["ما النافية", "خبر مقدم", "حرف جر", "مجرور", "حرف جر", "مبتدأ مؤخر"]),
    ("هَلْ مِنْ مَزِيدٍ", ["حرف", "حرف جر", "مبتدأ"]),
    ("لَيْسَ زَيْدٌ بِقَائِمٍ", ["فعل ناقص", "اسم ليس", "حرف جر", "خبر ليس"]),
    # sibling: a plain jar after ليس is its khabar said first
    ("لَيْسَ بِالْبَيْتِ أَحَدٌ", ["فعل ناقص", "خبر ليس", "حرف جر", "مجرور", "اسم ليس"]),
])
def test_the_tree_stands_the_noun_behind_a_zaid_letter_in_its_place(sentence, roles):
    assert tree_roles(iraab.analyze(sentence)["tree"]["tree"]) == roles


@pytest.mark.parametrize("sentence, verb, hidden", [
    # the noun behind the زائد letter is the verb's doer, so no hidden هو is told of
    ("مَا جَاءَنَا مِنْ بَشِيرٍ", "جَاءَنَا", False),
    ("كَفَى بِاللَّهِ وَكِيلًا", "كَفَى", False),
    # sibling: with no noun after it, the doer is hidden
    ("مَا جَاءَ", "جَاءَ", True),
])
def test_a_verb_whose_doer_is_behind_a_zaid_letter_hides_none(sentence, verb, hidden):
    assert ("مستتر" in card(sentence, verb)["reason"]) is hidden


@pytest.mark.parametrize("sentence, said", [
    # ما then a place then a noun with a صفة of its own: the noun is a thing named, the مبتدأ; ما negates
    ("مَا لَهُ عَامِلٌ آخَرُ", "ما النافية"),
    ("مَا عِنْدَنَا كَاتِبٌ مَاهِرٌ", "ما النافية"),
    # sibling: an elative compares what ما is to something, so is told of it (ما عند الله خيرٌ)
    ("مَا عِنْدَ اللَّهِ خَيْرٌ كَثِيرٌ", "مبتدأ"),
])
def test_ma_before_a_described_noun_negates(sentence, said):
    found = card(sentence, "مَا")
    assert (found.get("name") or found["role"]) == said


def test_a_verb_whose_hamza_sits_on_waw_before_its_pronoun_has_its_doer():
    # يَقْرَؤُهُ: the dictionary writes it يقرأه only; read so, مَن is its doer, not a مبتدأ of its own
    assert card("الْكِتَابُ يَقْرَؤُهُ مَنْ يُحِبُّ الْعِلْمَ", "مَنْ")["role"] == "فاعل"
    # sibling: أَقْرَؤُهُمْ is the elative's letters as much as the I-verb's, so it stays a noun, the doer
    roles = [w["role"] for w in iraab.analyze("يَؤُمُّ الْقَوْمَ أَقْرَؤُهُمْ لِكِتَابِ اللَّهِ")["words"]]
    assert roles[:3] == ["فعل", "مفعول به", "فاعل"]


def test_the_ma_that_works_as_laysa_is_named_a_negation_with_its_own_rule():
    # ما الحجازية is a particle: no ناقص (a verb's name), and its nouns are told its rule, not كان وأخواتها's
    assert card("مَا هَذَا بَشَرًا", "مَا")["reason"].startswith("حرف نفي")
    assert "ما الحجازية تعمل عمل ليس" in card("مَا هَذَا بَشَرًا", "بَشَرًا")["reason"]
    # sibling: ليس is a sister of كان and keeps the family's rule
    assert "كان وأخواتها" in card("لَيْسَ زَيْدٌ قَائِمًا", "قَائِمًا")["reason"]
