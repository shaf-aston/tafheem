"""What a card prints for a word (sign, case, reason, summary), per rule, on typed sentences.

Run: python -m pytest tests/nahw/test_card_fields.py
"""
from __future__ import annotations

import pytest
from backend.models.analyze import WordAnalysis
from backend.services.nahw import iraab, signs
from backend.services.nahw.book import term_ar
from backend.services.text.harakat import build_nun, five_verb_nun, merged_nun
from tests.nahw_helpers import analysed, cards, NADA, needs_parser, NOMINAL, VERBAL, _ATTENTION, _read, _role

pytestmark = needs_parser


# A card's reason must explain the role the card wears, whoever named it.
REASON_SENTENCES = ["مَتَى سَافَرَ الرَّجُلُ", "كُتِبَ الدَّرْسُ", "جاء محمد وعلي", "يا محمد اجلس",
                    "إِنَّ الطَّالِبَ مُجْتَهِدٌ", "كَتَبَ الطَّالِبُ الدَّرْسَ فِي الْبَيْتِ"]


def test_every_role_has_a_reason():
    from backend.services.nahw.book import teacher_rules
    from backend.services.nahw.roles import ROLES
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
    # a doubled or hollow root's command to many, spelled as its past passive: opening the sentence or after فَ
    ("يَا أَيُّهَا النَّاسُ قَدْ فُرِضَ عَلَيْكُمُ الْحَجُّ فَحُجُّوا", 7, "mabni", "فعل أمر"),
    ("سِيرُوا هَذَا جُمْدَانُ", 0, "mabni", "فعل أمر"),
    ("ائْتُوا رَوْضَةَ خَاخٍ", 0, "mabni", "فعل أمر"),  # أَتَى's command: its hamzah after the wasl sits on a ي
    ("ائْتِ الْمَسْجِدَ", 0, "mabni", "فعل أمر"),
    # after a joined ف or و the wasl drops and the first-letter hamzah takes a sukun: the command, not a past
    ("فَأْتُوا بِسُورَةٍ مِثْلِهِ", 0, "mabni", "فعل أمر"),
    ("فَأْذَنُوا بِحَرْبٍ", 0, "mabni", "فعل أمر"),
    ("وَأْمُرْ أَهْلَكَ بِالصَّلَاةِ", 0, "mabni", "فعل أمر"),
    ("مُدُّوهُ مِنَ الْمَاءِ", 0, "mabni", "فعل أمر"),
    ("ثُمَّ رُدُّوا إِلَى اللَّهِ", 1, "mabni", "مبني للمجهول"),  # told on after ثُمَّ: still passive
    ("قُتِلُوا فِي سَبِيلِ اللَّهِ", 0, "mabni", "مبني للمجهول"),  # a sound root: its command is spelled اُقْتُلُوا, no tie
    ("اقْضِيَا يَوْمًا آخَرَ مَكَانَهُ", 0, "mabni", "فعل أمر"),  # a dual command the dictionary only guessed a name
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
    ("تَعَلَّمَهُ زَيْدٌ", 0, "case", "mabni"),  # the damma is the pronoun's, the verb stays past
    ("تَنَزَّلُ الْمَلَائِكَةُ وَالرُّوحُ فِيهَا", 0, "case", "raf'"),  # تَتَنَزَّلُ with one ت gone
    ("تَنَزَّلَ الْمَلَكُ", 0, "case", "mabni"),
    ("لَؤُمَ الرَّجُلُ طَبْعًا", 2, "role", "تمييز"),  # the middle letter written in the pattern
    ("كَرُمَ زَيْدٌ أَصْلًا", 2, "role", "تمييز"),
    ("كَبُرَتْ كَلِمَةً تَخْرُجُ مِنْ أَفْوَاهِهِمْ", 1, "role", "تمييز"),  # فَعُلَ takes no object
    ("شَرُفَ الْمَكَانُ مَوْقِعًا", 2, "role", "تمييز"),
    ("كَبُرَ مَقْتًا", 1, "role", "تمييز"),  # كَبُرَ, missing from the dictionary: its typed فَعُلَ vowels tell it
    ("يَكْبُرُ زَيْدٌ أَخَاهُ سِنًّا", 3, "role", "تمييز"),  # كَبَرَ in tamyeez_verbs
    ("كَبُرَ الْوَلَدُ كِبَرًا", 2, "role", "مفعول مطلق"),  # its own masdar is no تمييز
    ("حَسُنَ زَيْدٌ رَاكِبًا", 2, "role", "حال"),  # a doer's measure stays a state
    # a built noun after a فَعُلَ verb is its doer and the indefinite nasb after it the تمييز (4:69)
    ("حَسُنَ أُولَئِكَ رَفِيقًا", 1, "role", "فاعل"),
    ("حَسُنَ أُولَئِكَ رَفِيقًا", 2, "role", "تمييز"),
    ("حَسُنَ هَذَا رَجُلًا", 1, "role", "فاعل"),
    # أَغَارُ: غَارَ يَغَارُ, which the dictionary lacks; its passive أُغَارُ does not stand for it
    ("قَالَ أَغَارُ عَلَيْكَ", 1, "role", "فعل"),
    ("أُغَارُ عَلَيْكَ", 0, "role", "فعل مجهول"),
    ("يَنْفَعُ مَا تَعَلَّمْتَ", 1, "role", "فاعل"),  # the verb has no doer yet: the relative is it
    ("فَاتَّقُوا اللَّهَ مَا اسْتَطَعْتُمْ", 2, "name", "ما المصدرية الظرفية، حرف مصدري"),  # its doer is settled
    ("يَنْفَعُ الْعِلْمُ مَا دُمْتَ حَيًّا", 2, "name", "ما المصدرية الظرفية، حرف مصدري"),
    ("كَتَبَ زَيْدٌ كِتَابًا", 2, "role", "مفعول به"),  # a فَعَلَ verb keeps its object
    ("قَالَ أَتَقُولُونَ عَلَى اللَّهِ", 1, "role", "فعل"),  # a question hamza opens what is said
    ("قَالَ أَوَعَلَيْكَ أَغَارُ", 1, "role", "حرف جر"),
    ("أَفَلَا تَعْقِلُونَ", 0, "role", "حرف"),  # أَ + فَ + لا, not the verb أَفَلَا
    ("أَوْلَمَ الرَّجُلُ", 0, "role", "فعل"),  # a silent و is the verb's own letter
    ("جَمَعْنَاهُمْ جَمِيعًا", 1, "role", "حال"),  # bare جميع is a حال even off the verb's own root
    ("يَفْعَلُ مَا آمُرُهُ", 1, "role", "مفعول به"),
    ("أَكَلَ مَا طَبَخَهُ", 1, "role", "مفعول به"),
    ("يُعْجِبُنِي مَا صَنَعْتَ", 1, "role", "فاعل"),
    ("شَرِبْتُ كُلَّ الشَّرَابِ", 1, "role", "مفعول به"),  # a three-letter verb's فَعَال names the drink
    ("جَاءَ عُثْمَتَّانِ", 1, "sign", "ضمة"),  # an unread word with a doubled ت: one word, no dual
    ("جَاءَ كُرْبْتَانِ", 1, "sign", "ضمة"),  # an unread word with sukun before the ت: one word, no dual
    ("هَذِهِ تَطْلِيقَتَانِ", 1, "sign", "الألف، مثنى"),  # an unread ة noun's dual still shows its alif
    ("طَلَّقَهَا تَطْلِيقَتَيْنِ", 1, "sign", "الياء، مثنى"),
    ("جَاءَ بِبُهْتَانِ", 1, "sign", "كسرة"),  # sukun before the ت: one word, no dual
    ("أَفْلَحْتَ كُلَّ الْفَلَاحِ", 1, "role", "مفعول مطلق"),  # كل added to the verb's فَعَال doing
    ("كَتَبْتُ كُلَّ الْكِتَابِ", 1, "role", "مفعول به"),  # فِعَال here names the thing written
    ("مَنْ قَتَلَ قَتِيلًا فَلَهُ سَلَبُهُ", 2, "role", "مفعول به"),  # قتيل = مقتول, the one done to
    ("صَهَلَ الْفَرَسُ صَهِيلًا", 2, "role", "مفعول مطلق"),  # فَعِيل doing off a verb with no object
    # the kasra the ي left, a command after it: called again past the first word, governed by no word before it
    ("رَبِّ اغْفِرْ لِي رَبِّ اغْفِرْ لِي", 3, "role", "منادى"),
    ("اللَّهُمَّ اغْفِرْ لِي رَبِّ اغْفِرْ لِي", 3, "role", "منادى"),
    ("تُبْ إِلَى رَبِّ اسْجُدْ لَهُ", 2, "role", "مجرور"),  # a preposition before it governs it
    ("قَالَ يَا قَوْمِ اعْبُدُوا اللَّهَ قَوْمِ اعْبُدُوا اللَّهَ", 5, "role", "منادى"),  # a noun with ال before it takes no مضاف إليه
    ("نَظَرْتُ إِلَى كِتَابِ رَبِّ اقْرَأْ", 3, "role", "مضاف إليه"),  # a bare noun before it does
    # لا hung on the noun at the head, a جار ومجرور telling of it: the noun is اسم لا
    ("لَا قَطْعَ فِي ثَمَرٍ وَلَا كَثَرٍ", 1, "role", "اسم لا"),
    ("لَا قَطْعَ الْيَوْمَ وَلَا كَثَرٍ", 2, "role", "خبر لا"),  # a ظرف tells of it the same
    ("لَا قَطْعَ ثَمَرٍ وَلَا كَثَرٍ", 2, "role", "مضاف إليه"),  # a bare noun under it is no khabar
    # a pronoun on a verb of saying is what it says: the verb after ثُمَّ ... is the condition's answer, nothing said
    ("مَنْ قَالَهُنَّ ثُمَّ مَاتَ تَحْتَ لَيْلَتِهِ مَاتَ عَلَى الْفِطْرَةِ", 1, "name", "فعل الشرط"),
    # أَيُّمَا: أيّ with ما الزائدة written onto it, the ما leaving أيّ and its مضاف إليه joined
    ("أَيُّمَا امْرَأَةٍ نَكَحَتْ فَنِكَاحُهَا بَاطِلٌ", 1, "role", "مضاف إليه"),
    ("أَيُّمَا امْرَأَةٍ نَكَحَتْ فَنِكَاحُهَا بَاطِلٌ", 2, "name", "فعل الشرط"),
    ("أَيُّمَا رَجُلٍ قَالَ لِأَخِيهِ يَا كَافِرُ فَقَدْ بَاءَ بِهَا أَحَدُهُمَا", 7, "name", "جواب الشرط"),
    ("فَأَيُّمَا امْرَأَةٍ نَكَحَتْ فَنِكَاحُهَا بَاطِلٌ", 1, "role", "مضاف إليه"),  # a joined ف still splits the ما off
    ("أَيَّمَا الْأَجَلَيْنِ قَضَيْتُ فَلَا عُدْوَانَ عَلَيَّ", 0, "role", "مفعول به"),  # 28:28, the condition's object first
    ("أَيَّامًا مَعْدُودَاتٍ", 0, "role", "مفعول به"),  # 2:184 days: a word ending ما is no أيّ+ما
    ("وَأَيَّامًا مَعْدُودَاتٍ", 1, "role", "صفة"),  # and not when joined to و either
    ("مَهْمَا تَأْتِنَا بِهِ", 0, "role", "مبتدأ"),  # built مهما keeps its ما
    ("أَيُّمَا امْرَأَةٍ نَكَحَتْ فَنِكَاحُهَا بَاطِلٌ", 4, "role", "خبر"),  # the answer's khabar, no فاعل across the ف
    ("أَيُّمَا امْرَأَةٍ جَاءَتْ فَبَيْتُهَا بَاطِلٌ", 4, "role", "خبر"),
    ("ائْتُوا رَوْضَةَ خَاخٍ", 1, "role", "مفعول به"),  # after أَتَى's command, not a خبر's noun
    ("وَأْدُ الْبَنَاتِ حَرَامٌ", 0, "role", "مبتدأ"),  # و + أْ with a case damma: the noun وَأْد, no command
    ("وَأْدُ الْبَنَاتِ حَرَامٌ", 2, "role", "خبر"),
    ("مَنْ قَالَهُنَّ ثُمَّ مَاتَ تَحْتَ لَيْلَتِهِ مَاتَ عَلَى الْفِطْرَةِ", 6, "name", "جواب الشرط"),
    # a damma on the last letter before a stuck pronoun is no past verb's: سَلَبُهُ is the noun, so the مَنْ before it is a relative
    ("مَنْ قَطَعَ مِنْهُ شَيْئًا فَلِمَنْ أَخَذَهُ سَلَبُهُ", 6, "name", "مبتدأ مؤخر"),
    # the doer's تُ keeps its past verb
    ("كُلُّ مَالٍ نَحَلْتُهُ عَبْدًا حَلَالٌ", 2, "role", "فعل"),
    # a damma carried over to join the next word is no ending: with no pronoun stuck on, the past verb stays
    ("إِذَا دَعَوْتُمُ اللَّهَ فَاعْزِمُوا", 1, "role", "فعل"),
    ("إِذَا صَلَّى جَالِسًا فَصَلُّوا جُلُوسًا", 4, "role", "حال"),  # a masdar of a verb that takes no object, as a state
    ("إِنَّ أَحْسَنَ مَا زُرْتُمُ اللَّهَ فِي قُبُورِكُمْ وَمَسَاجِدِكُمُ الْبَيَاضُ", 8, "role", "خبر إن"),  # past the اسم's صلة
    ("مِفْتَاحُ الصَّلَاةِ الطُّهُورُ وَتَحْرِيمُهَا التَّكْبِيرُ وَتَحْلِيلُهَا التَّسْلِيمُ", 3, "role", "مبتدأ"),  # و joins a sentence
    ("مِفْتَاحُ الصَّلَاةِ الطُّهُورُ وَتَحْرِيمُهَا التَّكْبِيرُ وَتَحْلِيلُهَا التَّسْلِيمُ", 6, "role", "خبر"),
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
    # a doubled verb's fatha after لا is its jussive's (harakat.doubled_last): no negation puts a verb in nasb, so the لا forbids
    ("لَا تَمُدَّ يَدَكَ", 0, "reason", "لا الناهية"),
    ("لَا تَمُدَّ يَدَكَ", 1, "name", "فعل مضارع للنهي"),
    ("أَنْ لَا تَمُدَّ يَدَكَ", 1, "reason", "لا النافية"),  # nearest case: after أن the fatha is its nasb
    ("لَنْ يَرُدَّ وَلَا يَمُدَّ يَدَهُ", 2, "reason", "لا النافية"),  # and after لن's verb, whose negation the لا stresses
    ("لَنْ يَرُدَّ وَلَا تَمُدَّ يَدَكَ", 2, "reason", "لا الناهية"),  # nearest case: another doer, the لا forbids
    # a prohibition asks, and what asks is never in a condition's clause, nor its answer unless a ف ties it (Ibn Aqil V4, page unchecked)
    ("إِنْ تَدْرُسْ لَا تَرْسُبْ", 2, "reason", "لا النافية"),
    ("إِنْ تَدْرُسْ لَا تَرْسُبْ", 3, "name", "جواب الشرط"),
    ("إِنْ تَجْتَهِدُوا لَا تَخِيبُوا", 2, "reason", "لا النافية"),
    ("مَنْ لَا يَرْحَمْ لَا يُرْحَمْ", 1, "reason", "لا النافية"),
    ("مَنْ لَا يَرْحَمْ لَا يُرْحَمْ", 1, "book", "تسهيل النحو"),  # its book named as any particle's, not a raw section number
    ("مَنْ لَا يَرْحَمْ لَا يُرْحَمْ", 3, "reason", "لا النافية"),
    ("مَنْ لَا يَرْحَمْ لَا يُرْحَمْ", 4, "reason", "جواب الشرط"),
    ("إِنْ تَدْرُسْ وَلَا تَكْسَلْ تَنْجَحْ", 2, "reason", "لا النافية"),  # joined to the condition's verb, in its clause
    ("إِنْ تَدْرُسْ وَلَا تَكْسَلْ تَنْجَحْ", 4, "name", "جواب الشرط"),  # the و joins تكسل on: the answer is after it
    ("مَنْ لَمْ يَشْكُرِ النَّاسَ لَمْ يَشْكُرِ اللَّهَ", 1, "name", "حرف نفي وجزم وقلب"),  # nearest case: another jazm particle
    ("مَنْ لَمْ يَشْكُرِ النَّاسَ لَمْ يَشْكُرِ اللَّهَ", 4, "name", "حرف نفي وجزم وقلب"),  # keeps its own name
    ("إِنْ قَصَّرْتَ فَلَا تَحْزَنْ", 2, "reason", "لا الناهية"),  # nearest case: tied by its ف, the answer may ask
    ("لَا تَكْذِبْ وَلَا تَظْلِمْ", 2, "reason", "لا الناهية"),  # nearest case: no condition
    # nearest case: what a verb of saying says (مقول القول) is a sentence of its own, neither the clause nor the answer
    ("وَإِذَا قِيلَ لَهُمْ لَا تُفْسِدُوا فِي الْأَرْضِ قَالُوا", 3, "reason", "لا الناهية"),  # 2:11
    ("وَإِذَا قِيلَ لَهُمْ لَا تُفْسِدُوا فِي الْأَرْضِ قَالُوا", 7, "name", "جواب الشرط"),
    ("مَنْ قَالَ لَا تَفْعَلْ فَقَدْ نَصَحَ", 2, "reason", "لا الناهية"),
    ("إِنْ قُلْتَ لَهُ لَا تَكْذِبْ غَضِبَ", 3, "reason", "لا الناهية"),
    ("إِنْ قُلْتَ لَهُ لَا تَكْذِبْ غَضِبَ", 5, "name", "جواب الشرط"),
    ("إِنْ قُلْتَ لَهُ لَا تَكْذِبْ وَلَا تَسْرِقْ غَضِبَ", 5, "reason", "لا الناهية"),  # a verb joined on to a said one is said too
    # a verb of saying before the opener says the whole condition: the condition opens its sentence and the rule holds there
    ("قَالَ الْمُعَلِّمُ إِنْ تَدْرُسْ لَا تَرْسُبْ", 2, "name", "حرف شرط جازم"),
    ("قَالَ الْمُعَلِّمُ إِنْ تَدْرُسْ لَا تَرْسُبْ", 4, "reason", "لا النافية"),
    ("قَالَ الْمُعَلِّمُ إِنْ تَدْرُسْ لَا تَرْسُبْ", 5, "name", "جواب الشرط"),
    ("قَالَ زَيْدٌ إِنْ جَاءَ عَمْرٌو أَكْرَمْتُهُ", 5, "name", "جواب الشرط"),
    ("قَالَ إِنَّ زَيْدًا قَائِمٌ", 1, "name", "حرف ناسخ مشبه بالفعل"),  # nearest case: إنّ, no condition
    # an إلا after إنْ with no second verb between: one clause, negated and restricted (Mughni, إنْ النافية; page unchecked)
    ("إِنْ أَرَدْنَا إِلَّا الْحُسْنَى", 0, "name", "إن النافية"),  # 9:107
    ("قَالُوا إِنْ أَرَدْنَا إِلَّا الْحُسْنَى", 1, "name", "إن النافية"),
    ("قَالُوا إِنْ نَحْنُ إِلَّا بَشَرٌ", 1, "name", "إن النافية"),
    ("إِنْ جَاءَ زَيْدٌ لَمْ يَبْقَ إِلَّا عَمْرٌو", 4, "name", "جواب الشرط"),  # nearest case: a second verb, the answer
    # a conditional إنْ takes لم or لا before its verb (فَإِنْ لَمْ تَفْعَلُوا، إِلَّا تَفْعَلُوهُ)
    ("إِنْ لَمْ تَدْرُسْ تَرْسُبْ", 0, "name", "حرف شرط جازم"),
    ("إِنْ لَمْ تَدْرُسْ تَرْسُبْ", 2, "name", "فعل الشرط"),
    ("إِنْ لَمْ تَدْرُسْ تَرْسُبْ", 3, "name", "جواب الشرط"),
    ("إِنْ لَا تَفْعَلُوهُ تَكُنْ فِتْنَةٌ", 3, "name", "جواب الشرط"),
    ("إِنْ زَيْدًا قَائِمٌ", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # the nasb tells it from the negation, no لام needed
    # a ناسخ verb after إنْ and a لام of emphasis later in its clause: the lightened إنّ, idle (7:102, 17:73)
    ("وَإِنْ وَجَدْنَا أَكْثَرَهُمْ لَفَاسِقِينَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),
    ("وَإِنْ كَادُوا لَيَفْتِنُونَكَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),
    ("وَإِنْ كَانَتْ لَكَبِيرَةً", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # 2:143
    ("وَإِنْ كُنْتُمْ مِنْ قَبْلِهِ لَمِنَ الضَّالِّينَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # 2:198: a جار before is no خبر told
    ("وَإِنْ كَادَ الَّذِينَ كَانُوا أَصْحَابَهُ لَيَتْرُكُونَهُ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # another verb's خبر
    ("وَإِنْ كُنْتُمْ فِي رَيْبٍ", 0, "name", "حرف شرط جازم"),  # nearest case: no لام, a condition
    ("إِنْ كَانَ زَيْدٌ غَائِبًا فَإِنَّ عَمْرًا لَحَاضِرٌ", 0, "name", "حرف شرط جازم"),  # the لام is the answer's إنّ's
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ صَادِقًا لَقَدْ ظَلَمْنَاهُ", 1, "name", "حرف شرط جازم"),  # a لام on قد answers an oath
    ("وَإِنْ كَانَ ذَلِكَ لَأَضْرِبَنَّهُ", 0, "name", "حرف شرط جازم"),  # a لام and نّ after a complete كان: an oath's answer
    ("إِنْ تَزُرْنَا لَنَحْنُ أَسْعَدُ النَّاسِ", 0, "name", "حرف شرط جازم"),  # no ناسخ after it: a condition
    ("إِنْ كَانَ يَقُولُ إِنَّهُ لَصَادِقٌ فَقَدْ كَذَبَ", 0, "name", "حرف شرط جازم"),  # the لام is the said إنّ's
    ("إِنْ كَانَ ذَلِكَ فَلَقَدْ صَدَقَ", 0, "name", "حرف شرط جازم"),  # the لام is in the answer, after its ف
    ("إِنْ كَانَ رَسُولُ اللَّهِ لَيُقَبِّلُ بَعْضَ أَزْوَاجِهِ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a present verb
    ("إِنْ كَانَ وَعْدُ رَبِّنَا لَمَفْعُولًا", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # 17:108, a noun
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ فِي الدَّارِ لَقَدْ ظَلَمْنَاهُ", 1, "name", "حرف شرط جازم"),  # a لام on قد answers an oath
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ يَصْدُقُ لَقَدْ ظَلَمْنَاهُ", 1, "name", "حرف شرط جازم"),  # قد, after a verb خبر
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ لَصَدَقَ", 1, "name", "حرف شرط جازم"),  # a لام on a past verb answers an oath
    ("وَاللَّهِ إِنْ كُنْتَ لَنِعْمَ الصَّاحِبُ", 1, "name", "إن المخففة من الثقيلة، مهملة"),  # nothing after كان to be its خبر but the لام's word
    ("وَاللَّهِ إِنْ زَيْدٌ لَقَدْ قَامَ", 1, "name", "إن المخففة من الثقيلة، مهملة"),  # an oath does not take the لام on قد before a noun
    ("وَاللَّهِ إِنْ زَيْدٌ لَنِعْمَ الرَّجُلُ", 1, "name", "إن المخففة من الثقيلة، مهملة"),  # nor on a frozen verb
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ قَبْلَ الْيَوْمِ لَقَدْ ظَلَمْنَاهُ", 1, "name", "حرف شرط جازم"),  # a ظرف may be كان's خبر: the لام answers the oath
    ("وَاللَّهِ إِنْ كَانُوا مِنْ قَبْلُ لَفِي ضَلَالٍ مُبِينٍ", 1, "name", "إن المخففة من الثقيلة، مهملة"),  # a bare جار with no مبتدأ answers no oath (3:164)
    ("إِنْ كُنْتُ قَبْلَ الْيَوْمِ لَقَدْ نَصَحْتُكَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # no oath: لقد answers no condition without ف
    ("وَإِنْ كَانَ ذَلِكَ لَيَنْدَمَنَّ", 0, "name", "حرف شرط جازم"),  # the nun of emphasis: an oath's answer
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ صَادِقًا لَأَنْتَ أَكْذَبُ النَّاسِ", 1, "name", "حرف شرط جازم"),  # after a noun خبر told
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ يَصْدُقُ لَأَنْتَ أَكْذَبُ النَّاسِ", 1, "name", "حرف شرط جازم"),  # after a verb خبر told
    ("إِنْ كَانَ ذَلِكَ فَزَيْدٌ لَكَرِيمٌ", 0, "name", "حرف شرط جازم"),  # after the answer's ف
    ("إِنْ كَانَ ذَلِكَ قَالَ إِنَّهُ لَصَادِقٌ", 0, "name", "حرف شرط جازم"),  # after another إنّ
    ("سَأَزُورُكَ إِنْ كُنْتَ فِي الْبَيْتِ وَلَقَدْ وَعَدْتُكَ", 1, "name", "حرف شرط جازم"),  # a و before it: another sentence
    ("إِنْ كَانَ زَيْدٌ فِي الْبَيْتِ وَلَزَيْدٌ كَرِيمٌ", 0, "name", "حرف شرط جازم"),  # the same, on a noun
    ("وَإِنْ كَانَتْ لَكَبِيرَةً إِلَّا عَلَى الَّذِينَ هَدَى اللَّهُ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # 2:143 whole: the لام rules out النافية
    ("وَإِنْ كَانُوا مِنْ قَبْلُ لَفِي ضَلَالٍ مُبِينٍ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # 62:2, a جار
    ("وَإِنْ يَكَادُ الَّذِينَ كَفَرُوا لَيُزْلِقُونَكَ بِأَبْصَارِهِمْ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # 68:51, a present ناسخ in raf'
    ("إِنْ تَكُنْ لَصَادِقًا", 0, "name", "حرف شرط جازم"),  # a ناسخ typed in jazm: the condition put it there
    ("وَاللَّهِ إِنْ كَانَ ذَلِكَ لَيَقُولُنَّ", 1, "name", "حرف شرط جازم"),  # the nun of emphasis after a damma
    ("وَاللَّهِ إِنْ كَانَ ذَلِكَ لَتُبْلَوُنَّ", 1, "name", "حرف شرط جازم"),
    ("إِنْ كَانَ زَيْدٌ لَقَائِمٌ", 0, "name", "حرف شرط جازم"),  # a noun typed in raf' is no خبر كان
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ فِي الدَّارِ لَأَنْتَ أَكْرَمُ النَّاسِ", 1, "name", "حرف شرط جازم"),  # nor a pronoun of raf'
    ("وَاللَّهِ إِنْ ظَنَنْتَ زَيْدًا كَرِيمًا لَأَنْتَ مُخْطِئٌ", 1, "name", "حرف شرط جازم"),  # nor ظن's second object
    # once the ناسخ holds its خبر, or a ف, an إنّ or a و opens what follows, a لام after it answers the oath
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ صَادِقًا لَفِي قَوْلِهِ حِكْمَةٌ", 1, "name", "حرف شرط جازم"),
    ("وَاللَّهِ إِنْ كَادَ زَيْدٌ يَمُوتُ لَفِي ذَلِكَ عِبْرَةٌ", 1, "name", "حرف شرط جازم"),  # كاد's verb, tagged MOD
    ("وَاللَّهِ إِنْ ظَنَنْتُ زَيْدًا قَائِمًا لَفِي الدَّارِ عَمْرٌو", 1, "name", "حرف شرط جازم"),  # ظن's second object
    ("وَاللَّهِ إِنْ كَانَ ذَلِكَ إِنَّ فِي ذَلِكَ لَعِبْرَةً", 1, "name", "حرف شرط جازم"),
    ("وَاللَّهِ إِنْ كَانَ ذَلِكَ وَلَإِلَى اللَّهِ مَصِيرُهُ", 1, "name", "حرف شرط جازم"),
    ("وَإِنْ كُنَّا يَوْمَ الْقِيَامَةِ لَخَاسِرِينَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a ظرف before the خبر
    ("وَإِنْ ظَنَنْتُ زَيْدًا يَوْمَ الْجُمُعَةِ لَقَائِمًا", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # ظن's ظرف
    ("وَإِنْ ظَنَنْتُهُ ظَنًّا لَصَادِقًا", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # ظنًّا a مفعول مطلق, not the second object
    ("وَإِنْ كَانُوا جَمِيعًا لَمُحْضَرِينَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a حال hung on كان
    ("وَاللَّهِ إِنْ كَادَ زَيْدٌ لَيَخْرُجَنْ", 1, "name", "حرف شرط جازم"),  # the light nun of emphasis
    ("وَاللَّهِ إِنْ قُمْتَ لَفِي ذَلِكَ خَيْرٌ", 1, "name", "حرف شرط جازم"),  # no ناسخ after إن
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ يَقُومُ لَفِي ذَلِكَ خَيْرٌ", 1, "name", "حرف شرط جازم"),  # كان's خبر a verb
    ("وَإِنْ كَادُوا جَمِيعًا لَيَفْتِنُونَكَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a حال hung on كاد
    ("وَإِنْ ظَنَنْتُكَ فِي أَمْرِكَ لَصَادِقًا", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a جار hung on ظن
    ("وَإِنْ كَادَ زَيْدٌ لَيَظُنُّ ذَلِكَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # the root's own نّ, in raf'
    ("وَاللَّهِ إِنْ كَادَ زَيْدٌ لَيَخْرُجَنّ", 1, "name", "حرف شرط جازم"),  # the nun of emphasis, its fatha untyped
    ("إِنْ تَكُونُوا لَصَادِقِينَ", 0, "name", "حرف شرط جازم"),  # the five verbs' nun dropped for jazm
    ("وَاللَّهِ إِنْ رَأَيْتَهُ لَفِي ذَلِكَ عِبْرَةٌ", 1, "name", "حرف شرط جازم"),  # the جار opens a nominal clause
    ("وَاللَّهِ إِنْ كَانَ زَيْدٌ صَادِقًا لَفِي الْجَنَّةِ يَسْكُنُ", 1, "name", "حرف شرط جازم"),  # كان holds its noun خبر, so the لام answers the oath (3:158)
    ("وَاللَّهِ إِنْ كَادَ زَيْدٌ يَمُوتُ لَفِي الْجَنَّةِ يَسْكُنُ", 1, "name", "حرف شرط جازم"),  # كاد holds its verb خبر
    ("إِنْ هَذَانِ لَسَاحِرَانِ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # 20:63: the لام on the خبر of a noun
    ("إِنْ زَيْدٌ لَقَائِمٌ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # the خبر in raf'
    ("إِنْ زَيْدٌ لَفِي الدَّارِ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a جار خبر
    ("إِنْ زَيْدٌ لَيَقُومُ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a present verb خبر
    ("إِنْ هُوَ لَصَادِقٌ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # هُوَ's fatha is its build, no nasb
    ("إِنْ زَيْدًا لَقَائِمٌ", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # the noun typed in nasb
    ("إِنْ عِنْدَكُمْ مِنْ سُلْطَانٍ بِهَذَا", 0, "name", "إن النافية"),  # 10:68: no لام, no verb
    ("إِنْ زَيْدٌ قَائِمٌ", 0, "name", "إن النافية"),  # no لام tells it from the negation
    ("إِنْ زَيْدٌ بَخِيلٌ فَلِمَ تَلُومُهُ", 0, "name", "إن النافية"),  # a verb after the ف is another clause's, no condition
    ("وَإِنْ أَحَدٌ مِنَ الْمُشْرِكِينَ اسْتَجَارَكَ فَأَجِرْهُ", 0, "name", "حرف شرط جازم"),  # 9:6: a verb explains the one left out
    ("إِنِ امْرُؤٌ هَلَكَ لَيْسَ لَهُ وَلَدٌ", 0, "name", "حرف شرط جازم"),  # 4:176
    ("إِنْ أَحَدٌ جَاءَكَ لَأُكْرِمَنَّهُ", 0, "name", "حرف شرط جازم"),  # the لام on the nun of emphasis answers an oath
    ("إِنْ زَيْدًا لَقِيتَهُ فَأَكْرِمْهُ", 0, "name", "حرف شرط جازم"),  # a verb after the nasb noun: the condition (الاشتغال)
    ("إِنْ زَيْدًا مَرَرْتَ بِهِ فَسَلِّمْ عَلَيْهِ", 0, "name", "حرف شرط جازم"),  # the pronoun on the verb's جار holds the noun
    ("إِنْ زَيْدًا قَامَ أَبُوهُ", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # the verb has its own doer: a خبر, no condition
    ("فَإِنِ امْرُؤٌ قَاتَلَهُ أَوْ شَاتَمَهُ فَلْيَقُلْ إِنِّي صَائِمٌ", 0, "name", "حرف شرط جازم"),  # the hadith of fasting
    ("وَاللَّهِ إِنْ أَحَدٌ زَارَكَ لَزَيْدٌ خَيْرٌ مِنْهُ", 1, "name", "حرف شرط جازم"),  # a لام after the verb answers the oath
    ("إِنْ أَحَدٌ يَعْلَمُ الْغَيْبَ", 0, "name", "إن النافية"),  # a present verb is the خبر, not a condition
    ("إِنِ الَّذِينَ كَفَرُوا فِي غُرُورٍ", 0, "name", "إن النافية"),  # the verb is the relative's صلة
    ("إِنْ عِنْدَكُمْ مِنْ سُلْطَانٍ بِهَذَا أَتَقُولُونَ عَلَى اللَّهِ مَا لَا تَعْلَمُونَ", 0, "name", "إن النافية"),  # 10:68 in full
    ("إِنِ الَّذِي قَامَ لَصَادِقٌ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # the صلة's verb is not the condition's
    ("إِنِ الْمُسْلِمَاتِ صَادِقَاتٌ", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # a feminine plural's kasra is its nasb
    ("إِنِ الْمُسْلِمِينَ صَادِقُونَ", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # the ين of a sound plural is its nasb
    ("إِنِ الزَّيْدَيْنِ قَائِمَانِ", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # fatha before ي, kasra on ن: two, whatever the tag
    ("إِنْ عَيْن جَارِيَةٌ", 0, "name", "إن النافية"),  # no kasra typed on the ن: a single noun may end so
    ("إِنْ فِي ذَلِكَ لَعِبْرَةً", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # a خبر put first: the لام goes on the nasb noun
    ("إِنْ عِنْدَكَ لَخَيْرًا كَثِيرًا", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # a ظرف put first: the لام goes on the nasb noun
    ("إِنْ مِسْكِينٌ لَصَادِقٌ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a single noun's own ين is no pair's nasb
    ("إِنِ الَّذِي ظَلَمَكَ جَاءَكَ فَأَكْرِمْهُ", 0, "name", "حرف شرط جازم"),  # past the صلة, the verb that explains
    ("إِنْ زَيْدًا قَامَ إِلَى عَمْرٍو", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # no pronoun on the جار: no الاشتغال
    ("إِنْ زَيْدٌ قَامَ أَبُوهُ", 0, "name", "إن النافية"),  # the verb has its own doer
    ("إِنْ أَحَدٌ فِي الدَّارِ وَلَقَدْ بَحَثْتُ", 0, "name", "إن النافية"),  # a لام after a و opens another sentence; I am no hidden أحد
    ("إِنْ زَيْدٌ بَخِيلٌ فَقَدْ أَعْطَاكَ", 0, "name", "إن النافية"),  # a verb after the ف is another clause's
    ("إِنْ أَحَدٌ فِي الدَّارِ فَخَرَجَ", 0, "name", "إن النافية"),  # with no قد too
    ("النَّاسُ مَجْزِيُّونَ بِأَعْمَالِهِمْ إِنْ خَيْرًا فَخَيْرٌ وَإِنْ شَرًّا فَشَرٌّ", 3, "name", "حرف شرط جازم"),  # كان left out, its خبر kept before the ف
    ("إِنْ خَيْرٌ فَخَيْرٌ", 0, "name", "حرف شرط جازم"),  # كان left out, its اسم kept
    ("إِنِ الشَّيَاطِينُ لَكَاذِبُونَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a broken plural's ين with its damma typed is no nasb
    ("إِنْ مَسَاكِينُ جَاءُوا فَأَعْطِهِمْ", 0, "name", "حرف شرط جازم"),  # nor here
    ("إِنْ عِنْدِي مِنْ مَالٍ وَقَدْ ذَهَبَ", 0, "name", "إن النافية"),  # a ظرف is no doer; the verb after و is another sentence's
    ("إِنْ أَحَدٌ فِي الدَّارِ وَقَدْ خَرَجَ", 0, "name", "إن النافية"),  # a verb after و opens another sentence
    ("إِنْ أَحَدٌ فِي الدَّارِ وَخَرَجَ", 0, "name", "إن النافية"),  # with no قد too
    ("إِنْ فِي الدَّارِ رَجُلٌ قَامَ", 0, "name", "إن النافية"),  # a جار put first is no doer; the verb is the noun's صفة
    ("إِنْ أَحَدٌ مِمَّنْ ظَلَمَكَ فِي الدَّارِ", 0, "name", "إن النافية"),  # a صلة inside the noun's words explains no dropped verb
    ("إِنْ زَيْدٌ ضَرَبْتُهُ", 0, "name", "إن النافية"),  # a verb of another person holds no hidden doer for the noun
    ("إِنْ أَنْتَ قُمْتَ فَقُمْ", 0, "name", "حرف شرط جازم"),  # a verb of the noun's own person does
    ("إِنِ الْمِسْكِين لَصَادِقٌ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a single noun's ين is no nasb
    ("إِنْ زَيْدٌ لَيْسَ بِقَائِمٍ", 0, "name", "إن النافية"),  # a frozen verb is no condition's
    ("إِنْ زَيْدٌ قَدْ قَامَ", 0, "name", "إن النافية"),  # nor one behind قد
    ("إِنْ زَيْدٌ مَا قَامَ", 0, "name", "إن النافية"),  # nor one behind ما
    ("إِنْ أَحَدٌ مِمَّنْ ظَلَمَكَ لَنَادِمٌ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # a صلة inside the noun's words, no oath: the لام is the خبر's
    ("إِنْ رَجُلٌ صَدَقَ لَنَاجٍ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # no oath: the verb a صفة, the لام the خبر's
    ("إِنْ أَحَدٌ قَالَ لَزَيْدٌ أَفْضَلُ مِنْكَ فَكَذِّبْهُ", 0, "name", "حرف شرط جازم"),  # the لام inside what the verb says
    ("إِنْ زَيْدٌ لَرَجُلٌ صَدَقَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # the لام before the verb is the خبر's
    ("وَاللَّهِ إِنْ زَيْدٌ قَامَ أَبُوهُ لَكَرِيمٌ", 1, "name", "إن المخففة من الثقيلة، مهملة"),  # the doer stands before the لام: the verb explains nothing
    ("إِنْ زَيْدًا رَآنِي", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # a pronoun of the first person goes back to no noun
    ("إِنْ فِي الدَّارِ رَجُلًا", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # the noun a fronted جار leaves after it
    ("إِنْ رَجُلٌ يَعْرِفُ الْحَقَّ جَاءَكَ فَأَكْرِمْهُ", 0, "name", "حرف شرط جازم"),  # a present صفة on the noun is passed
    ("إِنْ رَجُلٌ لَيْسَ لَهُ مَالٌ جَاءَكَ فَأَعْطِهِ", 0, "name", "حرف شرط جازم"),  # and a frozen one
    ("إِنْ رَجُلٌ يُرِيدُ أَنْ يَذْهَبَ جَاءَكَ فَأَعْطِهِ", 0, "name", "حرف شرط جازم"),  # أنْ before its verb opens no clause
    ("إِنْ ذُو مَالٍ جَاءَكَ فَأَكْرِمْهُ", 0, "name", "حرف شرط جازم"),  # ذو is third person, whatever the tag
    ("إِنْ زَيْدٌ وَعَمْرٌو جَاءَا فَأَكْرِمْهُمَا", 0, "name", "حرف شرط جازم"),  # a noun joined by و is the noun's
    ("إِنْ رَجُلٌ مِنْ قَوْمِكَ وَامْرَأَةٌ جَاءَاكَ فَأَكْرِمْهُمَا", 0, "name", "حرف شرط جازم"),  # no doer before its verb
    ("إِنْ زَيْدًا أَكْرَمْتَ أَخَاهُ فَأَكْرِمْهُ", 0, "name", "حرف شرط جازم"),  # الاشتغال through what the verb works on
    ("إِنْ زَيْدًا مَرَرْتَ بِهِ فَسَلِّمْ عَلَيْهِ", 0, "name", "حرف شرط جازم"),  # and through its جار
    ("إِنْ زَيْدًا قَامَ أَبُوهُ فَأَكْرِمْهُ", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # never through its doer, nor the answer's pronoun
    ("إِنْ هُوَ لَمْ يَحْمِلْ عَلَى النَّفْسِ ضَيْمَهَا فَلَيْسَ إِلَى حُسْنِ الثَّنَاءِ سَبِيلُ", 0, "name", "حرف شرط جازم"),  # لم turns it past
    ("إِنْ عَمَلًا صَالِحًا فَجَزَاءٌ حَسَنٌ", 0, "name", "حرف شرط جازم"),  # كان left out, its خبر kept with its صفة
    ("إِنْ عِنْدَكَ فَخُذْ", 0, "name", "حرف شرط جازم"),  # or a ظرف kept alone
    ("إِنْ زَيْدًا إِنَّهُ صَادِقٌ", 0, "name", "إن المخففة من الثقيلة، عاملة"),  # no ف, no answer: an إنّ sentence is the خبر (22:17)
    ("إِنْ أَحَدٌ مَعَكَ فَيُعِينَكَ", 0, "name", "إن النافية"),  # كان keeps no اسم and خبر both; the ف after a negation
    ("إِنْ أَحَدٌ يَعْرِفُ رَجُلًا سَافَرَ", 0, "name", "إن النافية"),  # the first verb is the خبر; one inside its words explains nothing
    ("إِنْ أَنَا قُمْتُ فَقُمْ مَعِي", 0, "name", "حرف شرط جازم"),  # the verb is of the pronoun's person
    ("إِنْ أَنَا مِمَّنْ ظَلَمَكَ", 0, "name", "إن النافية"),  # a verb of another person is not the pronoun's
    ("إِنْ زَيْدٌ لَنِعْمَ الرَّجُلُ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # the لام on a frozen verb
    ("إِنْ زَيْدٌ لَنِعْمَ الرَّجُلُ", 2, "name", "فعل جامد لإنشاء المدح"),
    ("إِنْ زَيْدٌ لَعَسَى أَنْ يَقُومَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),
    ("إِنْ زَيْدٌ لَقَدْ قَامَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # and on قد with its verb
    ("إن زيدا قائم", 0, "name", "حرف ناسخ مشبه بالفعل"),  # typed with no sukun: إنّ without its shadda
    ("مَا قَامَ زَيْدٌ لَكِنْ إِنَّ عَمْرًا قَائِمٌ", 4, "name", "حرف ناسخ مشبه بالفعل"),  # لكنْ, light, is no إنْ: every axis safe on it
    ("إِنْ فَزَيْدٌ قَائِمٌ", 0, "name", "إن النافية"),  # a ف ends the clause before any noun
    ("إِنْ زَيْدٌ فِي الدَّارِ لَكِنَّهُ خَرَجَ", 0, "name", "إن النافية"),  # a sister of إنّ opens another sentence
    ("إِنْ أَحَدٌ فِي الدَّارِ وَالنَّاسُ نَامُوا", 0, "name", "إن النافية"),  # a و not hung on the noun opens another sentence
    ("إِنْ زَيْدٌ ضَرَبَهُ الْمُعَلِّمُونَ", 0, "name", "إن النافية"),  # the verb has its own doer after it
    ("إِنْ زَيْدٌ قَامَ هَذَا", 0, "name", "إن النافية"),  # a built doer too
    ("وَاللَّهِ إِنْ رَجُلٌ صَدَقَ لَنَاجٍ", 1, "name", "إن المخففة من الثقيلة، مهملة"),  # one noun is no oath's answer: the لام is the خبر's
    ("إِنْ خَيْرًا مِنْ ذَلِكَ فَخُذْهُ", 0, "name", "حرف شرط جازم"),  # a جار after a nasb noun is that noun's: كان left out
    ("إِنْ زَيْدٌ لَلَيْسَ قَائِمًا", 0, "name", "إن النافية"),  # no لام on ليس: «ولا يلي ذي اللام ما قد نفيا»
    ("إِنْ أَحَدٌ جَاءَنِي", 0, "name", "إن النافية"),  # nothing after the verb, nothing before: no answer
    ("وَاللَّهِ إِنْ أَحَدٌ جَاءَنِي", 1, "name", "إن النافية"),  # an oath before it is no answer
    ("قَالَ إِنْ أَحَدٌ جَاءَنِي", 1, "name", "إن النافية"),  # nor a verb of saying
    ("أُكْرِمُكَ إِنْ أَحَدٌ زَارَنِي", 1, "name", "حرف شرط جازم"),  # the answer put before it
    ("إِنِ السَّلَاطِين لَظَالِمُونَ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # no vowel on the ن: unknown, no nasb
    ("إِنِ امْرُؤٌ هَلَكَ لَيْسَ لَهُ وَلَدٌ وَلَهُ أُخْتٌ فَلَهَا نِصْفُ مَا تَرَكَ", 0, "name", "حرف شرط جازم"),  # 4:176 in full
    ("إِنْ رَجُلٌ وَامْرَأَةٌ جَاءَا فَأَكْرِمْهُمَا", 0, "name", "حرف شرط جازم"),  # a و hung on the noun joins it
    # after the explaining verb only a فاء, an oath's لام or a verb standing bare opens the answer
    ("إِنْ أَحَدٌ خَرَجَ مِنَ الدَّارِ", 0, "name", "إن النافية"),  # the verb's own جار is no answer
    ("إِنْ أَحَدٌ رَأَى زَيْدًا", 0, "name", "إن النافية"),  # nor its object
    ("إِنْ أَحَدٌ رَأَى زَيْدًا أَخْبَرَنِي", 0, "name", "حرف شرط جازم"),  # a past verb standing bare is the answer
    ("إِنْ أَحَدٌ زَارَنِي أُكْرِمْهُ", 0, "name", "حرف شرط جازم"),  # so is a jussive one
    ("إِنْ أَحَدٌ جَاءَنَا يَسْأَلُ عَنْكَ", 0, "name", "إن النافية"),  # one in raf' is a حال
    ("إِنْ أَحَدٌ أَرَادَ أَنْ يَخْرُجَ", 0, "name", "إن النافية"),  # a verb under a particle is no answer
    ("إِنْ أَحَدٌ جَاءَ وَجَلَسَ", 0, "name", "إن النافية"),  # nor one joined on
    ("وَإِنْ أَحَدٌ مِنَ الْمُشْرِكِينَ اسْتَجَارَكَ فَأَجِرْهُ", 5, "name", "فعل أمر"),  # 9:6: a command, not the noun فاجر
    ("إِنْ أَحَدٌ قَدْ جَاءَ فَسَأَلَ عَنْكَ", 0, "name", "إن النافية"),  # a verb after قد is no condition's
    ("إِنْ أَحَدٌ مَا جَاءَ فَسَأَلَ عَنْكَ", 0, "name", "إن النافية"),  # nor one after ما
    ("إِنْ عِنْدَنَا أَحَدٌ خَرَجَ فَعَادَ", 0, "name", "إن النافية"),  # a خبر put first makes a noun sentence
    ("إِنْ رَجُلٌ صَدَقَ لَنَاجٍ وَالْكَاذِبُ هَالِكٌ", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # no oath: the لام is the خبر's
    ("وَإِنْ أَحَدٌ جَاءَنِي", 0, "name", "إن النافية"),  # a joined و is no answer put first
    ("أَقُومُ إِنْ أَحَدٌ جَاءَ", 1, "name", "حرف شرط جازم"),  # a verb not of saying before it is the answer
    ("قُلْتُ لَكَ إِنْ أَحَدٌ جَاءَنِي", 2, "name", "إن النافية"),  # a verb of saying with its own words after it
    ("قَالَ زَيْدٌ إِنْ أَحَدٌ جَاءَنِي", 2, "name", "إن النافية"),
    ("قَالَ زَيْدٌ أُكْرِمُكَ إِنْ أَحَدٌ زَارَنِي", 3, "name", "حرف شرط جازم"),  # the speech holds the answer put first
    ("إِنْ أَحَدٌ فِي الدَّارِ وَالنَّاسُ نَامُوا عَنْهُ", 0, "name", "إن النافية"),  # a verb past a new sentence's و
    ("إِنْ أَحَدٌ عِنْدَنَا وَالْقَوْمُ رَحَلُوا فَبَقِينَا وَحْدَنَا", 0, "name", "إن النافية"),  # with a ف after it too
    ("إِنْ رَجُلٌ صَدَقَ لَهُوَ النَّاجِي", 0, "name", "إن المخففة من الثقيلة، مهملة"),  # no oath: the لام is the خبر's, not alone
    ("إِنْ أَحَدٌ زَارَنِي أَكْرَمْتُهُ", 0, "name", "حرف شرط جازم"),  # a past answer, its تُ's damma no raf'
    ("إِنْ زَيْدٌ لَيْسَ بِقَائِمٍ فَقَدْ كَذَبْتَ", 0, "name", "إن النافية"),  # ليس, frozen, is no condition's verb
    ("إِنْ أَحَدٌ ظَلَمَهُ هَؤُلَاءِ فَانْصُرْهُ", 0, "name", "إن النافية"),  # a built doer of its own: أحد is not its doer
    ("إِنْ فِي الدَّارِ رَجُلٌ قَامَ فَأَكْرِمْهُ", 0, "name", "إن النافية"),  # a خبر put first: no verb explains a جار
    ("إِنْ أَنْتَ أَكْرَمْتَنِي أَكْرَمْتُكَ", 0, "name", "حرف شرط جازم"),  # a pronoun's own person on its verb
    ("إِنْ زَيْدٌ ضَرَبْتُهُ فَقَدْ أَدَّبْتُهُ", 0, "name", "إن النافية"),  # another person's verb, though an answer follows
    ("إِنِ الَّذِي ظَلَمَكَ ضَرَبَهُ زَيْدٌ", 0, "name", "إن النافية"),  # a صلة's verb explains nothing
    ("إِنْ زَيْدٌ ضَرَبْتُهُ بَكَى فَاعْتَذَرْتُ", 0, "name", "إن النافية"),  # only the first verb past the noun's words may
    ("اُطْلُبْهُ إِنْ فِي السُّوقِ فَفِي السُّوقِ", 1, "name", "حرف شرط جازم"),  # كان left out, a جار its خبر
    ("إِنْ أَحَدٌ رَأَى الَّذِي سَرَقَ", 0, "name", "إن النافية"),  # a صلة's verb under the condition verb's object is no answer
    ("إِنْ أَحَدٌ قَالَ إِنَّ زَيْدًا خَرَجَ", 0, "name", "إن النافية"),  # nor a verb inside its said sentence
    ("إِنْ أَحَدٌ قَالَ اذْهَبْ", 0, "name", "إن النافية"),  # nor its speech, straight on a verb of saying
    ("إِنْ أَحَدٌ زَارَنِي أَكْرَمْتُهُ", 0, "name", "حرف شرط جازم"),  # nearest case: a bare answer, hung straight on the verb
    ("يَا زَيْدُ إِنْ أَحَدٌ جَاءَنِي", 2, "name", "إن النافية"),  # a called noun is no answer put first
    ("بَلْ إِنْ أَحَدٌ جَاءَنِي", 1, "name", "إن النافية"),  # nor a bare particle
    ("أَنْتَ ظَالِمٌ إِنْ أَحَدٌ ظَلَمَكَ", 2, "name", "حرف شرط جازم"),  # a nominal sentence is
    ("يَا زَيْدُ أُكْرِمُكَ إِنْ أَحَدٌ زَارَنِي", 3, "name", "حرف شرط جازم"),  # and a verb after the call
    ("إِنْ أَحَدٌ جَاءَنَا يَسْأَل عَنْكَ", 0, "name", "إن النافية"),  # a present typed bare may be a حال: no answer
    ("إِنْ أَحَدٌ جَاءَكَ يَسْأَلْكَ", 0, "name", "حرف شرط جازم"),  # one stilled in jazm is
    ("إِنْ أَحَدٌ زَارَكُمْ تَجِدُوهُ كَرِيمًا", 0, "name", "حرف شرط جازم"),  # and one of the five with its nun dropped
    ("إِنْ أَحَدٌ زَارَكُمْ تَجِدُونَهُ كَرِيمًا", 0, "name", "إن النافية"),  # its nun kept, raf': a حال may be
    ("فَأَمْسِكُوهُنَّ فِي الْبُيُوتِ", 0, "name", "فعل أمر"),  # 4:15: the plural's alif, gone before a pronoun, off a joined ف
    ("إِنْ جَاءَكُمْ أَحَدٌ فَأَجِيرُوهُ", 3, "name", "فعل أمر"),
    ("فُتِحَ الْبَابُ", 0, "name", "فعل مجهول"),  # a ف with a damma is the root's: no تِحْ joined by a فَ, built on a fatha
    ("وُعِدَ زَيْدٌ", 0, "name", "فعل مجهول"),  # nearest case, the و
    ("فَأَجِيرُوهُ", 0, "name", "فعل أمر"),  # the cut أَجِيرُوهُ is أَجِيرُوا with its object, as the uncut word is
    ("وَأَجِيرُوهُ", 0, "name", "فعل أمر"),  # nearest case, the و
    # إلّا before a jussive present verb is إنْ merged into لا: a condition, never the exception (9:40, 9:39)
    ("إِلَّا تَنْصُرُوهُ فَقَدْ نَصَرَهُ اللَّهُ", 0, "name", "حرف شرط جازم مدغم في لا النافية"),
    ("إِلَّا تَنْصُرُوهُ فَقَدْ نَصَرَهُ اللَّهُ", 1, "name", "فعل الشرط"),
    ("إِلَّا تَنْفِرُوا يُعَذِّبْكُمْ عَذَابًا أَلِيمًا", 2, "name", "جواب الشرط"),
    ("إِلَّا تَدْرُسْ تَرْسُبْ", 0, "name", "حرف شرط جازم مدغم في لا النافية"),  # stilled, not a dropped nun
    ("مَا زَيْدٌ إِلَّا يَكْتُبُ", 2, "name", "أداة حصر"),  # nearest case: a raf' verb, restriction
    ("إلا تنصروه فقد نصره الله", 0, "name", "حرف شرط جازم مدغم في لا النافية"),  # its hamza written, no vowels
    ("وَإِلَّا تَغْفِرْ لِي وَتَرْحَمْنِي أَكُنْ مِنَ الْخَاسِرِينَ", 0, "name", "حرف شرط جازم مدغم في لا النافية"),  # 11:47
    # a كان sister takes no object: the word its restricting إلا hands it is its خبر (36:29)
    ("إِنْ كَانَتْ إِلَّا صَيْحَةً وَاحِدَةً", 3, "role", "خبر كان"),
    ("وَمَا كَانَ جَوَابَهُمْ إِلَّا قَوْلُهُمْ", 2, "role", "خبر كان"),  # typed: the raf' word is the اسم, the nasb one the خبر
    ("وَمَا كَانَ جَوَابَهُمْ إِلَّا قَوْلُهُمْ", 4, "role", "اسم كان"),
    ("مَا كَانَ زَيْدٌ إِلَّا قَائِمًا", 4, "role", "خبر كان"),  # nearest case: the اسم already raf'
    ("لَا تَعْبُدُوا إِلَّا اللَّهَ", 3, "role", "مفعول به"),  # nearest case: a full verb keeps its object
    # after إذا nothing but the لا puts the verb in jazm, so that لا forbids
    ("إِذَا جَاءَ زَيْدٌ لَا تُكَلِّمْهُ", 3, "reason", "لا الناهية"),
    # a particle left idle before a verb in raf' governs nothing: it is named for the work it still does
    ("يَوْمَ الصُّلَيْفَاءِ لَمْ يُوفُونَ بِالْجَارِ", 2, "reason", "حرف نفي وقلب مهمل"),
    ("أَنْ تَقْرَآنِ عَلَى أَسْمَاءَ وَيْحَكُمَا", 0, "reason", "حرف مصدري مهمل"),
    ("لَمْ تُكَلِّمُونِّي فِي الْأَمْرِ", 0, "name", "حرف نفي وقلب مهمل"),
    ("أَرَدْتُ أَنْ يَكْتُبُونَ الدَّرْسَ", 1, "name", "حرف مصدري مهمل"),  # a root with no ن of its own: the five verbs' nun
    ("عَلِمْتُ أَنْ يَكْتُبُونَ الدَّرْسَ", 1, "name", "أن المخففة من الثقيلة"),  # what a verb of the heart knows: أنّ lightened
    ("أَرَدْتُ أَنْ يَخُونَ", 1, "name", "حرف نصب"),  # nearest case: the nun may be the root's (خَانَ), one doer's verb in nasb
    ("لَنْ يَكْتُبُونَ", 0, "name", "حرف نصب"),  # nearest case: لن is never left idle
    ("أَرَدْتُ أَنْ يَبْنِيَانِ", 1, "name", "حرف مصدري مهمل"),  # a root ending ي, but only the pair's nun takes a kasra
    ("أَرَدْتُ أَنْ يَبْنِيَانِهِ", 1, "name", "حرف مصدري مهمل"),  # the pair's nun before a pronoun written on it
    ("لَنْ يَبْنِيَانِ", 0, "name", "حرف نصب"),  # nearest case: not even before the pair's nun
    ("ظَنَنْتُ أَنْ يَكْتُبُونَ الدَّرْسَ", 1, "name", "أن المخففة من الثقيلة"),
    ("اتَّخَذْتُ أَنْ يَكْتُبُونَ الدَّرْسَ", 1, "name", "حرف مصدري مهمل"),  # nearest case: a verb of turning knows nothing
    ("لَمْ يَكْتُبُوا", 0, "reason", "يجزم الفعل المضارع"),  # nearest case: the nun dropped, the لم governs
    ("يُرِيدُ أَنْ يَكْتُبَ", 1, "reason", "ينصب الفعل المضارع"),
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
    ("لِكَيْلَا تَأْسَوْا عَلَى مَا فَاتَكُمْ", 1, "sign", "حذف النون"),  # 57:23: كيلا with the لام of reason written on it
    ("لَنْ تَقْرَآ الْكِتَابَ", 1, "sign", "حذف النون"),  # an آ is a hamza and the pair's alif after it
    ("أَنْتُمَا تَقْرَآنِ الْكِتَابَ", 1, "sign", "ثبوت النون"),
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


@pytest.mark.parametrize("sentence, index, field, wrong", [
    ("اِهْدِنَا الصِّرَاطَ", 0, "sign", "حذف النون"),
    ("هُوَ يَظُنُّ ذَلِكَ", 1, "sign", "مبني"),                       # a root's doubled nun is no nun of emphasis
    # لو after a verb of wishing is the masdar particle the verb takes (2:109): it opens no condition
    ("وَدَّ كَثِيرٌ مِنْ أَهْلِ الْكِتَابِ لَوْ يَرُدُّونَكُمْ", 6, "name", "الشرط"),
    ("أُحِبُّ لَوْ تَزُورُنِي", 2, "name", "الشرط"),
    # ما المصدرية الظرفية is a particle: the picture's ma card must not make it an object (naming.finish keeps its family)
    ("لَا أَكْتُبُ مَا دُمْتُ مَرِيضًا", 2, "role", "مفعول به"),
    ("سَأَبْقَى مَا لَمْ تَأْذَنْ لِي", 1, "role", "مفعول به"),
    # a condition opens on a verb: إنْ before a negation with no verb after it opens none
    ("إِنْ لَا رَيْبَ فِيهِ", 0, "name", "شرط"),
    # written with no hamza, الا before a verb that lost its nun may be أَلَّا (أن + لا): no condition is sure
    ("الا تعبدوا الا الله", 0, "name", "شرط"),
    # a كان sister holding its خبر already takes no second one from its إلا (11:118)
    ("وَلَا يَزَالُونَ مُخْتَلِفِينَ إِلَّا مَنْ رَحِمَ رَبُّكَ", 4, "role", "خبر"),
    # a past read with its typed vowels keeps its first و or ف: no command ضَعُوا، رِحُوا joined on
    ("الرِّجَالُ وَضَعُوا الْكِتَابَ", 1, "name", "أمر"),
    ("الْقَوْمُ فَرِحُوا", 1, "name", "أمر"),
    # the masdar-as-state rule is kept to commands: a past verb's masdar is left to the other rules
    ("صَلَّى الرَّجُلُ جُلُوسًا", 2, "role", "حال"),
    # و + a raf' noun opens a second sentence only when both nouns are typed in raf'
    ("وَاللَّهِ إِنْ كَانَ ذَلِكَ وَلَإِلَى اللَّهِ مَصِيرُهُ", 4, "role", "مبتدأ"),
])
def test_card_field_is_not(sentence: str, index: int, field: str, wrong: str):
    assert wrong not in (_read(sentence)["words"][index][field] or "")


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
    ("لَوْ جَاءَ زَيْدٌ لَأَكْرَمْتُهُ", 1, "وجملة الشرط لا محل لها"),
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


@pytest.mark.parametrize("sentence, at, case, sign", [
    # the nun of emphasis builds the verb on the fatha with an object pronoun after it too; before ني the two
    # nuns are written as one doubled letter (لِيَلِيَنِّي مِنْكُمْ أُولُو الْأَحْلَامِ, Muslim)
    ("لِيَكْتُبَنَّهُ زَيْدٌ", 0, "mabni", "مبني على الفتح"),
    ("لِيَلِيَنِّي مِنْكُمْ أُولُو الْأَحْلَامِ", 0, "mabni", "مبني على الفتح"),
    ("لَيَأْتِيَنِّي زَيْدٌ", 0, "mabni", "مبني على الفتح"),
    ("لِيَضْرِبْنَهُ", 0, "mabni", "مبني على السكون"),  # the nun of women, read past its pronoun
    ("يَظُنُّنِي زَيْدٌ", 0, "raf'", "ضمة"),  # a root's doubled nun, a damma on it: no nun of emphasis
    ("يُكْرِمُنِي زَيْدٌ", 0, "raf'", "ضمة"),
])
def test_a_nun_on_a_verb_builds_it_past_its_pronoun(sentence: str, at: int, case: str, sign: str):
    word = _read(sentence)["words"][at]
    assert (word["case"], word["sign"]) == (case, sign), sentence


@pytest.mark.parametrize("sentence, at, case, sign", [
    # the kept nun and ني's نون الوقاية written as one doubled nun after the group's long vowel (6:80، 39:64)
    ("أَتُحَاجُّونِّي فِي اللَّهِ", 0, "raf'", "ثبوت النون"),
    ("أَفَغَيْرَ اللَّهِ تَأْمُرُونِّي", 2, "raf'", "ثبوت النون"),
    ("تَأْمُرُونَنِي", 0, "raf'", "ثبوت النون"),  # both nuns written
    ("هُمْ يَدْعُونِّي", 1, "raf'", "ثبوت النون"),  # read as one doer, but دَعَا has no ن to merge: the kept one
    ("لَا تَنْسَوْنِي", 1, "jazm", "حذف النون"),  # nearest case: one bare nun, the pronoun's: the verb's went
    ("لَا تُكَلِّمُونِّي فِي الْأَمْرِ", 1, "raf'", "ثبوت النون"),  # two nuns, so the verb's is kept: the لا denies, no ناهية
    # after لم too: a root's own ن after a long letter is a hollow verb's, whose long letter jazm drops (لَمْ يَخُنِّي)
    ("لَمْ تُكَلِّمُونِّي فِي الْأَمْرِ", 1, "raf'", "ثبوت النون"),
    ("لَنْ تُكَلِّمُونِّي فِي الْأَمْرِ", 1, "nasb", "حذف النون"),  # nearest case: a nasb particle takes the nun, the ن left is ني's
    ("لَا تُكَلِّمُونِي فِي الْأَمْرِ", 1, "jazm", "حذف النون"),  # nearest case: the pronoun's nun alone, the ناهية's jazm
    ("هُوَ يُعِينِّي عَلَى الْعَمَلِ", 1, "raf'", "ضمة مقدرة"),  # nearest case: after a ي, أَعَانَ's own nun merged into ني's
])
def test_the_five_verbs_nun_merged_into_the_pronouns_is_kept(sentence: str, at: int, case: str, sign: str):
    word = _read(sentence)["words"][at]
    assert (word["case"], word["sign"][:len(sign)]) == (case, sign), sentence


@pytest.mark.parametrize("word, merged", [
    ("أَتُحَاجُّونِّي", True),  # the kept nun and ني's written as one, after the group's long و (6:80)
    ("يُكْرِمَانِّي", True),  # after the pair's ا
    ("لَيَدْعُوَنِّي", False),  # nearest case: a fatha on the و makes it the root's, the doubled nun emphasis's
    ("يُعِينِّي", False),  # after a ي the nun may be the root's own (أَعَانَ)
    ("تَنْسَوْنِي", False),  # one nun only, the pronoun's
])
def test_a_doubled_nun_before_ni_merges_two_only_after_a_long_vowel(word: str, merged: bool):
    assert merged_nun(word, 2) is merged
    assert not merged or five_verb_nun(word, 2, False) is None  # the word alone never says whose nun it is: the root does


@pytest.mark.parametrize("sentence, at, case, sign", [
    # the pair's nun goes before the nun of emphasis (توالي الأمثال), so after a لا of prohibition the verb is in jazm by its loss
    ("وَلَا تَتَّبِعَانِّ سَبِيلَ الَّذِينَ لَا يَعْلَمُونَ", 1, "jazm", "حذف النون"),  # 10:89
    ("هُمَا يَتَّبِعَانِ السَّبِيلَ", 1, "raf'", "ثبوت النون"),  # nearest case: no nun of emphasis, the pair's own kept
    ("وَاللَّهِ لَتَذْهَبَانِّ", 1, "raf'", "ثبوت النون المحذوفة لتوالي الأمثال"),  # nearest case: in raf' too it goes, so three nuns do not meet
])
def test_the_pairs_nun_goes_before_the_nun_of_emphasis(sentence: str, at: int, case: str, sign: str):
    word = _read(sentence)["words"][at]
    assert (word["case"], word["sign"]) == (case, sign), sentence


@pytest.mark.parametrize("number, root, five", [
    ("p", "وخي", True),  # يَخُونِّي read as the group of وَخَى: their kept nun merged into ني's
    ("s", "خون", False),  # nearest case: one doer of خَانَ, the nun his root's own
])
def test_a_merged_nun_shows_the_five_verbs_raf_only_when_the_root_has_no_nun(number: str, root: str, five: bool):
    # a card as the analyser gives it, so the sign is read whichever reading it settles on
    card = {"word": "يَخُونِّي", "camel": {"number": number, "root": root, "enclitic": "1s_dobj", "weak_last": number == "p"}}
    assert (signs._present_sign(card, "raf'") == "ثبوت النون") is five


@pytest.mark.parametrize("sentence, at, case, sign", [
    # فاء السببية answering a pure negation or request: the present after it in nasb by a hidden أن (Ibn Aqil vol 4
    # p11-12: لا يقضى عليهم فيموتوا، ولا تطغوا فيه فيحل)
    ("وَلَا تَنَازَعُوا فَتَفْشَلُوا", 2, "nasb", "حذف النون"),
    ("لَا يُقْضَى عَلَيْهِمْ فَيَمُوتُوا", 3, "nasb", "حذف النون"),
    ("ذَاكِرُوا فَتَنْجَحُوا", 1, "nasb", "حذف النون"),
    ("هُمْ يَكْتُبُونَ فَيَتَعَلَّمُونَ", 2, "raf'", "ثبوت النون"),  # nearest case: the nun kept, a ف of sequence
    ("فَلْيَصُومُوا", 0, "jazm", "حذف النون"),  # nearest case: a لام الأمر between the ف and the verb
    ("لَا تَكْذِبِي فَتَخْسَرِي", 2, "nasb", "حذف النون"),  # the you-feminine verb: its ت after the ف
    ("إِنْ تَجْتَهِدُوا فَتَنْجَحُونَ", 2, "raf'", "ثبوت النون"),  # the nun kept: the ف ties the answer, a noun clause (V4, page unchecked)
    ("لَا تَكْذِبْ فَتَكُونَ مِنَ الْخَاسِرِينَ", 2, "nasb", "فتحة"),  # nearest case: one doer, the ن كَانَ's own
    ("وَلَا تَقْرَبَا هَذِهِ الشَّجَرَةَ فَتَكُونَا مِنَ الظَّالِمِينَ", 4, "nasb", "حذف النون"),  # 2:35, the pair's nun gone
])
def test_a_present_verb_whose_nun_went_after_a_fa_is_in_nasb(sentence: str, at: int, case: str, sign: str):
    word = _read(sentence)["words"][at]
    assert (word["case"], word["sign"][:len(sign)]) == (case, sign), sentence  # the ضمة's place follows it


@pytest.mark.parametrize("sentence, at, case", [
    # a present verb after a ف between the condition and its answer is in nasb or jazm (Ibn Aqil V4, page unchecked), so it is no
    # answer: the ف ties only an answer that could not be a condition (V4, page unchecked), and the answer comes after it
    ("إِنْ تَدْرُسُوا فَتَجْتَهِدُوا يُحِبَّكُمُ الْمُعَلِّمُ", 2, "nasb"),
    ("إِنْ تَدْرُسْ فَتَفْهَمَ تَنْجَحْ", 2, "nasb"),  # the fatha the reader typed stands
    ("مَنْ يَدْرُسْ فَيَنْجَحَ يَفْرَحْ", 2, "nasb"),
    ("إِنْ تَدْرُسْ فَتَسْتَعِدَّ تَنْجَحْ", 2, "nasb"),  # a doubled verb's fatha after the ف: nasb, so no answer either
])
def test_a_verb_after_fa_between_the_condition_and_its_answer_is_no_answer(sentence: str, at: int, case: str):
    words = _read(sentence)["words"]
    assert words[at]["case"] == case, sentence
    assert words[at + 1].get("name") == "جواب الشرط" and words[at + 1]["case"] == "jazm", sentence


@pytest.mark.parametrize("sentence, at, case", [
    # a لا joined on after a verb under لن only stresses the negation (لا زائدة لتوكيد النفي): لن governs this verb too
    ("لَنْ تَكْتُبُوا وَلَا تَقْرَءُوا", 3, "nasb"),
    ("لَنْ تَكْتُبُوا وَلَا تَقْرَءُونَ", 3, "raf'"),  # nearest case: one keeping its nun is in raf', the لا only negating
    ("لَنْ تُكَلِّمُونِي وَلَا تَأْمُرُونِّي", 3, "raf'"),  # so too a nun merged into ني's
    ("لَنْ يَرُدَّ الْكِتَابَ وَلَا يَمُدَّ يَدَهُ", 4, "nasb"),  # past the first verb's object
    ("لَمْ يَرُدَّ وَلَا يَمُدَّ", 3, "jazm"),  # nearest case: under لم, jazm both
    ("اكْتُبُوا وَلَا تَنْسَوْا", 2, "jazm"),  # nearest case: no nasb particle before, the لا forbids
    ("لَنْ أَكْتُبَ الْيَوْمَ لَا تَنْتَظِرُونِي", 4, "jazm"),  # nearest case: no و joins it, a new clause the لا forbids
    ("لَنْ تَكْتُبُوا الْيَوْمَ لَا تَنْتَظِرُوا", 4, "jazm"),  # so too to the same person
    ("لَنْ أَحْضُرَ وَلَا تَنْتَظِرُونِي", 3, "jazm"),  # nearest case: to another person the لا forbids
    ("لَنْ تَكْتُبُوا وَلَا تَنْتَظِرِي", 3, "jazm"),  # so to another number or gender
    ("لَنْ أَذْهَبَ وَلَا يَدْرِي", 3, "raf'"),  # so to another person, showing nothing: a plain negation
    ("لَنْ تَخْرُجَ وَلَا تَقُلْ شَيْئًا", 3, "jazm"),  # nearest case: a jussive shown on the verb says the لا forbids
    ("لَنْ تَذْهَبَ هِنْدٌ وَلَا تَنْتَظِرُنِي", 4, "raf'"),  # and a damma shown, that it only negates
    ("لَمْ يَذْهَبْ وَلَا يَدْرِي", 3, "raf'"),  # nearest case: after لم the لا stresses no nasb, and negates by itself
    ("لَنْ يَذْهَبَ زَيْدٌ وَلَمْ يَكْتُبْ", 4, "jazm"),  # nearest case: another negation governs by itself
    ("لَنْ أَذْهَبَ وَمَا أَدْرِي", 3, "raf'"),  # nearest case: ما governs no present verb and opens a clause of its own
    ("لَمْ يَذْهَبْ وَمَا يَدْرِي", 3, "raf'"),
])
def test_a_wa_la_after_a_verb_under_lan_takes_lans_nasb(sentence: str, at: int, case: str):
    assert _read(sentence)["words"][at]["case"] == case, sentence


@pytest.mark.parametrize("sentence, at, name", [
    # the five verbs keep their nun only in raf', whatever comes before it
    ("إِنْ تَجْتَهِدُوا فَتَنْجَحُونَ", 2, "جواب الشرط"),  # after a ف, a noun clause's khabar, the answer (Ibn Aqil V4, page unchecked)
    ("لَمْ يَذْهَبُوا وَيَكْتُبُونَ", 2, None),  # nearest case: after a و, by a jussive, it is no jussive joined on
    ("أَلَّا يَقْدِرُونَ عَلَى شَيْءٍ", 1, None),  # 57:29: before it the أنْ lightened from أنّ, which governs no verb
    ("أَنْ تَقْرَآنِ عَلَى أَسْمَاءَ وَيْحَكُمَا", 1, None),  # only the pair's nun takes a kasra: an أن left idle (Ibn Aqil; page unchecked)
    ("يَوْمَ الصُّلَيْفَاءِ لَمْ يُوفُونَ بِالْجَارِ", 3, None),  # a لم left idle (Ibn Aqil; page unchecked)
])
def test_a_five_verb_keeping_its_nun_is_in_raf(sentence: str, at: int, name: str | None):
    word = _read(sentence)["words"][at]
    assert (word.get("name"), word["case"]) == (name, "raf'"), sentence


@pytest.mark.parametrize("sentence, at, case", [
    # after a particle that governs a present verb by itself a kept nun is the root's own (لَنْ يَخُونَ: خَانَ), however the
    # analyser counted the doers
    ("لَنْ يَخُونَ الْأَمِينُ", 1, "nasb"),
    ("يُرِيدُ أَنْ يَخُونَكَ", 2, "nasb"),
    ("أَخْشَى أَنْ يَحِينَ الْوَقْتُ", 2, "nasb"),
    ("لَمْ يَكْتُبُوا", 1, "jazm"),  # nearest case: the nun dropped
])
def test_a_kept_nun_after_a_governing_particle_is_the_roots(sentence: str, at: int, case: str):
    assert _read(sentence)["words"][at]["case"] == case, sentence


@pytest.mark.parametrize("sentence, at", [
    ("إِنْ جَاءَ زَيْدٌ فَلْيَجْلِسْ", 3),  # a لام-command after the ف is the answer itself, never a verb between (Ibn Aqil V4, page unchecked)
    ("إِنْ تَدْرُسْ فَلْتَنْجَحْ", 2),
    ("إِنْ قَامَ زَيْدٌ فَلْيَقُمْ عَمْرٌو", 3),
])
def test_a_lam_command_after_fa_is_the_conditions_answer(sentence: str, at: int):
    """condition.find: a verb its لام commands answers the condition; only a bare one after ف or و may stand between."""
    word = _read(sentence)["words"][at]
    assert (word.get("name"), word["case"]) == ("جواب الشرط", "jazm"), sentence


@pytest.mark.parametrize("sentence, at, case", [
    # a doubled verb's jussive takes the fatha its nasb does (لَمْ يَرُدَّ: فُتح لالتقاء الساكنين): with no particle, ف or لام
    # before it no hidden أن can stand, so the fatha shows a jussive, the answer of a condition or a request
    ("إِنْ تَدْرُسُوا يُحِبَّكُمُ الْمُعَلِّمُ", 2, "jazm"),
    ("ازْهَدْ فِي الدُّنْيَا يُحِبَّكَ اللَّهُ", 3, "jazm"),
    ("لَا تَكْذِبْ فَيَضُرَّكَ", 2, "nasb"),  # nearest case: after a ف, فاء السببية
    ("أُحِبُّ أَنْ يَرُدَّ الْكِتَابَ", 2, "nasb"),  # after أن
    ("هُوَ يُحِبُّ الْخَيْرَ", 1, "raf'"),  # a damma typed
    ("لَا تَرُدَّ السَّائِلَ", 1, "jazm"),  # no negation puts a verb in nasb: the لا forbids
    ("لَا تُضَارَّ وَالِدَةٌ بِوَلَدِهَا", 1, "jazm"),  # 2:233
    ("اللَّهُمَّ لَا تَرُدَّنِي خَائِبًا", 2, "jazm"),  # the fatha read off the verb's own letter, past its ني
    ("لِيَرُدَّنِي إِلَى بَيْتِي", 0, "jazm"),  # a لام of command says which
    # after a joining word the verb it is joined to says which
    ("أُرِيدُ أَنْ أَقْرَأَ وَأَرُدَّ الْكِتَابَ", 3, "nasb"),
    ("لَمْ يَقْرَأْ وَيَرُدَّ الْكِتَابَ", 2, "jazm"),
    ("أُرِيدُ أَنْ أَقْرَأَ ثُمَّ أَرُدَّ الْكِتَابَ", 4, "nasb"),  # ثم, which the parser takes for a noun
    ("لَمْ يَقْرَأْ ثُمَّ يَرُدَّ الْكِتَابَ", 3, "jazm"),
    # nearest cases: joined to no verb in nasb or jazm, or after إِذَنْ, the fatha is nasb, a hidden أن's
    ("لَأَلْزَمَنَّكَ أَوْ تَرُدَّ حَقِّي", 2, "nasb"),
    ("إِذَنْ أُحِبَّكَ", 1, "nasb"),
    ("إِذًا أُحِبَّكَ", 1, "nasb"),  # إذن written with a tanween (particles.stamp)
    ("لِكَيْلَا تَضِلَّ", 1, "nasb"),
    ("تُبْ إِلَيْهِ يُحِبَّكَ", 2, "jazm"),  # nearest case: after a preposition, the answer of a request
    ("لَنْ يَرُدَّ وَلَا يَمُدَّ يَدَهُ", 3, "nasb"),  # the لا only stresses لن's negation
])
def test_a_doubled_verbs_fatha_after_a_verb_a_noun_or_la_is_a_jussive(sentence: str, at: int, case: str):
    assert _read(sentence)["words"][at]["case"] == case, sentence


@pytest.mark.parametrize("word, after, nun", [
    ("لِيَلِيَنِّي", 2, "emphasis"),  # the nun of emphasis and ني's nun written as one
    ("يَكْتُبَنَّنَا", 2, "emphasis"),  # before نا both are written
    ("تَأْمَنَّا", 2, None),  # لَا تَأْمَنَّا (12:11): the root's ن merged with نا, no nun of emphasis
])
def test_only_ni_shares_its_nun_with_the_nun_of_emphasis(word: str, after: int, nun: str | None):
    assert build_nun(word, after) == nun


@pytest.mark.parametrize("sentence, at, case", [
    # what a verb of saying says opens its own sentence, so a لِ opening it is لام الأمر (facts.said_verb)
    ("قَالَ الْمُعَلِّمُ لِيَكْتُبُوا دُرُوسَهُمْ", 2, "jazm"),
    ("جَاءَ الطُّلَّابُ لِيَكْتُبُوا دُرُوسَهُمْ", 2, "nasb"),  # nearest case: after a verb of coming, لام التعليل
    # a doubled verb's jussive takes a fatha as its nasb does, so a لِ opening the sentence still says الأمر (harakat.doubled_last)
    ("لِيَمُدَّ يَدَهُ", 0, "jazm"),
    ("لِيَرُدَّهُ زَيْدٌ", 0, "jazm"),
    ("جَاءَ لِيَرُدَّ الْكِتَابَ", 1, "nasb"),  # nearest case: after a clause, لام التعليل
    ("لِيَغْفِرَ لَكَ اللَّهُ", 0, "nasb"),  # nearest case: a fatha on a single letter is nasb
    ("لِيَرُدُّ الْمَالَ", 0, "jazm"),  # whatever vowel the doubled letter wears, the لام says which
])
def test_a_lam_opening_what_is_said_is_the_lam_of_command(sentence: str, at: int, case: str):
    assert _read(sentence)["words"][at]["case"] == case, sentence


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


@pytest.mark.parametrize("sentence, at, case, sign", [
    # تَتَحَاسَدُوا written with one of its two تاءات (Alfiyya, باب الإدغام): after لا، لم the present verb in jazm
    ("لَا تَحَاسَدُوا", 1, "jazm", "حذف النون"),
    # after a nasb particle no past follows either (expects.json nasb), nor under a kasra لام on the word (49:13)
    ("لَنْ تَحَاسَدُوا", 1, "nasb", "حذف النون"),
    ("جِئْتُ كَيْ تَعَارَفُوا", 2, "nasb", "حذف النون"),
    ("جَعَلْنَاكُمْ شُعُوبًا لِتَعَارَفُوا", 2, "nasb", "حذف النون"),
    ("حَتَّى تَعَارَفُوا", 1, "mabni", "مبني على الضم"),  # nearest case: حتى takes a past too ("until they knew")
    ("لَتَعَارَفُوا", 0, "mabni", "مبني على الضم"),  # nearest case: a fatha لام, the لام of an oath's answer, before a past
    ("لا تحاسدوا ولا تباغضوا", 1, "jazm", "حذف النون"),
    ("وَلَا تَوَلَّوْا عَنْهُ", 1, "jazm", "حذف النون"),  # 8:20, the Quranic Treebank's حرف نهي
    ("لَمْ تَنَازَعَا", 1, "jazm", "حذف النون"),
    ("الطُّلَّابُ تَحَاسَدُوا", 1, "mabni", "مبني على الضم"),  # nearest case: no particle, the past verb
    ("مَا تَحَاسَدُوا", 1, "mabni", "مبني على الضم"),  # nearest case: ما negates a past as well
    ("بَعْدَ أَنْ تَحَاسَدُوا", 2, "mabni", "مبني على الضم"),  # nearest case: أَنْ takes a past too
    ("لَا تَنَازَعَ زَيْدٌ", 1, "mabni", "مبني على الفتح"),  # nearest case: no present ends so
    ("لَا صَدَّقُوا وَلَا صَلَّوْا", 1, "mabni", "مبني على الضم"),  # nearest case: a past with no تاء of its own
    ("فَلَا تَابُوا وَلَا تَذَكَّرُوا", 3, "mabni", "مبني على الضم"),  # nearest case: لا said again over pasts (75:31)
    ("لَا تَحَاسَدْنَ", 1, "mabni", "مبني على السكون"),  # the women's nun, stilled before it: the present, built
    ("لَمَّا تَزَوَّجَا سَافَرَا", 1, "mabni", "مبني على الفتح"),  # nearest case: لَمَّا opens a past too ("when")
    ("فَلَمَّا تَبَيَّنَ لَهُ قَالَ", 1, "mabni", "مبني على الفتح"),  # nearest case: the ن is the root's, no women's
    ("لَا تَبَيَّنَ لَهُ", 1, "mabni", "مبني على الفتح"),
])
def test_a_verb_with_one_of_its_two_taas_after_a_particle_of_the_present_is_the_present_one(sentence, at, case, sign):
    verb = _read(sentence)["words"][at]
    assert (verb["case"], verb["sign"]) == (case, sign)


@pytest.mark.parametrize("sentence, at, case, sign", [
    ("لَا يَعْنِيهِ", 1, "raf'", "ضمة مقدرة على الياء للثقل"),  # the ي before the pronoun is the verb's: no jazm, لا only negates
    ("لا يعنيه", 1, "raf'", "ضمة مقدرة على الياء للثقل"),
    ("زَيْدٌ يَدْعُوهُ", 1, "raf'", "ضمة مقدرة على الواو للثقل"),  # its و is no plural's
    ("لَمْ يَدْعُهُ", 1, "jazm", "حذف حرف العلة"),  # the weak letter gone before the pronoun
    ("لَا تَرْمِهِ", 1, "jazm", "حذف حرف العلة"),
    ("الطُّلَّابُ يَكْتُبُونَهُ", 1, "raf'", "ثبوت النون"),  # the five verbs' nun before a pronoun
    ("لَنْ يَكْتُبُوهُ", 1, "nasb", "حذف النون"),
    ("لَنْ يَكْتُبَهَا", 1, "nasb", "فتحة"),  # the ا is the pronoun's, not the pair's
    ("يَهْدِيهِمْ رَبُّهُمْ", 0, "raf'", "ضمة مقدرة على الياء للثقل"),
    ("يَرْضَاهُ اللَّهُ", 0, "raf'", "ضمة مقدرة على الألف للتعذر"),
    ("لَمْ يَأْتِنَا أَحَدٌ", 1, "jazm", "حذف حرف العلة"),
    ("لَمْ يَرْمِهِ أَحَدٌ", 1, "jazm", "حذف حرف العلة"),
    ("يُؤْتُونَهُ", 0, "raf'", "ثبوت النون"),
    ("لَمْ يَضْرِبُوهُ", 1, "jazm", "حذف النون"),
    # on a weak last letter the ا before a pronoun is the root's (يرضى), no pair's: no nun to drop
    ("لَنْ يَرْضَاهُ أَحَدٌ", 1, "nasb", "فتحة مقدرة على الألف للتعذر"),
    ("لَنْ يَخْشَاهُمَا", 1, "nasb", "فتحة مقدرة على الألف للتعذر"),
    ("لَا يَرْضَاهُ أَحَدٌ", 1, "raf'", "ضمة مقدرة على الألف للتعذر"),  # so لا only negates
    ("لَنْ يَرْضَيَا", 1, "nasb", "حذف النون"),  # nearest case: the pair's ا after the ي
    # a و left bare before a pronoun after jazm or nasb is the group's: one doer's goes (لم يَدْعُهُ) or takes a fatha
    ("لَا تَنْسَوْهُ", 1, "jazm", "حذف النون"),
    ("لَمْ يَرْمُوهُ أَحَدٌ", 1, "jazm", "حذف النون"),
    ("لَنْ يَرْمُوهُ", 1, "nasb", "حذف النون"),
    ("لَنْ يَدْعُوَهُ", 1, "nasb", "فتحة"),  # nearest case: the fatha on و makes it one doer's
    ("لَوْمَا تَأْتِينَا بِالْمَلَائِكَةِ", 1, "raf'", "ضمة مقدرة على الياء للثقل"),  # 15:7: an urging particle governs nothing
])
def test_a_present_verb_shows_its_case_on_its_own_letters_before_an_attached_pronoun(sentence, at, case, sign):
    """harakat.stilled and signs._present_sign read the verb less its pronoun: يَعْنِيهِ keeps its ي, يَكْتُبُونَهُ its nun."""
    verb = _read(sentence)["words"][at]
    assert (verb["case"], verb["sign"]) == (case, sign)


@pytest.mark.parametrize("sentence, at, case, sign", [
    # جواب الطلب: a jussive straight after a command is its answer, a present in jazm, not a second command
    ("فَاسْتَغْفِرُونِي أَغْفِرْ لَكُمْ", 1, "jazm", "سكون"),
    ("فَاسْتَهْدُونِي أَهْدِكُمْ", 1, "jazm", "حذف حرف العلة"),
    ("زُرْنِي أُكْرِمْكَ", 1, "jazm", "سكون"),
    ("أَكْرِمْ زَيْدًا", 0, "mabni", "مبني على السكون"),  # nearest case: a command opening the sentence stays one
    ("رَبِّ اغْفِرْ لِي", 1, "mabni", "مبني على السكون"),  # nearest case: after a منادى the command stays one
    ("زُرْنِي أَكْرِمْ زَيْدًا", 1, "mabni", "مبني على السكون"),  # nearest case: أَفْعِلْ with fatha is a command, not أُفْعِلْ
    # أُفْعِلْ after لَمْ is the present in jazm: its sukun is no past passive's (أُكْرِمَ)
    ("لَمْ أُكْرِمْكَ", 1, "jazm", "سكون"),
    ("لَمْ أُكْرِمْ زَيْدًا", 1, "jazm", "سكون"),
    ("لَمَّا أُكْرِمَ زَيْدٌ", 1, "mabni", "مبني على الفتح"),  # nearest case: لَمَّا "when" takes the past
    ("لِمَ تَرَكَ الصَّلَاةَ", 1, "mabni", "مبني على الفتح"),  # nearest case: لِمَ "why", spelled as لَمْ, takes the past
    ("لِمَ أُخْرِجَ زَيْدٌ", 1, "mabni", "مبني على الفتح"),
    # nearest cases: a command after قَالَ, a call, or joined by ف or و is a command, not an answer
    ("قَالَ أَمْسِكْ عَلَيْكَ لِسَانَكَ", 1, "mabni", "مبني على السكون"),
    ("اللَّهُمَّ أصْلِحْ لِي دِينِي", 1, "mabni", "مبني على السكون"),
    ("قُمْ فَأَمْسِكْ عَلَيْكَ لِسَانَكَ", 1, "mabni", "مبني على السكون"),
    ("اُسْكُتْ وَأَمْسِكْ عَلَيْكَ لِسَانَكَ", 1, "mabni", "مبني على السكون"),
    # nearest cases: a أَفْعَلَ the dictionary knows (أَمْسَكَ، أَنْزَلَ) is its own command beside another; a shared root is the answer
    ("اسْكُتْ أَمْسِكْ", 1, "mabni", "مبني على السكون"),
    ("قُلْ أَمْسِكْ لِسَانَكَ", 1, "mabni", "مبني على السكون"),
    ("قُمْ أَنْزِلِ الْمَتَاعَ", 1, "mabni", "مبني على السكون"),
    ("اجْلِسْ أَجْلِسْ", 1, "jazm", "سكون"),
    ("قُمْ فَأَنْذِرْ", 1, "mabni", "مبني على السكون"),  # 74:2: the ف CAMeL splits off is no part of the command
    # nearest case: bare لم and a past no present of its root spells is لِمَ "why"
    ("لم ترك الصلاة", 1, "mabni", "مبني على الفتح"),
])
def test_a_jussive_after_a_command_or_lam_is_a_present_in_jazm(sentence, at, case, sign):
    """repair/typed.py reads جواب الطلب; morphology._wants_present and harakat.past_passive_shape keep أُفْعِلْ present."""
    verb = _read(sentence)["words"][at]
    assert (verb["case"], verb["sign"]) == (case, sign)


@pytest.mark.parametrize("sentence, at, case, sign", [
    # a معطوف wears its معطوف عليه's case, its kasra on ـات a nasb too: where its و hangs on the verb (it follows the
    # verb's object), and after a built word, which stands in its role's case (إيّا is the object pronoun)
    ("رَأَيْتُ زَيْدًا وَالْمُسْلِمَاتِ", 2, "nasb", "كسرة، نيابة عن الفتحة، جمع مؤنث سالم"),
    ("رَأَيْتُ هَؤُلَاءِ وَالْمُسْلِمَاتِ", 2, "nasb", "كسرة، نيابة عن الفتحة، جمع مؤنث سالم"),
    ("جاء زيد والمسلمات", 2, "raf'", "ضمة"),  # joined to the doer before its و, untyped: it shares the doer's raf'
    ("ضرب زيد عمرا وبكر", 3, "nasb", "فتحة"),  # joined to the nearest, the object
    ("ضرب عمرا زيد والمسلمات", 3, "raf'", "ضمة"),  # the object first: the nearest is the doer
    ("إِيَّاكَ وَالْمُسْلِمَاتِ", 1, "nasb", "كسرة، نيابة عن الفتحة، جمع مؤنث سالم"),
    ("وَإِيَّاكُمْ وَمُحْدَثَاتِ الْأُمُورِ", 1, "nasb", "كسرة، نيابة عن الفتحة، جمع مؤنث سالم"),
    ("مَرَرْتُ بِزَيْدٍ وَالْمُسْلِمَاتِ", 2, "jarr", "كسرة"),  # nearest case: after a مجرور the kasra is jarr
    ("مَرَرْتُ بِهَذَا وَالْمُسْلِمَاتِ", 2, "jarr", "كسرة"),
])
def test_a_follower_wears_the_case_of_the_word_it_follows(sentence, at, case, sign):
    """followers.followed finds the معطوف عليه past a verb or إيّا; take_their_ending reads a built word's place."""
    word = _read(sentence)["words"][at]
    assert (word["case"], word["sign"]) == (case, sign)


@pytest.mark.parametrize("sentence, at, role", [
    # a past passive the dictionary lacks, behind a joined ف or و: the particle's fatha is no part of فُعِلَ
    ("فَأُتِيَ بِرَجُلٍ", 0, "فعل مجهول"),
    ("فَسُحِبَ عَلَى وَجْهِهِ", 0, "فعل مجهول"),
    ("وَقُتِلَ زَيْدٌ", 0, "فعل مجهول"),
    ("فَسَحَبَ زَيْدٌ الْحَبْلَ", 0, "فعل"),  # nearest case: the active past opens on a fatha
    ("فَأُقِيمَتِ الصَّلَاةُ", 0, "فعل مجهول"),  # أَقَامَ's فُعِلَ opens on أ, a long ي after its kasra
])
def test_a_past_passive_behind_a_joined_particle_is_a_verb(sentence, at, role):
    """morphology._passive_shape_past_joined reads فُعِلَ past the joined ف or و."""
    verb = _read(sentence)["words"][at]
    assert (verb["role"], verb["case"]) == (role, "mabni")


@pytest.mark.parametrize("sentence, at, case, sign", [
    # on ت ي ن the shape of أُقِيمَ is the present of أَفْعَلَ (harakat.past_passive_shape), and with one doer a last ن is the root's,
    # its vowel the case (ending.mood), no nun of the five verbs: joined by ف to a verb in nasb it takes the nasb
    ("أَرْجُو أَنْ تَأْتِيَ فَتُعِينَ أَخَاكَ", 3, "nasb", "فتحة"),
    ("أُرِيدُ أَنْ تَقُومَ فَتَكُونَ مَعَنَا", 3, "nasb", "فتحة"),
    ("لَمْ يَأْتِ فَيُعِينَ أَخَاهُ", 2, "nasb", "فتحة"),
    ("هُوَ يُعِينُ أَخَاهُ", 1, "raf'", "ضمة"),
    ("أَنْتِ تَكْتُبِينَ الدَّرْسَ", 1, "raf'", "ثبوت النون"),  # nearest case: أَنْتِ's ي, its nun the five verbs'
    ("أَنْتُمْ تُعِينُونَ إِخْوَانَكُمْ", 1, "raf'", "ثبوت النون"),
    ("لَنْ نُعِينَ الظَّالِمَ", 1, "nasb", "فتحة"),  # the five verbs open on ي or ت: نُفْعِلُ's last ن is the root's
    ("نُعِينَ أَخَانَا", 0, "nasb", "فتحة"),  # with no particle too, as يُعِينَ: the fatha typed on it is its case
    ("يُعِينَ أَخَاهُ", 0, "nasb", "فتحة"),
])
def test_a_present_verb_on_a_root_ending_in_nun_shows_its_case_on_that_nun(sentence, at, case, sign):
    verb = _read(sentence)["words"][at]
    assert (verb["role"], verb["case"], verb["sign"]) == ("فعل", case, sign)


@pytest.mark.parametrize("sentence, at, role", [
    # a letter typed with a sukun is not doubled: فَصُمْ is the command "fast", never صُمّ "deaf" (a doubled ميم)
    ("فَصُمْ", 0, "فعل"),
    ("فَنَمْ", 0, "فعل"),
    ("فَصُمْهُ", 0, "فعل"),
    ("هُمْ صُمٌّ", 1, "خبر"),  # nearest case: typed doubled, the adjective stays
])
def test_a_letter_typed_still_is_never_doubled(sentence, at, role):
    """harakat.vowel_agreement: a sukun typed where the reading has a shadda rules that reading out."""
    assert _read(sentence)["words"][at]["role"] == role


@pytest.mark.parametrize("sentence, index, named, role, case", [
    # حروف التحضيض (Kafiya p55: هلا، ألا، لولا، لوما، لها صدر الكلام، ويلزم الفعل): urging before a verb
    ("هَلَّا تَدْرُسُ", 0, "حرف عرض وتحضيض", "حرف", "mabni"),
    ("لَوْمَا تَأْتِينَا بِالْمَلَائِكَةِ", 0, "حرف عرض وتحضيض", "حرف", "mabni"),  # 15:7, read as its twin لولا
    ("لَوْمَا زَيْدٌ لَهَلَكَ عَمْرٌو", 0, "حرف امتناع لوجود", "حرف", "mabni"),  # before a noun, as لولا is
    ("لَقِيَ لَوْمًا شَدِيدًا", 1, None, "مفعول به", "nasb"),  # nearest case: a tanween makes it the noun (blame)
    ("لَقِيَ لَوْمًا شَدِيدًا", 2, None, "صفة", "nasb"),
    ("رَأَيْتُ لَوْمًا كَثِيرًا", 1, None, "مفعول به", "nasb"),
])
def test_an_urging_particle_is_named_so_and_one_with_a_tanween_is_the_noun_its_letters_spell(
        sentence: str, index: int, named: str | None, role: str, case: str):
    word = _read(sentence)["words"][index]
    assert (word.get("named"), word["role"], word["case"]) == (named, role, case)


@pytest.mark.parametrize("sentence, index, case, sign", [
    # CAMeL files رأى's present under راوند (rhubarb); mended, its dropped hamza leaves a weak last letter
    ("لَمْ يَرَهُ أَحَدٌ", 1, "jazm", "حذف حرف العلة"),
    ("لَمْ يَرَ زَيْدٌ عَمْرًا", 1, "jazm", "حذف حرف العلة"),
    ("أَلَمْ تَرَ كَيْفَ فَعَلَ رَبُّكَ", 1, "jazm", "حذف حرف العلة"),
    ("زَيْدٌ يَرَى الْهِلَالَ", 1, "raf'", "ضمة مقدرة على الألف للتعذر"),
    ("رَأَيْتُ زَيْدًا", 0, "mabni", "مبني على السكون"),  # nearest case: the past keeps its hamza
])
def test_the_present_of_raa_has_a_weak_last_letter(sentence: str, index: int, case: str, sign: str):
    verb = _read(sentence)["words"][index]
    assert (verb["case"], verb["sign"]) == (case, sign)


@pytest.mark.parametrize("sentence, at, role", [
    # a doer name the parser hung on the verb as a modifier, showing raf', with the noun in nasb hung on it: the doer
    # comes first, the nasb noun is the verb's object (a نعت or بدل would wear the name's case)
    ("شَدَّ زَيْدٌ الْحَبْلَ شَدًّا", 2, "مفعول به"),
    ("ضَرَبَ زَيْدٌ عَمْرًا ضَرْبًا", 2, "مفعول به"),
    ("قَرَأَ مُحَمَّدٌ الْكِتَابَ", 2, "مفعول به"),
])
def test_a_nasb_noun_after_a_doer_name_is_the_verbs_object(sentence, at, role):
    """repair/subject_clash.doer_first takes the name whatever link the parser gave it to the verb."""
    assert _role(sentence, at) == role


@pytest.mark.parametrize("sentence, at, role", [
    # a word on the elative's shape typed with a fatha, first or after a ما, before a مِنْ-phrase: no عامل stands
    # before it to set a noun in nasb, so it is the past verb; after إِنَّ or a كان-verb it may be the noun in nasb
    ("أَصْبَحَ مِنْ عِبَادِي مُؤْمِنٌ", 0, "فعل"),
    ("مَا أَصْبَحَ مِنْهُمْ أَحَدٌ", 1, "فعل"),
    ("إِنَّمَا أَصْبَحَ مِنْهُمْ رَجُلٌ", 1, "فعل"),
    ("إِنَّ أَكْرَمَ مِنْكُمْ زَيْدٌ", 1, "اسم إن"),
    ("لَيْسَ شَيْءٌ أَعْظَمَ مِنْ ذَلِكَ", 2, "خبر كان"),
    # the dual pronoun هُمَا ends in ما but is no ما: the verb it is written on sets the noun in nasb
    ("أَعْطَيْتُهُمَا أَكْثَرَ مِنْ حَقِّهِمَا", 1, "مفعول به"),
])
def test_a_fatha_with_nothing_to_set_it_in_nasb_is_the_past_verbs(sentence, at, role):
    """morphology.pick leaves the verb read where its elative rule finds no عامل of nasb before the word."""
    assert _role(sentence, at) == role


def test_a_command_ending_in_a_damma_still_answers_a_condition():
    """اُدْعُ ends on its ع's damma, its و dropped for the command, which is never a حال or صفة (Ibn Aqil V3 p198:
    وامنع هنا إيقاع ذات الطلب): the damma is no raf' that would make it one, as it is on a present verb."""
    from backend.services.nahw.syntax.particles import _answers_bare
    command = {"pos": "VRB", "asp": "c", "typed": "فَادْعُ", "lemma": "دَعا", "base": "ادع", "form": "ادع", "stuck_on": 0}
    assert _answers_bare(command) and not _answers_bare(dict(command, asp="i"))
