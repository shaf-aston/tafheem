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

# where the rule is about the sign: a dual pointer inflects by its letters, it is not built on its last kasra
EXPECTED_SIGN = {
    "هَذَانِ الْمُهَنْدِسَانِ مَاهِرَانِ": {0: "الألف، مثنى"},
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
    "لَمْ يَأْكُلْ وَيَشْرَب": {2: "jazm"},
    "لَنْ يَأْكُلُوا وَيَشْرَبُوا": {2: "nasb"},
}
# the five verbs' nun: kept in raf', dropped in nasb and jazm (signs._present_sign)
EXPECTED_SIGN.update({
    "لَنْ يَكْتُبُوا": {1: "حذف النون"},
    "الطُّلَّابُ يَكْتُبُونَ الدَّرْسَ": {1: "ثبوت النون"},
})
# a verb clause is governed only by a family that frames it (كان: its khabar); the verb a parser hangs
# a صلة on does not govern it (naming._governed)
EXPECTED_GOVERNOR = {
    "كَانَ الطِّفْلُ يَلْعَبُ": {2: 0},
    "جَاءَ مَنْ نَجَحَ": {2: None},
}
# a command's doer is the hidden أنت, so the noun after it is its object, unless its damma says it is the doer
# (slot.verb_place); a noun with a pronoun stuck on is definite, so what follows it is a حال, and the pair
# an idafa (tree.definite)
EXPECTED_PICTURE = {
    "اكْتُبْ الدَّرْسَ": ["فعل أمر", "مفعول به"],
    "لِيَقُمْ زَيْدٌ": ["لام الأمر", "فعل مضارع للأمر", "فاعل"],
    "كِتَابُهُ جَدِيدٌ": ["مبتدأ", "مضاف", "مضاف إليه", "خبر"],
    "جَاءَ أَخُوهُ مُسْرِعًا": ["فعل", "فاعل", "مضاف", "مضاف إليه", "حال"],
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
