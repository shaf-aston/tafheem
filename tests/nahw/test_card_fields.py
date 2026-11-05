"""What a card prints for a word (sign, case, reason, summary), per rule, on typed sentences.

Run: python -m pytest tests/nahw/test_card_fields.py
"""
from __future__ import annotations

import pytest
from backend.models.analyze import WordAnalysis
from backend.services.nahw import iraab
from backend.services.text.arabic_text import words
from backend.services.nahw.book import term_ar
from tests.nahw_helpers import analysed, cards, NADA, needs_parser, NOMINAL, VERBAL, _ATTENTION, _read, _role

pytestmark = needs_parser


# A card's reason must explain the role the card wears, whoever named it.
REASON_SENTENCES = ["مَتَى سَافَرَ الرَّجُلُ", "كُتِبَ الدَّرْسُ", "جاء محمد وعلي", "يا محمد اجلس",
                    "إِنَّ الطَّالِبَ مُجْتَهِدٌ", "كَتَبَ الطَّالِبُ الدَّرْسَ فِي الْبَيْتِ"]


def test_every_role_has_a_reason():
    from backend.services.nahw.book import teacher_rules
    from backend.services.nahw.syntax.naming import ROLES
    assert [role for role in ROLES if role not in teacher_rules()["reasons"]] == []


@pytest.mark.parametrize("sentence", REASON_SENTENCES)
def test_each_reason_explains_its_own_role(sentence: str):
    words = iraab.analyze(sentence)["words"]
    for word in words:
        role = word["role"]
        if word["type"] == "punc" or role == "–":
            continue
        assert role in word["reason"] or (role.startswith("فعل") and word["type"] == "fi'l"), (word["word"], role, word["reason"])


# The verb's card: a command by its typed shape, a present verb's case by its ending or the particle before it.
VERB_CARDS = [
    ("اُكْتُبْ الدَّرْسَ", 0, "mabni", "فعل أمر"),
    ("قُمْ يَا وَلَدُ", 0, "mabni", "فعل أمر"),
    ("لَمْ يَكْتُبْ الطَّالِبُ", 1, "jazm", "مجزوم"),
    ("لم يكتب الطالب", 1, "jazm", "مجزوم"),
    ("لن يذهب زيد", 1, "nasb", "منصوب"),
    ("يَكْتُبُ الطَّالِبُ", 0, "raf'", "مرفوع"),
    ("كَتَبَ الطَّالِبُ", 0, "mabni", "فعل ماضٍ"),  # nearest case: a past verb is untouched
    ("بِعْ الكِتَابَ", 0, "mabni", "فعل أمر"),      # CAMeL offers only the name بِع
    ("نَمْ مُبَكِّرًا", 0, "mabni", "فعل أمر"),     # and the parser's reading is the noun نَمّ
    ("أَكْرِمْ الضَّيْفَ", 0, "mabni", "فعل أمر"),   # Form IV, hamzat al-qat'
    ("أَقِمْ الصَّلَاةَ", 0, "mabni", "فعل أمر"),     # hollow Form IV: the middle letter is gone
    ("لَمْ أَقِمْ", 1, "jazm", "مجزوم"),             # nearest case: after لم it is a present verb
    ("أَحْمَدْ جَاءَ", 0, "raf'", "مرفوع"),         # a name paused on is no command
    ("لَمْ أَجْلِسْ", 1, "jazm", "مجزوم"),        # nearest case: the same shape after لم is a present verb
]


@pytest.mark.parametrize("sentence, index, case, said", VERB_CARDS)
def test_verb_card_case_and_reason_agree(sentence: str, index: int, case: str, said: str):
    word = iraab.analyze(sentence)["words"][index]
    assert (word["case"], said in word["reason"]) == (case, True), word


@pytest.mark.parametrize("sentence, sign, said", [
    ("قُومِي", "مبني على حذف النون", "و«ي» ضمير متصل مبني في محل رفع فاعل"),  # the ي is its doer, said once
    ("ارْفَعِي صَوْتَكِ", "مبني على حذف النون", "و«ي» ضمير متصل مبني في محل رفع فاعل"),
    ("اُكْتُبِي", "مبني على حذف النون", "وفاعله ضمير متصل (أنتِ)"),  # nearest case: the ي kept inside the verb
    ("أَكْرِمْنِي", "مبني على السكون", "و«ني» ضمير متصل مبني في محل نصب مفعول به"),  # nearest case: an object
])
def test_a_command_to_a_woman_is_built_on_dropping_the_nun(sentence: str, sign: str, said: str):
    verb = cards(sentence)[0]
    assert verb["sign"] == sign
    assert said in verb["reason"] and verb["reason"].count("فاعل") == 1  # one doer, said once


@pytest.mark.parametrize("sentence, sign", [
    ("اُكْتُبُوهُ", "مبني على حذف النون"),  # the plural's alef drops before a pronoun (Hamʿ V3 p514)
    ("اُكْتُبُوا", "مبني على حذف النون"),  # nearest case: no pronoun, the alef written
    ("ضَرَبُوهُ", "مبني على الضم"),
    ("رَمَوْهُ", "مبني على الضم"),
    ("ضَرَبُوا", "مبني على الضم"),  # nearest case: no pronoun
    ("ضَرَبَهُ", "مبني على الفتح"),  # nearest case: one doer, no plural's و
])
def test_a_verb_with_the_plurals_waw_before_a_pronoun(sentence: str, sign: str):
    assert cards(sentence)[0]["sign"] == sign


@pytest.mark.parametrize("sentence, verbal", [
    ("لَمْ يَكْتُبْ الطَّالِبُ", True), ("قَدْ نَجَحَ الطَّالِبُ", True), ("لَنْ يَذْهَبَ زَيْدٌ", True),
    ("إِنَّ الطَّالِبَ مُجْتَهِدٌ", False)])  # nearest case: a particle before a noun
def test_a_particle_before_the_verb_keeps_the_sentence_verbal(sentence: str, verbal: bool):
    summary = iraab.analyze(sentence)["summary"]
    assert (summary == term_ar("jumlah_filiyyah")) is verbal, summary


