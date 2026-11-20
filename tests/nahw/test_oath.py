"""The oath (Ibn Aqil, باب القسم, vol 4 p42; page unchecked).

With و or ت the verb of swearing is left out: the jar is «متعلق بفعل القسم المحذوف تقديره أُقْسِمُ», the letter is «حرف قسم
وجر», and the sentence sworn is «جواب القسم», with no place. A لام opening that answer is «اللام الواقعة في جواب القسم».
When the oath comes before a condition (لَئِنْ), the لام on إنْ is «اللام الموطئة للقسم» and the answer is the oath's, the
condition's left out (Alfiyya: واحذف لدى اجتماع شرط وقسم جواب ما أخرت; page unchecked).

The nun of emphasis on one of the five verbs: their own nun went so three nuns do not meet, and the verb stays مرفوع
(«ثبوت النون المحذوفة لتوالي الأمثال»); a verb none of the five is built on the fatha.
"""
import pytest

from backend.services.nahw.book import reseated
from tests.nahw_helpers import analyze, card, cards, needs_parser

pytestmark = needs_parser

ATTACHED = "متعلق بفعل القسم المحذوف تقديره «أُقْسِمُ»"
NO_PLACE = "لا محل لها من الإعراب"


def nodes(node: dict):
    yield node
    for kid in node.get("children", []):
        yield from nodes(kid)


def top(sentence: str) -> dict:
    return analyze(sentence)["tree"]["tree"]


def roles(node: dict) -> list:
    return [n.get("role") for n in nodes(node)]


@pytest.mark.parametrize("sentence, letter_at", [
    ("وَاللَّهِ لَأَفْعَلَنَّ", 0),
    ("تَاللَّهِ لَأَكِيدَنَّ أَصْنَامَكُمْ", 0),  # ت: the parser hangs the sentence on the oath letter
    ("وَاللَّهِ لَقَدْ قَامَ زَيْدٌ", 0),
    ("وَالْعَصْرِ إِنَّ الْإِنْسَانَ لَفِي خُسْرٍ", 0),
    ("فَوَاللَّهِ مَا الْفَقْرَ أَخْشَى عَلَيْكُمْ", 1),  # the ف before it stays at the front
    ("وَالَّذِي نَفْسِي بِيَدِهِ لَا تَدْخُلُونَ الْجَنَّةَ", 0),  # sworn by a relative
    ("وَرَبِّ الْكَعْبَةِ لَأَفْعَلَنَّ", 0),  # sworn by a مضاف: the answer opens after its مضاف إليه
])
def test_the_oath_letter_hangs_on_the_verb_left_out_and_the_sentence_sworn_is_its_answer(sentence, letter_at):
    picture = top(sentence)
    assert picture["label"] == "جُمْلَةٌ فِعْلِيَّةٌ"
    oath = picture["children"][letter_at]
    assert oath["label"] == ATTACHED and oath["children"][0]["role"] == "حرف قسم وجر"
    answer = picture["children"][letter_at + 1]
    assert answer["role"] == "جواب القسم" and answer["detail"] == NO_PLACE


def test_the_lam_opening_the_answer_is_the_oaths_but_a_lam_inside_inna_stays_emphasis():
    assert "اللام الواقعة في جواب القسم" in roles(top("وَاللَّهِ لَقَدْ قَامَ زَيْدٌ"))
    assert "اللام الواقعة في جواب القسم" in roles(top("وَاللَّهِ إِنْ قَامَ زَيْدٌ لَأَقُومَنَّ"))  # the لام, not the إنْ before it
    sworn = roles(top("وَاللَّهِ إِنَّ زَيْدًا لَقَائِمٌ"))
    assert "جواب القسم" in sworn and "لام التوكيد" in sworn and "اللام الواقعة في جواب القسم" not in sworn
    assert "اللام الواقعة في جواب القسم" not in roles(top("فَوَاللَّهِ مَا الْفَقْرَ أَخْشَى عَلَيْكُمْ"))  # a ما is no لام


