"""What is written onto a word, and the doer inside a verb, as the analyser shows them.

Runs typed sentences through the real endpoint and parser: the cards and the
picture a reader sees, not the functions behind them. A piece written onto a word
(بِـ، وَ، ـهُ) is a word of its own in the picture, with its own column.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.syntax.catib_onnx import files_present

pytestmark = pytest.mark.skipif(not files_present(), reason="CATiB parser model files not present")
client = TestClient(app)
CONDITION = "إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا"
HADITH = "أَعَدَّ اللَّهُ لِمَنْ خَرَجَ فِي سَبِيلِهِ لاَ يُخْرِجُهُ إِلاَّ جِهَادٌ فِي سَبِيلِي وَإِيمَانٌ بِي وَتَصْدِيقٌ بِرُسُلِي"


def analysed(sentence: str) -> tuple[list[dict], dict[str, list[tuple[dict, dict]]]]:
    """The cards, and each column's leaf with the unit around it, by the column's text."""
    body = client.post("/api/analyze", json={"sentence": sentence}).json()
    columns = body["tree"]["words"]
    leaves: dict[str, list[tuple[dict, dict]]] = {}

    def walk(node, unit):
        if node.get("word") is not None:
            leaves.setdefault(columns[node["word"]], []).append((node, unit))
        for child in node.get("children", []):
            walk(child, node)
    walk(body["tree"]["tree"], {})
    return body["words"], leaves


def parts(leaf: dict) -> list[str]:
    return [part["role"] for part in leaf.get("parts", [])]


def test_the_answer_shows_its_fa_its_doer_and_its_object():
    _, leaves = analysed(CONDITION)
    assert leaves["فَ"][0][0]["role"] == "حرف رابط"
    answer = leaves["اقْبَلْهَا"][0][0]
    assert parts(answer) == ["فعل", "فاعل", "مفعول به"]
    assert "أنتَ" in answer["parts"][1]["detail"]
    assert parts(leaves["كُنْتَ"][0][0]) == ["فعل ناقص", "اسم كان"]


def test_a_passive_verb_is_said_passive_and_its_object_is_the_second():
    cards, _ = analysed(CONDITION)
    assert "مبني للمجهول" in cards[4]["reason"]
    assert "مبني للمجهول" not in cards[1]["reason"]  # كُنْتَ opens with a damma, active all the same
    assert "المفعول الثاني" in cards[5]["book"]


def test_a_preposition_written_onto_a_relative_heads_a_jar_majroor_with_its_silah():
    _, leaves = analysed(HADITH)
    jar, unit = leaves["لِ"][0]
    assert jar["role"] == "حرف جر"
    assert unit["label"] == "متعلق بـأَعَدَّ"
    majroor = next(kid for kid in unit["children"] if kid is not jar)
    assert majroor["role"] == "مجرور" and majroor["label"] == "اِسْمٌ مَوْصُوْلٌ وَصِلَتُهُ"


def test_a_joining_waw_and_a_preposition_with_its_pronoun_are_words_of_their_own():
    _, leaves = analysed(HADITH)
    assert {leaf["role"] for leaf, _ in leaves["وَ"]} == {"حرف عطف"}
    jar, unit = leaves["بِ"][0]
    assert unit["label"].startswith("متعلق بـ")
    assert [kid["role"] for kid in unit["children"]] == ["حرف جر", "مجرور"]
    mudaf, idafa = leaves["سَبِيلِ"][0]
    assert [kid["role"] for kid in idafa["children"]] == ["مضاف", "مضاف إليه"]


def test_lau_opens_a_condition_whose_answer_its_lam_ties_on():
    body = client.post("/api/analyze", json={"sentence": "لَوْ جَاءَ زَيْدٌ لَأَكْرَمْتُهُ"}).json()
    top = body["tree"]["tree"]
    # book shape: the لام stands beside the answer's sentence, not inside it
    assert [kid["role"] for kid in top["children"]] == [
        "حرف شرط غير جازم", "فعل الشرط", "حرف واقع في جواب الشرط", "جواب الشرط"]
    assert {top["children"][i]["detail"] for i in (1, 3)} == {"لا محل لها من الإعراب"}


def test_the_chart_says_lam_al_amr_and_writes_the_verb_once():
    _, leaves = analysed("مَنْ شَاءَ فَلْيَصُمْهُ")
    lam, sentence = leaves["لْ"][0]
    assert lam["role"] == "لام الأمر"
    assert sentence["role"] == "جواب الشرط" and leaves["فَ"][0][0]["role"] == "حرف رابط"
    assert leaves["فَ"][0][1] is not sentence  # فَـ is outside the answer's sentence


def test_ghair_is_named_on_the_chart_as_its_card_says():
    cards, leaves = analysed("جَاءَ الطُّلَّابُ غَيْرَ زَيْدٍ")
    ghair, unit = leaves["غَيْرَ"][0]
    assert cards[2]["role"] == ghair["role"] == "مستثنى"
    assert [kid["role"] for kid in unit["children"]] == ["مستثنى", "مضاف إليه"]


def test_man_before_a_verb_is_never_min_and_its_card_says_what_the_picture_does():
    cards, leaves = analysed("مَنْ شَاءَ فَلْيَصُمْهُ وَمَنْ شَاءَ أَفْطَرَ")
    assert cards[0]["role"] == leaves["مَنْ"][0][0]["role"] != "حرف جر"
    assert cards[3]["role"] == leaves["مَنْ"][1][0]["role"]
    cards, _ = analysed("خَرَجْتُ مِنْ الْبَيْتِ")
    assert cards[1]["role"] == "حرف جر"


def test_a_noun_with_pieces_on_it_is_not_read_as_a_command():
    cards, _ = analysed("الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ")
    assert cards[6]["role"] == "معطوف"


def test_a_command_is_never_passive():
    cards, leaves = analysed("اُكْتُبُوا الدَّرْسَ")
    assert "مبني للمجهول" not in cards[0]["reason"]
    assert "أنتم" in leaves["اُكْتُبُوا"][0][0]["parts"][1]["detail"]


def test_a_ta_verb_after_a_third_person_subject_is_she():
    _, leaves = analysed("هِنْدٌ تَكْتُبُ")
    assert leaves["تَكْتُبُ"][0][0]["parts"][1]["detail"].endswith("هي")


@pytest.mark.parametrize("sentence, khabar, unit_job", [
    ("الْحَمْدُ لِلَّهِ", "خبر", None),
    ("زَيْدٌ فِي الدَّارِ", "خبر", None),
    ("زَيْدٌ عِنْدَكَ", "خبر", "مفعول فيه"),
    ("لَا رَيْبَ فِيهِ", "خبر إن", None),
    ("إِنَّ زَيْدًا فِي الدَّارِ", "خبر إن", None),
])
def test_a_jar_or_zarf_in_the_khabar_slot_hangs_on_an_understood_thabit(sentence, khabar, unit_job):
    _, leaves = analysed(sentence)
    (thabit, above), = leaves["ثابت"]
    assert thabit["role"] == khabar and thabit["hidden"] is True
    # the book's row: the subject, (ثابت) خبر, then the unit hung on it, side by side
    assert above["label"] == "جُمْلَةٌ اِسْمِيَّةٌ" and len(above["children"]) >= 3
    unit = next(kid for kid in above["children"] if kid.get("label"))
    assert unit["label"] == "متعلق بـثابت" and unit["role"] == unit_job
    body = client.post("/api/analyze", json={"sentence": sentence}).json()["tree"]
    assert body["written"].count(-1) == 1 and body["unwritten"]["note"]


@pytest.mark.parametrize("sentence", ["ذَهَبَ زَيْدٌ إِلَى السُّوقِ", "زَيْدٌ قَائِمٌ فِي الدَّارِ", "مَرَرْتُ بِزَيْدٍ"])
def test_a_jar_hanging_on_a_verb_or_a_khabar_gets_no_understood_word(sentence):
    _, leaves = analysed(sentence)
    assert "ثابت" not in leaves


@pytest.mark.parametrize("sentence, noun, name", [
    ("أَهْلًا وَسَهْلًا", "أَهْلًا", None),
    ("شُكْرًا لَكَ", "شُكْرًا", "مفعول مطلق"),
])
def test_a_nasb_noun_no_word_governs_hangs_on_an_understood_verb(sentence, noun, name):
    cards, leaves = analysed(sentence)
    (verb, above), = leaves["فعل محذوف"]
    assert verb["role"] == "فعل" and verb["hidden"] is True
    assert above["label"] == "جُمْلَةٌ فِعْلِيَّةٌ"
    named = leaves[noun][0][0]["role"]
    assert named == name if name else named in ("مفعول مطلق", "مفعول به")
    assert cards[0]["role"] == named  # the card says what the picture does
    body = client.post("/api/analyze", json={"sentence": sentence}).json()["tree"]
    assert body["written"].count(-1) == 1 and body["unwritten"]["note"]


@pytest.mark.parametrize("sentence", ["هَرَبَ الْوَلَدُ خَوْفًا", "رَأَيْتُ زَيْدًا", "إِنَّ زَيْدًا قَائِمٌ", "كَانَ زَيْدٌ قَائِمًا"])
def test_a_noun_a_word_governs_gets_no_understood_verb(sentence):
    _, leaves = analysed(sentence)
    assert "فعل محذوف" not in leaves