# One card field each, found by typing the sentence in (backend/scripts/nahw/analyze.py).
CARDS = [
    ("زَارَنَا صَدِيقِي أَمْسِ", 2, "sign", "مبني على الكسر"),  # a built ظرف says the vowel it is built on
    ("ذَهَبَ الطَّالِبُ إِلَى المَدْرَسَةِ", 2, "sign", "مبني على السكون"),  # a particle ending in a long letter
    ("إِنَّ اللهَ غَفُورٌ رَحِيمٌ", 0, "sign", "مبني على الفتح"),          # a particle says its vowel too
    ("اشْتَرَيْتُ عِشْرِينَ كِتَابًا", 1, "sign", "الياء، ملحق بجمع المذكر السالم"),  # a ten is only attached to the plural
    ("ظَنَنْتُ الامْتِحَانَ سَهْلًا", 1, "reason", "منصوب لأنه مفعول به أول. القاعدة: المفعول به منصوب"),
    ("ظَنَنْتُ الامْتِحَانَ سَهْلًا", 2, "reason", "منصوب لأنه مفعول به ثانٍ. القاعدة: المفعول به منصوب"),
    ("إِنَّ اللهَ غَفُورٌ رَحِيمٌ", 3, "reason", "مرفوع لأنه خبر ثانٍ لإن. القاعدة: إن وأخواتها ترفع الخبر"),
    # a pair of tools splits its work: the first إمّا sets out the choice, the second joins
    ("إِمَّا أَنْ تَذْهَبَ وَإِمَّا أَنْ تَبْقَى", 0, "reason", "حرف تفصيل"),
    ("إِمَّا أَنْ تَذْهَبَ وَإِمَّا أَنْ تَبْقَى", 3, "reason", "حرف عطف وتفصيل"),
    ("لَمَّا جَاءَ الْمَطَرُ فَرِحَ النَّاسُ", 0, "reason", "حرف وجود لوجود"),     # لمّا before a past verb joins nothing
    ("لَا تَأْكُلِ السَّمَكَ وَتَشْرَبَ اللَّبَنَ", 0, "reason", "لا الناهية"),  # jazm's sukun moved to kasra before ال
    ("مَكْرُ اللَّيْلِ خَطِيرٌ", 1, "reason", "والإضافة معنوية بمعنى «في»"),
    ("لَبِسْتُ خَاتَمَ ذَهَبٍ", 2, "reason", "والإضافة معنوية بمعنى «من»"),
    ("كِتَابُ الطَّالِبِ جَدِيدٌ", 1, "reason", "والإضافة معنوية بمعنى اللام"),
    ("أَنْتَ ضَارِبُ زَيْدٍ غَدًا", 2, "reason", "والإضافة لفظية غير محضة"),
    ("أَكَلْتُ الرَّغِيفَ نِصْفَهُ", 2, "reason", "بدل بعض من كل"),
    ("أَعْجَبَنِي زَيْدٌ عِلْمُهُ", 2, "reason", "بدل اشتمال"),
    ("جَاءَ أَخُوكَ زَيْدٌ", 2, "reason", "بدل كل من كل"),
    ("مَاذَا قَرَأْتَ؟ قَالَ الْقُرْآنَ", 0, "role", "مفعول به"),      # قال after the question is its reply, not قرأتَ's object
    ("جَلَسْتُ مَعَ النَّاسِ", 2, "role", "مضاف إليه"),        # the noun after a ظرف the parser drew as a preposition
    ("جَاءَ الْأَمِيرُ خَالِدٌ", 2, "role", "بدل"),             # an indefinite word after a noun with ال is no صفة
    ("قِفَا نَبْكِ", 0, "sign", "حذف النون"),                   # the dictionary's root قفو holds وقف's letters
    ("سَافَرْتُ طَلَبًا لِلْعِلْمِ", 1, "role", "مفعول لأجله"),   # a masdar giving the reason
    ("مَرَرْتُ بِإِبْرَاهِيمَ وَأَحْمَدَ", 2, "case", "jarr"),     # a diptote follower keeps its fatha in jarr
    ("اكْتُبَا الدَّرْسَ", 0, "sign", "حذف النون"),              # the dual command
    ("الدِّينُ النَّصِيحَةُ", 1, "role", "خبر"),           # nothing else is said of the mubtada
    ("الطُّهُورُ شَطْرُ الْإِيمَانِ", 1, "role", "خبر"),     # a plain noun made definite by its مضاف إليه names, not describes
    ("جَاءَ رَجُلٌ غَيْرُ خَالِدٍ", 2, "role", "صفة"),       # nearest case: a describing word stays a صفة
    ("اتَّقِ اللَّهَ حَيْثُمَا كُنْتَ", 2, "sign", "مبني على السكون"),  # a condition's place word is built, answer or none
    ("الكِتَابُ الجَدِيدُ مُفِيدٌ", 1, "role", "صفة"),       # nearest case: a khabar follows, so a صفة
    ("مَدْرَسَةُ الْبَلَدِ الْكَبِيرَةُ جَمِيلَةٌ", 2, "role", "صفة"),  # the مضاف's صفة, after its مضاف إليه
    ("الْيَدُ الْعُلْيَا خَيْرٌ", 1, "sign", "ضمة مقدرة"),    # a صفة wears its noun's case
    ("يَا عِبَادِي", 1, "case", "nasb"),                   # a مضاف منادى is منصوب
    ("لَنْ يَذْهَبَ أَخِي", 2, "role", "فاعل"),            # the kasra before ya al-mutakallim is no case
    ("يَا عَبْدَ اللهِ", 2, "role", "مضاف إليه"),
    ("هَذَا بَيْتٌ كَبِيرٌ", 1, "role", "خبر"),            # an indefinite noun after a pointer
    ("هَذَا البَيْتُ كَبِيرٌ", 2, "role", "خبر"),          # nearest case: with ال the khabar comes later
    ("كَانَ الجَوُّ بَارِدًا", 0, "reason", "فعل ماضٍ"),   # CAMeL calls كان a pseudo-verb
    ("ضُرِبَ اللِّصُّ", 0, "sign", "مبني على الفتح"),      # CAMeL calls ضُرِبَ a noun
    ("الطُّلَّابُ يَدْرُسُونَ فِي المَكْتَبَةِ", 1, "sign", "ثبوت النون"),
    ("لَنْ يَكْتُبُوا", 1, "sign", "حذف النون"),
    ("يَكْتُبُ الطَّالِبُ", 0, "sign", "ضمة"),             # nearest case: one of the five verbs it is not
    ("الطُّلَّابُ كَتَبُوا الدَّرْسَ", 1, "sign", "مبني على الضم"),
    ("كَتَبَتْ البِنْتُ الدَّرْسَ", 0, "sign", "مبني على الفتح"),  # تاء التأنيث
    ("كَتَبْتُ الدَّرْسَ", 0, "sign", "مبني على السكون"),
    ("جَاءَ الَّذِي نَجَحَ", 1, "reason", "مبني في محل رفع"),
    ("لَا تَكْذِبْ", 0, "reason", "لا الناهية"),
    ("لَا يَكْذِبُ المُؤْمِنُ", 0, "reason", "لا النافية"),
    ("كِتَابِي جَدِيدٌ", 0, "sign", "ضمة مقدرة على ما قبل ياء المتكلم"),
    ("قَرَأْتُ فِي كِتَابِي", 2, "sign", "كسرة مقدرة"),
    ("جَاءَ الفَتَى", 1, "sign", "ضمة مقدرة على الألف"),
    ("جَاءَ العَصَا", 1, "sign", "ضمة مقدرة على الألف"),
    ("جَاءَ القَاضِي", 1, "sign", "ضمة مقدرة على الياء"),
    ("مَرَرْتُ بِالقَاضِي", 1, "sign", "كسرة مقدرة على الياء"),
    ("رَأَيْتُ القَاضِيَ", 1, "sign", "فتحة"),            # the fatha shows on a manqus
    ("قَرَأْتُ كِتَابًا", 1, "sign", "فتحة"),             # nearest case: a tall alef whose root is strong
    ("رَأَيْتُ أَخِي", 1, "case", "nasb"),               # renamed by the parser, the case follows
    ("رَأَيْتُ الطَّالِبَيْنِ", 1, "sign", "الياء، مثنى"),  # and a dual keeps its kind of sign
    ("لَنْ يَكْتُبَا", 1, "sign", "حذف النون"),
    ("لَمْ تَكْتُبِي", 1, "sign", "حذف النون"),
    ("لَنْ يَمْشِيَ", 1, "sign", "فتحة"),                 # nearest case: the ي is the root's
    # signs found wrong by the hadith and rules sets (score_iraab --set hadith / rules)
    ("لَا تَسُبُّوا أَصْحَابِي", 1, "sign", "حذف النون"),     # the dropped nun after لا
    ("اِحْفَظُوا الدَّرْسَ", 0, "sign", "مبني على حذف النون"),
    # a sound feminine plural's kasra is its nasb, a diptote's fatha its jarr
    ("رَأَيْتُ الْمُعَلِّمَاتِ", 1, "case", "nasb"),
    ("رَأَيْتُ الْمُعَلِّمَاتِ", 1, "sign", "كسرة، نيابة عن الفتحة"),
    ("صَلَّيْتُ فِي مَسَاجِدَ كَثِيرَةٍ", 2, "case", "jarr"),
    ("مَرَرْتُ بِأَحْمَدَ", 1, "sign", "فتحة، نيابة عن الكسرة"),
    # ما الكافة stops إنّ working: a plain mubtada and khabar follow
    ("إِنَّمَا زَيْدٌ قَائِمٌ", 1, "role", "مبتدأ"),
    ("إِنَّمَا زَيْدٌ قَائِمٌ", 2, "role", "خبر"),
    # the governor named by its family
    ("كَانَ زَيْدٌ قَائِمًا", 0, "reason", "فعل ماضٍ ناقص"),
    ("إِنَّ اللَّهَ غَفُورٌ", 0, "reason", "حرف ناسخ مشبه بالفعل"),
    ("اِسْقِ الزَّرْعَ", 0, "sign", "مبني على حذف حرف العلة"),
    ("اتَّقِ اللَّهَ", 0, "sign", "مبني على حذف حرف العلة"),  # no present prefix, so a command
    ("لَمْ يَبْكِ الطِّفْلُ", 1, "sign", "حذف حرف العلة"),
    ("لَمْ يَدْعُ الرَّجُلُ رَبَّهُ", 1, "sign", "حذف حرف العلة"),  # the damma left is the stem's, not raf'
    ("لَمْ يَخْشَ الْعَبْدُ", 1, "sign", "حذف حرف العلة"),       # nor is the fatha nasb
    ("لَا تَنْسَ ذِكْرَ اللَّهِ", 1, "sign", "حذف حرف العلة"),     # the dropped letter settles لا as forbidding
    ("لَمْ يَقْرَأْ زَيْدٌ", 1, "sign", "سكون"),                 # nearest case: a hamza is no weak letter
    ("زَيْدٌ يَقْرَأُ", 1, "sign", "ضمة"),                         # so a hamza-final verb keeps its raf'
    ("إِنَّ الصِّدْقَ يَهْدِي إِلَى الْبِرِّ", 2, "sign", "ضمة مقدرة على الياء"),
    ("مَنْ يُرِدِ اللَّهُ بِهِ خَيْرًا يُفَقِّهْهُ فِي الدِّينِ", 5, "sign", "سكون"),  # the sukun before the pronoun
    ("مَنْ غَشَّنَا فَلَيْسَ مِنَّا", 1, "sign", "مبني على الفتح"),  # نا the object
    ("كَتَبْنَا الدَّرْسَ", 0, "sign", "مبني على السكون"),        # nearest case: نا the doer
    ("حُفَّتِ الْجَنَّةُ بِالْمَكَارِهِ", 0, "sign", "مبني على الفتح"),
    ("لَيَنْصُرَنَّ اللَّهُ الْمُؤْمِنِينَ", 0, "sign", "مبني على الفتح"),
    ("اَلْبَنَاتُ يَرْسُمْنَ الْوَرْدَ", 1, "sign", "مبني على السكون"),
    ("جَاءَ أَبُو الطَّالِبِ", 1, "sign", "الواو"),
    ("لَا ضَرَرَ وَلَا ضِرَارَ", 1, "sign", "مبني على الفتح"),
    ("لَا قَلَمَيْنِ فِي الْحَقِيبَةِ", 1, "sign", "مبني على الياء"),
    ("يَا غَافِلًا اِنْتَبِهْ", 1, "sign", "فتحة"),           # a tanween is never a dual's
    ("إِنَّ مِنَ الْبَيَانِ لَسِحْرًا", 3, "sign", "فتحة"),    # CAMeL's verb, the parser's noun
    ("سَيَكْتُبُ الطَّالِبُ", 0, "sign", "ضمة"),           # nearest case: a joined letter before the prefix
    ("وَسَيَكْتُبُ الطَّالِبُ", 0, "sign", "ضمة"),          # and two of them
    ("الطُّلَّابُ دَعَوْا رَبَّهُمْ", 1, "sign", "مبني على الضم"),
    ("أَتَانَا الرَّسُولُ", 0, "sign", "مبني على الفتح"),     # the alef before نا is a fatha
    ("رَأَيْتُ أَخًا", 1, "sign", "فتحة"),                   # indefinite: no مضاف, the vowel shows
    ("سَلَّمْتُ عَلَى أَبِي الطَّبِيبِ", 2, "sign", "الياء"),    # CAMeL's name أبي is the noun أب
    ("يَسِّرُوا وَلَا تُعَسِّرُوا", 2, "sign", "حذف النون"),   # لا with a و joined to it
    # a kasra on ـات with nothing to put it in jarr is nasb; the صفة after it follows
    ("الصَّلَوَاتِ الْخَمْسَ إِلَّا أَنْ تَطَّوَّعَ شَيْئًا", 0, "sign", "نيابة عن الفتحة"),
    ("الصَّلَوَاتِ الْخَمْسَ إِلَّا أَنْ تَطَّوَّعَ شَيْئًا", 1, "role", "صفة"),
    ("الصَّلَوَاتِ الْخَمْسَ إِلَّا أَنْ تَطَّوَّعَ شَيْئًا", 4, "reason", "مضارع منصوب"),                    # the merged ta' (shadda) makes it present
    ("رَأَيْتُ الطَّالِبَاتِ الْمُجْتَهِدَاتِ", 2, "case", "nasb"),
    ("مَرَرْتُ بِالطَّالِبَاتِ", 1, "case", "jarr"),         # a preposition keeps the kasra jarr
    ("أُرِيدُ أَنْ تَطَّوَّعَ", 2, "reason", "مضارع منصوب"),
    ("تَطَوَّعَ زَيْدٌ", 0, "reason", "ماضٍ"),               # no shadda: a true past
    ("تَمَّ الأَمْرُ", 0, "reason", "ماضٍ"),                 # a short doubled past is not Form V
]


