"""A held-out set the engine was never tuned on: 45 fully vowelled sentences written by an
independent examiner, each with the role a nahw teacher expects on its key words. Roles only
(the role, or the finer name the card prints for it); signs only where a rule is about the sign.

A sentence here is never used to write a rule; a rule is fixed on its sibling and checked here."""
import pytest

from tests.nahw_helpers import analyze, cards, needs_parser, tree_roles

pytestmark = needs_parser

# sentence → {word index: role the card prints (its finer name, else its role)}
EXPECTED = {
    "الصِّدْقُ مَنْجَاةٌ": {0: "مبتدأ", 1: "خبر"},
    "الْبُسْتَانُ وَاسِعٌ أَشْجَارُهُ": {0: "مبتدأ", 1: "خبر", 2: "فاعل"},
    "فِي الدَّارِ رَجُلٌ": {1: "مجرور", 2: "مبتدأ مؤخر"},
    "كَانَ الْجَوُّ بَارِدًا": {1: "اسم كان", 2: "خبر كان"},
    "أَصْبَحَ الْفَلَّاحُ نَشِيطًا": {1: "اسم أصبح", 2: "خبر أصبح"},
    "لَيْسَ الْكَذُوبُ أَمِينًا": {1: "اسم ليس", 2: "خبر ليس"},
    "إِنَّ الْحَدِيقَةَ مُزْهِرَةٌ": {1: "اسم إن", 2: "خبر إن"},
    "لَعَلَّ الْمُسَافِرَ قَادِمٌ": {1: "اسم لعل", 2: "خبر لعل"},
    "كَأَنَّ النُّجُومَ لَآلِئُ": {1: "اسم كأن", 2: "خبر كأن"},
    "قَرَأَ الطَّالِبُ الْقِصَّةَ": {1: "فاعل", 2: "مفعول به"},
    "صَبَرَ الْمَرِيضُ صَبْرًا طَوِيلًا": {1: "فاعل", 2: "مفعول مطلق", 3: "صفة"},
    "وَقَفَ الْجُنْدِيُّ احْتِرَامًا لِلْقَائِدِ": {1: "فاعل", 2: "مفعول لأجله", 3: "مجرور"},
    "سَافَرْنَا لَيْلًا": {0: "فعل", 1: "مفعول فيه"},
    "جَاءَ الضَّيْفُ مُبْتَسِمًا": {1: "فاعل", 2: "حال"},
    "رَجَعَ الْجَيْشُ مُنْتَصِرًا": {1: "فاعل", 2: "حال"},
    "دَخَلَ الْمُعَلِّمُ الْفَصْلَ ضَاحِكًا": {1: "فاعل", 2: "مفعول به", 3: "حال"},
    "بَاعَ التَّاجِرُ ثَلَاثِينَ ثَوْبًا": {1: "فاعل", 2: "مفعول به", 3: "تمييز"},
    "طَابَ الْمُجْتَهِدُ نَفْسًا": {1: "فاعل", 2: "تمييز"},
    "امْتَلَأَ الْحَوْضُ مَاءً": {1: "فاعل", 2: "تمييز"},
    "زَارَنَا صَدِيقٌ كَرِيمٌ": {1: "فاعل", 2: "صفة"},
    "أَكَلْتُ الْخُبْزَ وَالْجُبْنَ": {1: "مفعول به", 2: "معطوف"},
    "حَضَرَ الْأَمِيرُ نَفْسُهُ": {1: "فاعل", 2: "توكيد"},
    "قَابَلْتُ أَخَاكَ مُحَمَّدًا": {1: "مفعول به", 2: "بدل"},
    "بَابُ بَيْتِ الْجَارِ مَفْتُوحٌ": {0: "مبتدأ", 1: "مضاف إليه", 2: "مضاف إليه", 3: "خبر"},
    "قَرَأْتُ كِتَابَ أُسْتَاذِ الْمَدْرَسَةِ": {1: "مفعول به", 2: "مضاف إليه", 3: "مضاف إليه"},
    "سَارَ الْقِطَارُ إِلَى الْمَدِينَةِ": {1: "فاعل", 2: "حرف جر", 3: "مجرور"},
    "مَرَرْتُ بِالْقَرْيَةِ": {1: "مجرور"},
    "خَرَجَ الطَّيْرُ مِنَ الْعُشِّ": {1: "فاعل", 3: "مجرور"},
    "مَنْ يَزْرَعِ الْخَيْرَ يَجْنِ الثَّوَابَ": {0: "مبتدأ", 2: "مفعول به", 4: "مفعول به"},
    "لَوْلَا الْمَطَرُ لَهَلَكَ الزَّرْعُ": {1: "مبتدأ", 3: "فاعل"},
    "هَلْ حَضَرَ الطَّبِيبُ": {2: "فاعل"},
    "أَيْنَ الْقَلَمُ": {0: "خبر", 1: "مبتدأ"},
    "مَتَى يَعُودُ الْمُسَافِرُ": {0: "مفعول فيه", 2: "فاعل"},
    "يَا طَالِبَ الْعِلْمِ اجْتَهِدْ": {1: "منادى", 2: "مضاف إليه", 3: "فعل أمر"},
    "يَا سَعِيدُ": {1: "منادى"},
    "نَجَحَ الطُّلَّابُ إِلَّا خَالِدًا": {1: "فاعل", 3: "مستثنى"},
    "لَا ظُلْمَ مَقْبُولٌ": {1: "اسم لا", 2: "خبر لا"},
    "الطُّلَّابُ يَكْتُبُونَ الدَّرْسَ": {0: "مبتدأ", 2: "مفعول به"},
    "أَحْبَبْتُ الَّتِي غَنَّتْ": {1: "مفعول به"},
    "كُسِرَ الزُّجَاجُ": {0: "فعل مجهول", 1: "نائب فاعل"},
    "يُحْتَرَمُ الْعَالِمُ": {0: "فعل مجهول", 1: "نائب فاعل"},
    "مَا أَعْذَبَ الْمَاءَ": {2: "مفعول به"},
    "نِعْمَ الْخُلُقُ الْوَفَاءُ": {1: "فاعل", 2: "مبتدأ"},
    "هَذَانِ الْمُهَنْدِسَانِ مَاهِرَانِ": {0: "مبتدأ", 2: "خبر"},
}