def test_the_oath_jar_is_no_khabar_left_out():
    # وَالْعَصْرِ is no متعلق بثابت: only the jar inside إنّ's khabar is
    labels = [n.get("label") for n in nodes(top("وَالْعَصْرِ إِنَّ الْإِنْسَانَ لَفِي خُسْرٍ"))]
    assert labels.count(ATTACHED) == 1 and labels.count("متعلق بـثابت") == 1


@pytest.mark.parametrize("sentence, parts", [
    ("أُقْسِمُ بِاللَّهِ لَأَفْعَلَنَّ", ["فعل", "متعلق بـأُقْسِمُ", "جواب القسم"]),
    ("أُقْسِمُ لَأَفْعَلَنَّ", ["فعل", "جواب القسم"]),  # no jar: the answer straight after the verb
])
def test_a_written_verb_of_swearing_keeps_its_jar_and_names_the_answer(sentence, parts):
    picture = top(sentence)
    assert [kid.get("role") or kid.get("label") for kid in picture["children"]] == parts
    assert "اللام الواقعة في جواب القسم" in roles(picture)
    assert ATTACHED not in [n.get("label") for n in nodes(picture)]


@pytest.mark.parametrize("sentence", [
    "وَاللَّهُ غَفُورٌ رَحِيمٌ",  # و before a مرفوع: no oath
    "حَلَفَ زَيْدٌ بِاللَّهِ",  # a verb of swearing with nothing sworn
    "مَرَرْتُ بِزَيْدٍ وَعَمْرٍو لَقَدْ قَامَا",  # a jarr by و's joining, then a لام
    "إِنْ تَدْرُسْ تَنْجَحْ",
    "لَا أُقْسِمُ بِيَوْمِ الْقِيَامَةِ",  # sworn with nothing after it: no answer
    "وَلَيْلٍ كَمَوْجِ الْبَحْرِ أَرْخَى سُدُولَهُ",  # واو رُبّ before an indefinite: its jar hangs on the verb after
    (
        "وَالَّذِينَ جَاءُوا مِن بَعْدِهِمْ يَقُولُونَ رَبَّنَا اغْفِرْ لَنَا وَلِإِخْوَانِنَا الَّذِينَ سَبَقُونَا بِالْإِيمَانِ وَلَا تَجْعَلْ فِي قُلُوبِنَا غِلًّا لِّلَّذِينَ آمَنُوا رَبَّنَا إِنَّكَ رَءُوفٌ رَّحِيمٌ"),  # a relative opening a مبتدأ (59:10), no oath
])
def test_no_oath_where_none_is_sworn(sentence):
    picture = top(sentence)
    assert "جواب القسم" not in roles(picture)
    assert ATTACHED not in [n.get("label") for n in nodes(picture)]


@pytest.mark.parametrize("sentence, front", [
    ("لَئِنْ شَكَرْتُمْ لَأَزِيدَنَّكُمْ", []),
    ("وَلَئِنْ سَأَلْتَهُمْ لَيَقُولُنَّ اللَّهُ", ["حرف عطف"]),  # the و before it stays at the condition's front
    ("لَئِنْ أَكْرَمْتَنِي لَأُكْرِمَنَّكَ", []),
])
def test_after_lain_the_answer_is_the_oaths_and_the_conditions_is_left_out(sentence, front):
    picture = top(sentence)
    assert picture["label"] == "جُمْلَةٌ فِعْلِيَّةٌ"
    condition = next(n for n in nodes(picture) if n.get("label") == "جُمْلَةٌ شَرْطِيَّةٌ")
    assert [kid.get("role") for kid in condition["children"]] == [*front, "اللام الموطئة للقسم", "حرف شرط جازم", "فعل الشرط"]
    assert condition["children"][-1]["detail"] == NO_PLACE
    answer = picture["children"][1]
    assert answer["role"] == "جواب القسم"
    assert answer["detail"] == NO_PLACE + "، وجواب الشرط محذوف دل عليه جواب القسم"
    assert "اللام الواقعة في جواب القسم" in roles(answer)
    assert cards(sentence)[0]["reason"].startswith("حرف شرط جازم")