@pytest.mark.parametrize("sentence, index, wrong", [
    ("اِهْدِنَا الصِّرَاطَ", 0, "حذف النون"),
    ("هُوَ يَظُنُّ ذَلِكَ", 1, "مبني"),                       # a root's doubled nun is no nun of emphasis
])
def test_card_sign_is_not(sentence: str, index: int, wrong: str):
    assert wrong not in (_read(sentence)["words"][index]["sign"] or "")


@pytest.mark.parametrize("sentence, index, field, expected", CARDS)
def test_card_field(sentence: str, index: int, field: str, expected: str):
    word = _read(sentence)["words"][index]
    assert expected in (word[field] or ""), word


def test_word_types_are_the_pages():
    """The types a card may carry are the ones grammar.json labels, and the rules use no other."""
    import json
    from pathlib import Path
    from backend.models.analyze import WORD_TYPES
    labelled = json.loads((Path(__file__).parent.parent.parent / "frontend/src/config/grammar.json").read_text(encoding="utf-8"))["types"]
    assert WORD_TYPES - {"punc"} == set(labelled)
    for sentence in (VERBAL, NOMINAL, "جَاءَ الَّذِي نَجَحَ، هُوَ فِي البَيْتِ"):
        assert {w["type"] for w in _read(sentence)["words"]} <= WORD_TYPES
    assert WordAnalysis.from_raw({"word": "زيدٌ", "type": "noun"}).type is None


