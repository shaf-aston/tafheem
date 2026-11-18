"""A nominal sentence inside another (الجملة الاسمية خبرًا أو صلة): each rule held by its sentence and by a
sibling the same rule must leave alone."""
import pytest

from backend.services.sarf.morphology import pick
from backend.services.text.harakat import vowel_agreement
from tests.nahw_helpers import card, needs_parser


def role(sentence: str, word: str) -> str:
    said = card(sentence, word)
    return said.get("name") or said["role"]


@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    # the last word, told of the noun before the relative, is its khabar once the صلة has its own (الكلام ما أفاد)
    ("الرَّجُلُ الَّذِي أَبُوهُ عَالِمٌ كَرِيمٌ", "كَرِيمٌ", "خبر"),
    ("زَيْدٌ الَّذِي أُمُّهُ كَرِيمَةٌ نَاجِحٌ", "نَاجِحٌ", "خبر"),
    ("زَيْدٌ الَّذِي أُمُّهُ كَرِيمَةٌ وَأَخُوهُ عَالِمٌ نَاجِحٌ", "نَاجِحٌ", "خبر"),
    ("الطَّالِبُ الَّذِي يَجْتَهِدُ نَاجِحٌ", "نَاجِحٌ", "خبر"),
    # the khabar wears the الذي's gender and number: men's plural, and a plural not of people's feminine singular
    ("الطُّلَّابُ الَّذِينَ أَبُوهُمْ عَالِمٌ مُجْتَهِدُونَ", "الطُّلَّابُ", "مبتدأ"),
    ("الْكُتُبُ الَّتِي مُؤَلِّفُهَا عَالِمٌ مُفِيدَةٌ", "الْكُتُبُ", "مبتدأ"),
    # siblings: after a verb the noun is no مبتدأ, so the word describes the khabar inside the صلة
    ("جَاءَ الَّذِي أَبُوهُ رَجُلٌ كَرِيمٌ", "كَرِيمٌ", "صفة"),
    ("جَاءَ الَّذِي أَبُوهُ رَجُلٌ كَرِيمٌ", "الَّذِي", "فاعل"),
    ("رَأَيْتُ الَّذِي أَبُوهُ عَالِمٌ كَرِيمًا", "الَّذِي", "مفعول به"),
    ("جَاءَ الرَّجُلُ الَّذِي أَخُوهُ طَبِيبٌ مَاهِرٌ", "الرَّجُلُ", "فاعل"),
    # أُمُّهُ is a noun, never the particle أَمْ its letters spell
    ("زَيْدٌ الَّذِي أُمُّهُ كَرِيمَةٌ نَاجِحٌ", "أُمُّهُ", "مبتدأ"),
])
def test_the_word_after_a_whole_silah_is_the_khabar(sentence, word, said):
    assert role(sentence, word) == said


@needs_parser
def test_a_word_that_disagrees_with_the_noun_stays_in_the_silah():
    """الرَّجُلُ ... كَرِيمَةٌ: a khabar agrees with its مبتدأ, so the feminine word is told of أمه, never of الرجل."""
    assert role("الرَّجُلُ الَّذِي أُمُّهُ عَالِمَةٌ كَرِيمَةٌ", "الرَّجُلُ") != "مبتدأ"
    # nor a singular after a plural الذين: كَرِيمٌ describes the word inside the صلة (the khabar would be كِرَامٌ)
    assert role("الطُّلَّابُ الَّذِينَ أَبُوهُمْ عَالِمٌ كَرِيمٌ", "الطُّلَّابُ") != "مبتدأ"
    # nor is a word in nasb, which no مبتدأ's khabar takes: it is the حال
    assert role("الرَّجُلُ الَّذِي أَبُوهُ عَالِمٌ كَرِيمًا", "كَرِيمًا") == "حال"
    # nor a word describing a doer inside a verb's صلة: that صلة has no khabar of its own
    assert role("الْكِتَابُ الَّذِي يَقْرَؤُهُ الطَّالِبُ الْمُجْتَهِدُ", "الْمُجْتَهِدُ") == "صفة"