def test_a_plain_conditions_answer_is_its_own():
    picture = top("إِنْ تَدْرُسْ تَنْجَحْ")
    assert [kid.get("role") for kid in picture["children"]][:2] == ["حرف شرط جازم", "فعل الشرط"]
    assert cards("إِنْ تَدْرُسْ تَنْجَحْ")[0]["reason"].startswith("حرف شرط جازم")


def test_a_hamza_moved_onto_ya_by_a_joined_letter_is_read_on_its_alif():
    assert reseated("ئن", "إِن") == "إن"
    assert reseated("ئِنْ", "إن") == "إِنْ"
    assert reseated("ئن", "ئن") == "ئن"  # the lemma is not that word on its alif
    assert reseated("يئس", "يئس") == "يئس"  # a ئ inside its word is its own


@pytest.mark.parametrize("sentence, word, doer", [
    ("وَلَئِنْ سَأَلْتَهُمْ لَيَقُولُنَّ اللَّهُ", "لَيَقُولُنَّ", "(هم)"),  # يَقُولُونَ
    ("وَاللَّهِ لَتَقُولِنَّ الْحَقَّ", "لَتَقُولِنَّ", "(أنتِ)"),  # تَقُولِينَ: the kasra shows the ياء gone
    ("وَاللَّهِ لَتَذْهَبَانِّ", "لَتَذْهَبَانِّ", "(هما)"),  # تَذْهَبَانِ
])
def test_one_of_the_five_verbs_before_the_nun_of_emphasis_stays_marfu(sentence, word, doer):
    found = card(sentence, word)
    assert found["sign"] == "ثبوت النون المحذوفة لتوالي الأمثال"
    assert found["reason"].startswith("فعل مضارع مرفوع") and doer in found["reason"]


@pytest.mark.parametrize("sentence, word, sign, said", [
    ("وَاللَّهِ لَتَقُولَنَّ الْحَقَّ", "لَتَقُولَنَّ", "مبني على الفتح", "القاعدة: يُبنى الفعل المضارع على الفتح إذا باشرته نون التوكيد"),
    ("الطَّالِبَاتُ يَرْسُمْنَ", "يَرْسُمْنَ", "مبني على السكون", "القاعدة: يُبنى الفعل المضارع على السكون إذا اتصلت به نون النسوة"),
    ("لَنْ يَظُنَّ زَيْدٌ ذَلِكَ", "يَظُنَّ", "فتحة", "فعل مضارع منصوب"),  # a doubled root's ن is no nun of emphasis
    ("لَا تَقُولُنَّ ذَلِكَ", "تَقُولُنَّ", "حذف النون", "فعل مضارع مجزوم"),  # after لا الناهية the five verbs' nun is jazm's
])
def test_the_nearest_verbs_are_built_or_keep_their_own_case(sentence, word, sign, said):
    found = card(sentence, word)
    assert found["sign"] == sign and said in found["reason"]


def test_a_sworn_noun_joined_by_waw_stays_inside_the_oath_jar():
    picture = top("وَالْفَجْرِ وَلَيَالٍ عَشْرٍ")
    assert picture["label"] == "جَارٌّ وَمَجْرُوْرٌ"
    assert "معطوف عليه" in roles(picture)


def test_a_lam_answering_ta_is_the_oaths_and_its_verb_is_not_split_off():
    picture = top("تَاللَّهِ لَأَكِيدَنَّ أَصْنَامَكُمْ")
    answer = picture["children"][1]
    assert [kid.get("role") for kid in answer["children"]][:2] == ["اللام الواقعة في جواب القسم", "فعل"]


@pytest.mark.parametrize("sentence, word, said", [
    ("هَلْ تَضْرِبُنَّ زَيْدًا", "تَضْرِبُنَّ", "فعل مضارع مرفوع"),  # تَضْرِبُونَ: the doubled nun is emphasis, no jazm
    ("لَتُبْلَوُنَّ فِي أَمْوَالِكُمْ", "لَتُبْلَوُنَّ", "(أنتم)"),  # the و kept with its damma: masculine plural
])
def test_an_emphasised_five_verb_keeps_its_case_and_its_doer(sentence, word, said):
    assert said in card(sentence, word)["reason"]