@pytest.mark.parametrize("sentence, index, said", [
    ("إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا", 0, "حرف شرط"),
    ("إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا", 1, "فعل الشرط في محل جزم"),
    ("إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا", 8, "رابطة لجواب الشرط"),
    ("إِنْ تَدْرُسْ تَنْجَحْ", 2, "جواب الشرط مجزوم"),
    # لو governs nothing: its clauses have no place, and a لام ties on its answer
    ("لَوْ جَاءَ زَيْدٌ لَأَكْرَمْتُهُ", 0, "حرف شرط غير جازم"),
    ("لَوْ جَاءَ زَيْدٌ لَأَكْرَمْتُهُ", 1, "فعل الشرط، وجملته لا محل لها"),
    ("لَوْ جَاءَ زَيْدٌ لَأَكْرَمْتُهُ", 3, "واللام واقعة في جواب الشرط، وهو جواب الشرط"),
    ("إِنَّ الطَّالِبَ مُجْتَهِدٌ", 0, "ناسخ")])  # nearest case: إنّ before its noun
def test_a_verb_after_a_conditional_particle_makes_it_a_condition(sentence: str, index: int, said: str):
    assert said in _read(sentence)["words"][index]["reason"]


def test_two_conditions_joined_by_waw_are_two_conditions_not_one_verb_governing_another():
    # مَنْ leads, a verb follows, an answer follows: a conditional noun, not the relative;
    # the second مَنْ governs أَفْطَرَ, the first answer does not
    read = _read("مَنْ شَاءَ فَلْيَصُمْهُ وَمَنْ شَاءَ أَفْطَرَ")
    words = read["words"]
    assert read["summary"] == term_ar("jumlah_shartiyyah")
    assert [words[i]["role"] for i in (0, 3)] == ["مبتدأ"] * 2  # شَاءَ holds no doer of its own: the noun is it (naming._noun_place)
    assert [words[i].get("governor") for i in (1, 2, 4, 5)] == [0, 0, 3, 3]
    assert "جواب الشرط" in words[5]["reason"] and "رابطة" in words[2]["reason"]