@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    # a noun before a verb is no doer of it: the noun opens the verb's sentence as its مبتدأ (Tasheel 1.4.4 p11)
    ("زَيْدٌ أَبُوهُ يَكْتُبُ", "أَبُوهُ", "مبتدأ"),
    ("الطَّالِبُ كِتَابَهُ يَقْرَأُ", "الطَّالِبُ", "مبتدأ"),
    ("جَاءَ الَّذِي أَبُوهُ يَكْتُبُ", "أَبُوهُ", "مبتدأ"),
    # siblings: a doer after its verb, and a بدل after the doer, stay as they are
    ("زَيْدٌ يَكْتُبُ أَبُوهُ", "أَبُوهُ", "فاعل"),
    ("أَعْجَبَنِي زَيْدٌ عِلْمُهُ", "عِلْمُهُ", "بدل"),
])
def test_a_noun_before_its_verb_opens_a_sentence(sentence, word, said):
    assert role(sentence, word) == said


@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    # a word with ال straight after a known subject, in its case, is its صفة, not a second subject
    ("إِنَّمَا زَيْدٌ الْكَرِيمُ قَائِمٌ", "الْكَرِيمُ", "صفة"),
    ("إِنَّمَا زَيْدٌ الْكَرِيمُ قَائِمٌ", "قَائِمٌ", "خبر"),
    # sibling: an indefinite word after the subject is its khabar
    ("زَيْدٌ كَرِيمٌ", "كَرِيمٌ", "خبر"),
    # a وصف after a jar is told of the مبتدأ, the jar hung on it: no مبتدأ مؤخر (زيدٌ في بيته نائمٌ)
    ("زَيْدٌ فِي بَيْتِهِ نَائِمٌ", "نَائِمٌ", "خبر"),
    ("زَيْدٌ عِنْدَهُ كِتَابٌ", "كِتَابٌ", "مبتدأ مؤخر"),
])
def test_a_definite_word_after_the_subject_describes_it(sentence, word, said):
    assert role(sentence, word) == said


@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    # a pronoun written onto a noun is its مضاف إليه, so أبوه is one مبتدأ (المضاف إلى معرفة, Tasheel V1 p21)
    ("جَاءَ الَّذِي أَبُوهُ قَائِمٌ", "أَبُوهُ", "مبتدأ"),
    ("جَاءَ الَّذِي أَبُوهُ قَائِمٌ", "قَائِمٌ", "خبر"),
    ("كِتَابُكَ جَدِيدٌ", "كِتَابُكَ", "مبتدأ"),
    # sibling: a verb the parser may take for a noun keeps its own reading
    ("يَا سُعَادُ ارْفَعِي صَوْتَكِ", "ارْفَعِي", "فعل أمر"),
    ("يَا سُعَادُ ارْفَعِي صَوْتَكِ", "صَوْتَكِ", "مفعول به"),
    # a منقوص with tanween shows no case of its own: the place it stands in decides
    ("الطَّالِبُ مُجْتَهِدٌ وَأَبُوهُ رَاضٍ", "رَاضٍ", "خبر"),
    ("رَأَيْتُ قَاضِيًا", "قَاضِيًا", "مفعول به"),
    ("نَاصِيَتِي بِيَدِكَ، مَاضٍ فِيَّ حُكْمُكَ", "مَاضٍ", "خبر"),
    ("جَاءَ رَجُلٌ قَاضٍ", "قَاضٍ", "صفة"),
    # after a verb it is no jarr, and its nasb would keep the ya: so it is the raf' doer, beside an object or a second one
    ("أَعْطَى زَيْدًا قَاضٍ", "قَاضٍ", "فاعل"),
    ("رَأَى الرَّجُلَ رَاعٍ", "رَاعٍ", "فاعل"),
    ("جَعَلَ الْحُكْمَ قَاضٍ", "قَاضٍ", "فاعل"),
    ("رَأَى الرَّجُلَ رَاعٍ", "الرَّجُلَ", "مفعول به"),
    ("مَرَرْتُ بِقَاضٍ", "بِقَاضٍ", "مجرور"),
    # a و on a word typed in raf' joins; on a word in jarr it may be the oath's
    ("إِنَّ الَّذِي عِلْمُهُ نَافِعٌ وَخُلُقُهُ حَسَنٌ مَحْبُوبٌ", "حَسَنٌ", "خبر"),
    ("إِنَّ الَّذِي عِلْمُهُ نَافِعٌ وَخُلُقُهُ حَسَنٌ مَحْبُوبٌ", "مَحْبُوبٌ", "خبر إن"),
    ("وَاللَّهِ إِنَّ زَيْدًا لَقَائِمٌ", "وَاللَّهِ", "مجرور"),
])
def test_the_words_inside_a_nested_sentence(sentence, word, said):
    assert role(sentence, word) == said