# where the rule is about the sign: a dual pointer inflects by its letters, it is not built on its last kasra;
# the five verbs' nun is kept in raf' and dropped in nasb and jazm (signs._present_sign)
EXPECTED_SIGN = {
    "هَذَانِ الْمُهَنْدِسَانِ مَاهِرَانِ": {0: "الألف، مثنى"},
    "لَنْ يَكْتُبُوا": {1: "حذف النون"},
    "الطُّلَّابُ يَكْتُبُونَ الدَّرْسَ": {1: "ثبوت النون"},
}


def _printed(card: dict) -> str | None:
    return card.get("name") or card.get("role")


@pytest.mark.parametrize("sentence", list(EXPECTED))
def test_held_out_roles(sentence):
    words = cards(sentence)
    got = {i: _printed(words[i]) for i in EXPECTED[sentence]}
    assert got == EXPECTED[sentence], sentence


@pytest.mark.parametrize("sentence", list(EXPECTED_SIGN))
def test_held_out_signs(sentence):
    words = cards(sentence)
    got = {i: words[i].get("sign") for i in EXPECTED_SIGN[sentence]}
    assert got == EXPECTED_SIGN[sentence], sentence


# ── Rules a mutation showed no test guarded: one sentence each way, the answer checked by hand ──

# the mood a لام written onto a present verb gives it: لام الأمر jazm, لام التعليل nasb (naming._lam_mood)
# and a present verb joined by و to a verb in jazm or nasb is in that mood too (naming._followers_take_their_ending)
EXPECTED_CASE = {
    "لِيَكْتُبْ زَيْدٌ الدَّرْسَ": {0: "jazm"},
    "جِئْتُ لِأَتَعَلَّمَ": {1: "nasb"},
    # the same with no vowel typed on the last letter: only the لام says the mood
    "لِيَكْتُب الدَّرْسَ": {0: "jazm"},
    "جِئْتُ لِأَتَعَلَّم": {1: "nasb"},
    # a weak last letter still written is no jazm (the command is لِتَرْضَ), so an opening kasra لام is التعليل
    "لِتَرْضَى عَنَّا": {0: "nasb"},
    "لِيَرْضَ عَنَّا": {0: "jazm"},
    # a kasra لام behind a joined و is التعليل even at the start, a sukun one الأمر (only the لام shows: the nun is gone)
    "وَلِتَبْتَغُوا مِنْ فَضْلِهِ": {0: "nasb"},
    "وَلِتُكْمِلُوا الْعِدَّةَ": {0: "nasb"},
    "وَلْيَأْخُذُوا أَسْلِحَتَهُمْ": {0: "jazm"},
    "لِيَأْخُذُوا أَسْلِحَتَهُمْ": {0: "jazm"},
    "لَمْ يَأْكُلْ وَيَشْرَب": {2: "jazm"},
    "لَنْ يَأْكُلُوا وَيَشْرَبُوا": {2: "nasb"},
}
# a verb clause is governed only by a family that frames it (كان: its khabar); the verb a parser hangs
# a صلة on does not govern it (naming._governed)
EXPECTED_GOVERNOR = {
    "كَانَ الطِّفْلُ يَلْعَبُ": {2: 0},
    "جَاءَ مَنْ نَجَحَ": {2: None},
}
# a command's doer is the hidden أنت, so the noun after it is its object (slot.verb_place); a noun with a
# pronoun stuck on is definite, so a clause after it is its حال, not a صفة (hang.definite)
EXPECTED_PICTURE = {
    "اكْتُبْ الدَّرْسَ": ["فعل أمر", "مفعول به"],
    "لِيَقُمْ زَيْدٌ": ["لام الأمر", "فعل مضارع للأمر", "فاعل"],
    # لام التعليل is one حرف جر wherever it stands (naming.roles), its verb behind a hidden أن a masdar in jarr
    "لِتَرْضَى عَنَّا": ["حرف جر", "فعل", "حرف جر", "مجرور"],
    # a kasra لام behind و before a verb whose nun is gone is التعليل: no لام الأمر, no command (particles._lam_on),
    # and the و is a حرف عطف, not one of the حروف النصب by the list of what may stand before إذن (book.in_family)
    "وَلِتَبْتَغُوا مِنْ فَضْلِهِ": ["حرف عطف", "حرف جر", "فعل", "حرف جر", "مجرور", "مضاف", "مضاف إليه"],
    "وَلِيَعْلَمَ اللَّهُ الَّذِينَ آمَنُوا": ["حرف عطف", "حرف جر", "فعل", "فاعل", "مفعول به", "اسم موصول", "صلة", "فعل"],
    "وَلْيَأْخُذُوا أَسْلِحَتَهُمْ": ["حرف عطف", "لام الأمر", "فعل مضارع للأمر", "مفعول به", "مضاف", "مضاف إليه"],
    "لِيَأْخُذُوا أَسْلِحَتَهُمْ": ["لام الأمر", "فعل مضارع للأمر", "مفعول به", "مضاف", "مضاف إليه"],  # opening: الأمر
    "جَاؤُوا لِيَأْخُذُوا أَسْلِحَتَهُمْ": ["فعل", "حرف جر", "فعل", "مفعول به", "مضاف", "مضاف إليه"],  # after a clause: التعليل
    # what a verb of saying holds opens a sentence of its own, its مقول القول: الأمر (facts.said_verb)
    "قَالَ الْمُعَلِّمُ لِيَكْتُبُوا دُرُوسَهُمْ": ["فعل", "فاعل", "لام الأمر", "فعل مضارع للأمر", "مفعول به", "مضاف", "مضاف إليه"],
    "جَاءَ الطُّلَّابُ لِيَكْتُبُوا دُرُوسَهُمْ": ["فعل", "فاعل", "حرف جر", "فعل", "مفعول به", "مضاف", "مضاف إليه"],
    # a nun of emphasis never follows لام التعليل's nasb: a kasra لام before it is الأمر, its weak letter kept or not
    "لِيَلِيَنِّي مِنْكُمْ أُولُو الْأَحْلَامِ": ["لام الأمر", "فعل مضارع للأمر", "حرف جر", "مجرور", "فاعل", "مضاف", "مضاف إليه"],
    "لِيَكْتُبَنَّ زَيْدٌ": ["لام الأمر", "فعل مضارع للأمر", "فاعل"],
    # a nasb fatha typed on the verb rules out الأمر even at the start: التعليل (لِيَغْفِرَ لَكَ اللَّهُ, 48:2)
    "لِيَغْفِرَ لَكَ اللَّهُ": ["حرف جر", "فعل", "حرف جر", "مجرور", "فاعل"],
    "لِيُكْرِمَكَ زَيْدٌ": ["حرف جر", "فعل", "فاعل"],
    "لِيُكْرِمْكَ زَيْدٌ": ["لام الأمر", "فعل مضارع للأمر", "فاعل"],
    # a particle works on what comes after it: the لَ of لَكَ is a حرف جر, not the لام of the jazm before it (naming._family)
    "لِيَغْفِرْ لَكَ اللَّهُ": ["لام الأمر", "فعل مضارع للأمر", "حرف جر", "مجرور", "فاعل"],
    # a doubled verb's fatha is its jussive's too: the لِ opening the sentence stays لام الأمر (harakat.doubled_last)
    "لِيَمُدَّ يَدَهُ": ["لام الأمر", "فعل مضارع للأمر", "مفعول به", "مضاف", "مضاف إليه"],
    # لام التعليل and its verb tell why the act was done: hung on the verb, no صفة of the noun before (unwritten)
    "رَأَيْتُ رَجُلًا لِيَكْتُبَ": ["فعل", "مفعول به", "حرف جر", "فعل"],
    "أَعْطَيْتُهُ كِتَابًا لِيَقْرَأَهُ": ["فعل", "مفعول به ثانٍ", "حرف جر", "فعل"],
    "رَأَيْتُ رَجُلًا مِنَ الْأَنْصَارِ": ["فعل", "مفعول به", "موصوف", "صفة", "حرف جر", "مجرور"],
    # فاء السببية and واو المعية join the verb's masdar to the one the command holds: حرف عطف; an أن hidden
    # behind them puts the verb in nasb, so neither is a حرف نصب (Ibn Hisham, Qatr al-Nada, page unchecked)
    "اُدْرُسْ فَتَنْجَحَ": ["فعل أمر", "حرف عطف", "فعل"],
    "لَا تَأْكُلِ السَّمَكَ وَتَشْرَبَ اللَّبَنَ": ["لا الناهية", "فعل مضارع للنهي", "مفعول به", "حرف عطف", "فعل", "مفعول به"],
    "كِتَابُهُ جَدِيدٌ": ["مبتدأ", "مضاف", "مضاف إليه", "خبر"],
    "جَاءَ أَخُوهُ مُسْرِعًا": ["فعل", "فاعل", "مضاف", "مضاف إليه", "حال"],
    "جَاءَ أَخُوهُ يَرْكُضُ": ["فعل", "فاعل", "مضاف", "مضاف إليه", "حال", "فعل"],
    "رَأَيْتُ صَدِيقَهُ يَبْكِي": ["فعل", "مفعول به", "مضاف", "مضاف إليه", "حال", "فعل"],
}


@pytest.mark.parametrize("sentence", list(EXPECTED_CASE))
def test_held_out_cases(sentence):
    words = cards(sentence)
    assert {i: words[i].get("case") for i in EXPECTED_CASE[sentence]} == EXPECTED_CASE[sentence], sentence


@pytest.mark.parametrize("sentence", list(EXPECTED_GOVERNOR))
def test_held_out_governors(sentence):
    words = cards(sentence)
    assert {i: words[i].get("governor") for i in EXPECTED_GOVERNOR[sentence]} == EXPECTED_GOVERNOR[sentence], sentence


@pytest.mark.parametrize("sentence", list(EXPECTED_PICTURE))
def test_held_out_pictures(sentence):
    assert tree_roles(analyze(sentence)["tree"]["tree"]) == EXPECTED_PICTURE[sentence], sentence