def test_a_question_noun_with_one_verb_opens_no_condition():
    # nearest case: مَنْ with a verb but no answer stays the question or the relative
    words = _read("جَاءَ مَنْ نَجَحَ")["words"]
    assert words[1]["role"] != "اسم شرط جازم" and "الشرط" not in words[2]["reason"]


def test_a_conditional_noun_the_parser_gave_no_place_takes_the_books_place():
    # مَنْ whose verb has its object is the مبتدأ; a time or place word is a built ظرف, and the
    # answer under it still draws (أينما crashed the picture)
    man = _read("مَنْ صَامَ رَمَضَانَ فَلْيَصُمْهُ")["words"]
    assert man[0]["role"] == "مبتدأ" and "في محل رفع" in man[0]["reason"]
    assert "جواب الشرط في محل جزم" in man[3]["reason"]
    aynama = _read("أَيْنَمَا تَكُونُوا يُدْرِكْكُمُ الْمَوْتُ")
    assert aynama["summary"] == term_ar("jumlah_shartiyyah")
    assert aynama["words"][0]["role"] == "مفعول فيه" and "مبني في محل نصب" in aynama["words"][0]["reason"]


def test_a_command_the_parser_read_as_past_is_a_command():
    words = _read("إِنْ كُنْتَ تُحِبُّ اللَّهَ فَاتَّبِعْنِي")["words"]
    assert words[4]["aspect"] == "c" and words[4]["reason"].startswith("فعل أمر مبني على السكون")


def test_lawla_before_a_verb_urges_and_opens_no_condition():
    # nearest case to لو: لولا and لوما open a condition only before a noun
    assert _read("لَوْلَا تَسْتَغْفِرُونَ اللَّهَ")["summary"] != term_ar("jumlah_shartiyyah")


def test_each_reading_names_the_particle():
    words = iraab.analyze("إِذَا قَالَ الْعَبْدُ لاَ إِلَهَ إِلاَّ اللَّهُ وَاللَّهُ أَكْبَرُ")["words"]
    assert "ظرف شرط غير جازم" in words[0]["reason"]
    assert "لا النافية للجنس" in words[3]["reason"] and "أداة استثناء" in words[5]["reason"]
    assert "ويجوز أن تكون استئنافية" in words[7]["reason"]
    assert "أداة حصر" in iraab.analyze("مَا جَاءَ إِلَّا زَيْدٌ")["words"][2]["reason"]


@pytest.mark.parametrize("sentence, negates", [
    ("مَا فِي الدَّارِ أَحَدٌ", True),
    ("مَا عِنْدِي مَالٌ", True),
    ("مَا فِي بَيْتِ زَيْدٍ أَحَدٌ", True),
    ("مَا فِي الدَّارِ الْكَبِيرَةِ أَحَدٌ", True),
    ("مَا فِي الدَّارِ", False),
    ("وَمَا عِنْدَ اللَّهِ خَيْرٌ", False),
    ("وَمَا عِنْدَ اللَّهِ بَاقٍ", False),
])
def test_ma_before_a_fronted_khabar_and_its_raf_noun_is_the_negation(sentence: str, negates: bool):
    words = iraab.analyze(sentence)["words"]
    assert ("النافية" in words[0]["reason"]) is negates
    assert ("مبتدأ مؤخر" in words[-1]["reason"]) is negates


@pytest.mark.parametrize("sentence, sign", [("أَيُّكُمْ أَحْسَنُ عَمَلًا", "ضمة"), ("أَيُّ الْأَعْمَالِ أَفْضَلُ", "ضمة"),
                                            ("مَنْ أَبُوكَ", "مبني")])
def test_ayy_alone_of_the_question_words_takes_a_case(sentence: str, sign: str):
    assert iraab.analyze(sentence)["words"][0]["sign"].startswith(sign)


def test_the_wonder_verbs_noun_after_its_pronoun_is_no_second_object():
    words = iraab.analyze("مَا أَجْمَلَهَا لَيْلَةً")["words"]
    assert [w["role"] for w in words[:2]] == ["مبتدأ", "فعل"] and "للتعجب" in words[1]["reason"]


@pytest.mark.parametrize("sentence", ["مَا أَنْتَ إِلَّا بَشَرٌ", "وَمَا مُحَمَّدٌ إِلَّا رَسُولٌ", "ما أنت إلا بشر"])
def test_ma_before_illa_is_the_negation_and_illa_restricts_the_khabar(sentence: str):
    words = iraab.analyze(sentence)["words"]
    assert [w["role"] for w in words] == ["حرف", "مبتدأ", "حرف", "خبر"]
    assert "أداة حصر" in words[2]["reason"]


def test_the_nun_of_the_five_verbs_kept_after_la_is_raf_not_jazm():
    verb = _read("لَا يُؤْتُونَ النَّاسَ نَقِيرًا")["words"][1]
    assert (verb["case"], verb["sign"]) == ("raf'", "ثبوت النون")


@pytest.mark.parametrize("sentence, index, named, case", [
    ("فَإِذًا لَا يُؤْتُونَ النَّاسَ نَقِيرًا", 0, "حرف جواب وجزاء", "mabni"),  # a tanween is إذن, not the sudden إذا; the verb shows raf'
    ("إِذَنْ أُكْرِمَكَ", 0, "حرف جواب وجزاء ونصب", "mabni"),
    ("إِذَنْ أُكْرِمَكَ", 1, None, "nasb"),  # the present verb right after it is منصوب
    ("خَرَجْتُ فَإِذَا الأَسَدُ", 1, "حرف مفاجأة", "mabni"),  # nearest case: إذا without a tanween stays the sudden one
    # after the sentence it answers, فَإِذًا still opens its own clause (4:53)
    ("قَالَ زَيْدٌ فَإِذًا لَا يُؤْتُونَ النَّاسَ نَقِيرًا", 2, "حرف جواب وجزاء", "mabni"),
    ("زَيْدٌ إِذَنْ يَنْجَحُ", 1, "حرف جواب وجزاء", "mabni")])  # inside its clause it never works