@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    # two known nouns: only their order tells them apart, so the first said is the مبتدأ (after إنما too)
    ("إِنَّمَا زَيْدٌ الْقَائِمُ", "زَيْدٌ", "مبتدأ"),
    ("إِنَّمَا زَيْدٌ الْقَائِمُ", "الْقَائِمُ", "خبر"),
    ("إِنَّمَا وَلِيُّكُمُ اللَّهُ", "وَلِيُّكُمُ", "مبتدأ"),
    ("إِنَّمَا وَلِيُّكُمُ اللَّهُ", "اللَّهُ", "خبر"),
    ("إِنَّمَا أَخُوكَ زَيْدٌ", "زَيْدٌ", "خبر"),
    # siblings: a known word said after its مبتدأ is in order already; ما that may be نافية is no noun to weigh
    ("الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ", "الْمُسْلِمُ", "مبتدأ"),
    ("الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ", "مَنْ", "خبر"),
    ("مَا جَزَاؤُهُ إِلَّا سَجْنُهُ", "سَجْنُهُ", "خبر"),
    # a khabar tells of one مبتدأ: a second subject hung on it is no pair with it
    ("أَنَا سَيِّدُ وَلَدِ آدَمَ يَوْمَ الْقِيَامَةِ، وَأَوَّلُ مَنْ يَنْشَقُّ عَنْهُ الْقَبْرُ", "سَيِّدُ", "خبر"),
    # a known word with ال after a known noun describes it (مركب وصفي), alone or with more said; إنّ still works
    ("زَيْدٌ الْقَائِمُ", "الْقَائِمُ", "صفة"),
    ("زَيْدٌ الْكَرِيمُ عَالِمٌ", "الْكَرِيمُ", "صفة"),
    ("هَذَا زَيْدٌ الْكَرِيمُ", "الْكَرِيمُ", "صفة"),
    ("جَاءَ زَيْدٌ الْكَرِيمُ", "الْكَرِيمُ", "صفة"),
    ("إِنَّ زَيْدًا أَخُوكَ", "أَخُوكَ", "خبر إن"),
    # a word that works as a verb keeps its doer; a noun typed in nasb is no مبتدأ
    ("إِنَّمَا الْقَائِمُ أَبُوهُ", "أَبُوهُ", "فاعل"),
    ("الصَّلَاةَ الْجَامِعَةَ", "الْجَامِعَةَ", "صفة"),
    # an indefinite noun said first is the khabar said first (تَمِيمِيٌّ أَنَا), or told of an unwritten مبتدأ
    ("تَمِيمِيٌّ أَنَا", "أَنَا", "مبتدأ"),
    ("ذَهَبٌ خَاتَمُكَ", "خَاتَمُكَ", "مبتدأ"),
    # a ظرف said first is the khabar, whatever it is added to
    ("أَمَامَكَ الْمَسْجِدُ", "الْمَسْجِدُ", "مبتدأ مؤخر"),
    ("رَجُلٌ كَرِيمٌ", "كَرِيمٌ", "صفة"),
    # the رابط of a sentence told of a noun is a third person's pronoun: أخوك is no مبتدأ of its own
    ("زَيْدٌ أَبُوهُ عَالِمٌ", "أَبُوهُ", "مبتدأ"),
    # a noun in nasb or jarr is no مبتدأ: a ظرف said first, or a verb's object said first
    ("غَدًا عِنْدَهُ امْتِحَانٌ", "غَدًا", "مفعول فيه"),
    ("الْيَوْمَ أَبُوهُ مَرِيضٌ", "الْيَوْمَ", "مفعول فيه"),
    ("غَدًا أَخُوهُ يُسَافِرُ", "أَخُوهُ", "مبتدأ"),
    ("زَيْدًا أَبُوهُ يَضْرِبُ", "زَيْدًا", "مفعول به"),
    ("زَيْدٌ أَبُوهُ يَكْتُبُ", "أَبُوهُ", "مبتدأ"),
    # a توكيد follows its noun and tells nothing of its own: no مبتدأ
    ("زَيْدٌ نَفْسُهُ يَكْتُبُ", "نَفْسُهُ", "توكيد"),
    ("الطُّلَّابُ كُلُّهُمْ يَكْتُبُونَ", "كُلُّهُمْ", "توكيد"),
])
def test_two_known_nouns_the_first_said_is_the_mubtada(sentence, word, said):
    assert role(sentence, word) == said