def test_idhan_is_told_from_idha_by_its_spelling_and_works_only_before_a_verb_in_nasb(
        sentence: str, index: int, named: str | None, case: str):
    word = _read(sentence)["words"][index]
    assert (word.get("named"), word["case"]) == (named, case)


def test_a_pronoun_on_a_present_verb_is_not_read_as_its_passive_vowel():
    # the fatha before كَ in أُكْرِمَكَ is the verb's nasb; يُكْرَمُ is the passive
    assert "مجهول" not in _read("إِذَنْ أُكْرِمَكَ")["words"][1]["reason"]
    assert "مجهول" in _read("يُكْرَمُ الضَّيْفُ")["words"][0]["reason"]


def test_a_verb_whose_weak_last_letter_went_before_its_waw_is_read_by_the_letter_left():
    # صَلَّى: the ى is gone before the waw of يُصَلُّونَ, whose damma is the active's
    words = _read("فِي الْمَسْجِدِ رِجَالٌ يُصَلُّونَ")["words"]
    assert words[-1]["role"] == "فعل" and "مجهول" not in words[-1]["reason"]


def test_the_pronoun_on_a_verb_is_no_nun_of_the_five_verbs():
    # لا يَدْعُوهُ keeps its root و (not the dropped nun), لا تَأْكُلُونَهَا keeps its nun: neither is jussive
    assert [w["case"] for w in analysed("لَا يَدْعُوهُ زَيْدٌ")][1] == "raf'"
    assert [w["case"] for w in analysed("لَا تَأْكُلُونَهَا")][1] == "raf'"


@pytest.mark.parametrize("sentence, word, named", [
    ("وَابْتَلُوا الْيَتَامَى حَتَّى إِذَا بَلَغُوا النِّكَاحَ", "حَتَّى", "حرف ابتداء"),  # before إذا it works on nothing
    ("فَإِنْ آنَسْتُمْ مِنْهُمْ رُشْدًا", "فَإِنْ", "حرف شرط جازم"),
    ("وَبِدَارًا أَنْ يَكْبَرُوا", "أَنْ", "حرف نصب"),
])
def test_a_small_word_before_a_clause_is_named_by_what_it_does_there(sentence: str, word: str, named: str):
    assert named in {w["word"]: w for w in analysed(sentence)}[word]["reason"]


def test_the_qurans_uncontracted_jussive_is_a_verb_and_its_fa_proves_the_condition():
    # the dictionary has only فَلْيَسْتَعِفَّ; sarf's table also writes the doubled pair apart (p.289)
    got = {w["word"]: w for w in analysed("وَمَنْ كَانَ غَنِيًّا فَلْيَسْتَعْفِفْ")}
    assert "اسم شرط جازم" in got["وَمَنْ"]["reason"]
    assert got["فَلْيَسْتَعْفِفْ"]["role"] == "فعل" and "مجزوم" in got["فَلْيَسْتَعْفِفْ"]["reason"]


@pytest.mark.parametrize("sentence", [
    "مَنْ عَمِلَ صَالِحًا فَلِنَفْسِهِ",             # a noun sentence ties its answer with فَ
    "وَمَنْ كَفَرَ فَإِنَّ اللَّهَ غَنِيٌّ",           # إنّ
    "مَنْ جَاءَ بِالْحَسَنَةِ فَلَهُ خَيْرٌ مِنْهَا",
    "مَنْ يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ",  # the jussive after مَنْ alone is no relative's
    "مَنْ جَاءَ فَلَا تُكْرِمْهُ",                   # a prohibition could not stand as a condition
    "مَنْ جَاءَ فَقَدْ فَازَ",
])
def test_a_fa_on_an_answer_that_could_not_stand_alone_makes_man_a_condition(sentence: str):
    assert "اسم شرط جازم" in analysed(sentence)[0]["reason"]


def test_a_plain_past_verb_after_fa_is_no_proof_of_a_condition():
    # a past verb could stand as an answer with no فَ at all, so this is a relative and its عطف
    assert "اسم شرط" not in analysed("مَنْ جَاءَ فَقَامَ زَيْدٌ")[0]["reason"]


def test_la_before_a_jussive_with_a_pronoun_on_it_is_the_prohibition():
    assert "الناهية" in analysed("لَا تُكْرِمْهُ")[0]["reason"]


def test_a_past_verb_on_an_alef_is_built_on_an_implied_fatha():
    card = iraab.analyze(NADA, recorded=False)["words"][0]
    assert card["sign"] == "مبني على الفتح المقدر على الألف للتعذر"
    assert iraab.analyze("كَتَبَ زَيْدٌ", recorded=False)["words"][0]["sign"] == "مبني على الفتح"


def test_the_idafa_of_an_elative_is_ma3nawiyya_not_lafziyya():
    reason = iraab.analyze(NADA, recorded=False)["words"][2]["reason"]
    assert "لفظية" not in reason and "معنوية" in reason
    assert "لفظية" in iraab.analyze("جَاءَ ضَارِبُ زَيْدٍ", recorded=False)["words"][2]["reason"]


def test_a_past_verb_on_an_alef_keeps_its_implied_fatha_under_a_pronoun():
    sign = lambda s: iraab.analyze(s, recorded=False)["words"][0]["sign"]
    assert sign("رَمَاهُ الْوَلَدُ") == sign("دَعَاهُمُ النَّبِيُّ") == "مبني على الفتح المقدر على الألف للتعذر"
    assert sign("كَتَبَهُ الرَّجُلُ") == "مبني على الفتح"
    assert sign("رَمَيْتُ الْحَجَرَ") == "مبني على السكون"
    assert sign("رَوَيْنَاهُ عَنْهُ") == sign("رَمَيْتُهُ أَمْسِ") == "مبني على السكون"  # the doer's pronoun, under the object's
    assert sign("رَوَاهُ زَيْدٌ") == "مبني على الفتح المقدر على الألف للتعذر"  # one doer: its وا is no plural's


def test_ams_is_built_on_the_kasra_in_every_place():
    words = lambda s: iraab.analyze(s, recorded=False)["words"]
    for sentence, role in (("جِئْتُ أَمْسِ", "مفعول فيه"), ("مَا رَأَيْتُهُ مُنْذُ أَمْسِ", "مجرور"), ("كَانَ أَمْسِ يَوْمًا جَمِيلًا", "اسم كان")):
        ams = next(w for w in words(sentence) if w["word"] == "أَمْسِ")
        assert (ams["role"], ams["sign"]) == (role, "مبني على الكسر"), sentence
    assert words("مُنْذُ أَمْسِ")[1]["sign"] == words("أَمْسِ")[0]["sign"] == "مبني على الكسر"  # never the command "enter the evening"


def test_a_built_word_keeps_its_sukun_when_moved_to_kasra_for_the_next_sakin():
    sign = lambda s, i: iraab.analyze(s, recorded=False)["words"][i]["sign"]
    moved = "مبني على السكون، وحُرِّك بالكسر لالتقاء الساكنين"
    assert sign("أَحْسِنْ إِلَى مَنِ اسْتَشَارَكَ", 2) == moved
    assert sign("سَأَلْتُ عَنِ الْأَمْرِ", 1) == moved
    assert sign("جَاءَ هَؤُلَاءِ", 1) == "مبني على الكسر"  # its own kasra, no meeting


def test_a_relative_after_a_command_is_its_object_and_its_sila_a_verb():
    words = iraab.analyze("أَكْرِمْ مَنْ زَارَكَ", recorded=False)["words"]
    assert words[0]["sign"] == "مبني على السكون" and words[1]["role"] == "مفعول به"
    assert words[2]["role"] == "فعل"
    # حَرَمَكَ reads as a noun too ("your sanctuary"); after a relative its صلة is the verb
    assert iraab.analyze("أَعْطِ مَنْ حَرَمَكَ", recorded=False)["words"][2]["role"] == "فعل"


def test_a_conditional_noun_before_laysa_is_its_mubtada_not_its_ism():
    assert _role("مَنْ ظَلَمَنَا فَلَيْسَ صَدِيقًا", 0) == "مبتدأ"  # ليس comes after it: it governs nothing before
    words = iraab.analyze("مَنْ كَذَبَ فَلَيْسَ صَادِقًا", recorded=False)["words"]
    # كذب has no object, so its hidden هو points back to مَنْ: the مبتدأ, called the conditional noun it is
    assert words[0]["role"] == "مبتدأ" and words[0]["reason"].startswith("اسم شرط جازم")


def test_a_form_four_command_is_a_verb_but_a_name_stays_a_name():
    sign = lambda s, i: iraab.analyze(s, recorded=False)["words"][i]["sign"]
    assert sign("أَكْرِمُوا الضَّيْفَ", 0) == sign("أَفْشُوا السَّلَامَ", 0) == "مبني على حذف النون"
    assert _role("جَاءَ أَحْمَدُ", 1) == "فاعل"
    assert _role("أَحْمَدْ", 0) != "فعل"  # a name in pause keeps its own vowels


_DROPPED, _MEEM = "وحرف النداء محذوف تقديره يا", "والميم المشددة عوض عن حرف النداء المحذوف"


_DROPPED, _MEEM = "وحرف النداء محذوف تقديره يا", "والميم المشددة عوض عن حرف النداء المحذوف"


@pytest.mark.parametrize("sentence, at, role, said", [
    # يا is left off before a called noun (Ibn Aqil V3 p256: عبد الله اركب)
    ("رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً", 0, "منادى", _DROPPED),
    ("رَبَّنَا اغْفِرْ لَنَا", 0, "منادى", _DROPPED),
    ("عَبْدَ اللَّهِ ارْكَبْ", 0, "منادى", _DROPPED),
    ("عَبْدَ بَيْتِ اللَّهِ ارْكَبْ", 0, "منادى", _DROPPED),  # the command after a chain of مضاف إليه
    ("ربنا اِغْفِرْ لَنَا", 0, "منادى", _DROPPED),  # its case not typed: the command after it says it
    ("رب العالمين اِغْفِرْ لِي", 0, "منادى", _DROPPED),  # the command after the مضاف إليه
    ("رَبِّ اغْفِرْ لِي", 0, "منادى", _DROPPED),
    ("رَبَّنَا ظَلَمْنَا أَنْفُسَنَا", 0, "منادى", _DROPPED),  # its verb has an object of its own: no job left for it
    ("رَبَّنَا إِنَّنَا آمَنَّا", 0, "منادى", _DROPPED),  # nothing after إنّ works on a word before it
    ("كِتَابَ زَيْدٍ قَرَأْتُ", 0, "مفعول به", None),  # nearest case: the verb has no other object
    ("كِتَابَ زَيْدٍ قَرَأْتُ غِلَافَهُ", 0, "مفعول به", None),  # nearest case: busied with its pronoun (الاشتغال)
    ("غُلَامَ زَيْدٍ أَعْطَيْتُ دِرْهَمًا", 0, "مفعول به", None),  # nearest case: a verb of two objects  # the kasra the ياء المتكلم left when it went (V3 p274: يا عبدِ)
    ("اللَّهُمَّ", 0, "منادى", _MEEM),  # يا put at the end as the doubled ميم
    ("يَا رَبَّنَا", 1, "منادى", None),  # nearest case: يا typed, nothing left off
    ("رَبُّنَا اغْفِرْ لَنَا", 0, "مبتدأ", None),  # nearest case: typed in raf', no call
    ("كِتَابَهُ قَرَأَ زَيْدٌ", 0, "مفعول به", None),  # nearest case: no command after it
    ("رَأَيْتُ عَبْدَ اللَّهِ اذْهَبْ", 1, "مفعول به", None),  # nearest case: a command after it, but it does not open the sentence
])
def test_a_call_with_no_ya_typed(sentence: str, at: int, role: str, said: str | None):
    card = cards(sentence)[at]
    assert card["role"] == role
    assert all((wording == said) == (wording in card["reason"]) for wording in (_DROPPED, _MEEM)), card["reason"]
    if role == "منادى":  # the يا left off is no word of the sentence; a typed one is
        assert card["governor"] == (None if said else 0)


_MY_YA = "وياء المتكلم المحذوفة ضمير متصل مبني في محل جر مضاف إليه"