@needs_parser
def test_a_sentence_told_of_a_noun_needs_a_third_person_pronoun():
    assert role("زَيْدٌ أَخُوكَ عَالِمٌ", "أَخُوكَ") != "مبتدأ"


def _case(words: list[str], word: str) -> str | None:
    return next(r for w, r in zip(words, pick(words)) if w == word).get("cas")


def test_a_long_vowel_letter_carries_no_other_vowel():
    """أَبُوهُ: the و after a damma is that damma drawn long, so a reading that puts a fatha on it (أَبُوَهُ) contradicts
    what was typed; the six nouns' raf' is the reading kept. Siblings: أَبَاهُ (nasb), فِيهِ (a long ي)."""
    assert vowel_agreement("أَبُوهُ", "أَبُوَهُ") is None
    assert vowel_agreement("أَبُوهُ", "أَبُوُهُ") is not None
    assert vowel_agreement("فِيهِ", "فِيهِ") is not None
    # a last letter may carry its own vowel: لِيَ, and a verb's nasb (لَنْ يَدْعُوَ)
    assert vowel_agreement("لِي", "لِيَ") is not None
    assert vowel_agreement("يَدْعُو", "يَدْعُوَ") is not None
    # a و inside the stem may be a consonant typed without its fatha: مُوَاطِن، مُوَظَّف، سُوَر
    assert vowel_agreement("مُواطِنٌ", "مُوَاطِنٌ") is not None
    assert vowel_agreement("مُوظَّفٌ", "مُوَظَّفٌ") is not None
    assert vowel_agreement("سُورٌ", "سُوَرٌ") is not None
    assert vowel_agreement("أَخُوكَ", "أَخُوَكَ") is None
    words = ["زَيْدٌ", "أَبُوهُ", "يَكْتُبُ"]
    assert _case(words, "أَبُوهُ") == "n"
    assert _case(["رَأَيْتُ", "أَبَاهُ"], "أَبَاهُ") == "a"


def test_a_verb_reading_that_adds_a_shadda_is_not_taken():
    """جَاءَ الَّذِي أَبُوهُ: the vowelled word has no shadda, so the verb أَبُّوهُ is not a better fit than the noun."""
    words = ["جَاءَ", "الَّذِي", "أَبُوهُ", "قَائِمٌ"]
    read = next(r for w, r in zip(words, pick(words)) if w == "أَبُوهُ")
    assert not read.get("pos", "").startswith("verb")
    assert next(r for w, r in zip(["الَّذِي", "يَكْتُبُ"], pick(["الَّذِي", "يَكْتُبُ"])) if w == "يَكْتُبُ")["pos"] == "verb"