@pytest.mark.parametrize("sentence, at, gone", [
    # the ياء المتكلم went and left its kasra (Ibn Aqil V3 p274: يا عبدِ): nasb, unseen before the ya, never a command
    ("يَا قَوْمِ اعْبُدُوا اللَّهَ", 1, True),
    ("يَا رَبِّ", 1, True),  # after يا, not رَبَّى's command
    ("رَبِّ اغْفِرْ لِي", 0, True),
    ("رَبِّ زِدْنِي عِلْمًا", 0, True),  # the command after it with its object written on
    ("يَا رَبِّي", 1, False),  # nearest case: the ya typed, a piece of its own
])
def test_a_called_noun_whose_ya_went(sentence: str, at: int, gone: bool):
    card = cards(sentence)[at]
    assert (card["role"], card["case"], card["sign"]) == ("منادى", "nasb", "فتحة مقدرة على ما قبل ياء المتكلم")
    assert "command" not in card["notes"]
    assert (_MY_YA in card["reason"]) == gone, card["reason"]


def test_a_called_noun_with_no_ha_says_no_attention():
    card = cards("يَا زَيْدُ")[1]  # nearest case: a called noun with no ها written on
    assert card["sign"] == "مبني على الضم" and _ATTENTION not in card["reason"]


_BUSIED = "والناصب له فعل محذوف وجوبًا يفسره الفعل المذكور"


@pytest.mark.parametrize("sentence, at, role, governor, busied", [
    ("زَيْدًا ضَرَبْتُ", 0, "مفعول به", 1, False),  # its doer in the verb: تُ
    ("زَيْدًا نَصَرْنَا", 0, "مفعول به", 1, False),
    ("زَيْدًا اضْرِبْ", 0, "مفعول به", 1, False),  # a command's hidden أنت
    ("زَيْدًا ضَرَبُوا", 0, "مفعول به", 1, False),  # the و of many, written on
    ("الْكِتَابَ ارْفَعِي", 0, "مفعول به", 1, False),  # the ي hung as its doer is no pronoun busying it
    ("عِلْمًا طَلَبَ زَيْدٌ", 0, "مفعول به", 1, False),  # its doer after it
    ("كِتَابًا أُعْطِيتُ", 0, "مفعول به", 1, False),  # a passive verb of giving, its deputy the تُ, keeps one (V2 p123)
    ("جُبَّةً كُسِيتُ", 0, "مفعول به", 1, False),
    ("كِتَابًا أُعْطِيَ", 0, "مفعول به", 1, False),  # its deputy the هو hidden in it
    ("زَيْدًا ضَرَبْتُهُ", 0, "مفعول به", None, True),  # الاشتغال: the verb busied with its pronoun
    ("زَيْدًا اضْرِبْهُ", 0, "مفعول به", None, True),
    ("زَيْدًا ضَرَبُوهُ", 0, "مفعول به", None, True),
    ("زَيْدًا أَنَا ضَارِبُهُ", 0, "مفعول به", None, True),  # a participle doing its verb's work, the same (V2 p142)
    ("زَيْدًا ضَرَبْتُ غُلَامَهُ", 0, "مفعول به", None, True),  # busied with its سببي (V2 p128)
    ("زَيْدًا ضَرَبْتُ غُلَامَ صَاحِبِهِ", 0, "مفعول به", None, True),  # the pronoun deeper down the إضافة chain
    ("زَيْدًا مَرَرْتُ بِغُلَامِهِ", 0, "مفعول به", None, True),  # the سببي through a جار
    ("زَيْدًا ضَرَبَ غُلَامُهُ", 0, "مفعول به", 1, False),  # nearest case: the سببي is the doer, not worked on in nasb
    ("زَيْدًا ضَرَبْتُ أَخَاكَ", 0, "مفعول به", 1, False),  # nearest case: كَ is no pronoun of the one away, as زيد is
    ("رَأَيْتُ زَيْدًا يَضْرِبُ غُلَامَهُ", 1, "مفعول به", 0, False),  # nearest case: the object comes after its verb
    ("زَيْدًا مَرَرْتُ بِهِ", 0, "مفعول به", None, True),  # through a جار
    ("عِلْمًا طَلَبَهُ زَيْدٌ", 0, "مفعول به", None, True),
    ("زَيْدٌ ضَرَبْتُهُ", 0, "مبتدأ", None, False),  # nearest case: typed in raf'
    ("إِنَّ زَيْدًا ضَرَبْتُهُ", 1, "اسم إن", 0, False),  # nearest case: إنّ puts it in nasb
    ("رَأَيْتُ زَيْدًا يَضْرِبُهُ عَمْرٌو", 1, "مفعول به", 0, False),  # nearest case: the verb before it governs it
    ("أَعْطَيْتُهُ دِرْهَمًا", 1, "مفعول به", 0, False),  # nearest case: after its busied verb, not before
    ("كَتَبْتُ لَهُ رِسَالَةً", 2, "مفعول به", 0, False),  # nearest case: after a verb busied through a جار
])
def test_an_object_put_before_its_verb(sentence: str, at: int, role: str, governor: int | None, busied: bool):
    """زَيْدًا ضَرَبْتُ: a nasb noun before a verb that has its doer is its object (Ibn Aqil V2 p129); before a
    verb busied with a pronoun back to it, the object of a verb like that one, left out (V2 p128)."""
    card = cards(sentence)[at]
    assert (card["role"], card["governor"]) == (role, governor)
    assert (_BUSIED in card["reason"]) == busied, card["reason"]


@pytest.mark.parametrize("sentence, at, want", [
    # a past verb is never what a nasb particle works on (Tasheel 4.1.1): the present verb the vowels allow is the word
    ("أُحِبُّ أَنْ أَقْرَأَ", 2, ("فعل", "nasb")),
    ("أُرِيدُ أَنْ تَقْرَأَ", 2, ("فعل", "nasb")),
    ("لَنْ أَقْرَأَ", 1, ("فعل", "nasb")),
    ("عَلِمْتُ أَنْ جَاءَ زَيْدٌ", 2, ("فعل", "mabni")),  # nearest case: no present verb reads جَاءَ, so it stays the past verb
])
def test_a_verb_after_a_nasb_particle_is_the_present_one(sentence: str, at: int, want: tuple):
    card = cards(sentence)[at]
    assert (card["role"], card["case"]) == want
