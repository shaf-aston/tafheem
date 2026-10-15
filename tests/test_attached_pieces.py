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
    assert parts(answer) == ["فعل أمر", "فاعل", "مفعول به"]  # اقْبَلْهَا is a command, so it says so
    assert "أنتَ" in answer["parts"][1]["detail"]
    assert answer["parts"][1]["pronoun"] == "أنتَ"  # the chart writes it under the doer
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


@pytest.mark.parametrize("sentence, job", [("جَاءَ غَيْرُكَ", "فاعل"), ("رَأَيْتُ غَيْرَكَ", "مفعول به")])
def test_ghair_with_no_group_before_it_does_the_verbs_own_job(sentence, job):
    cards, _ = analysed(sentence)
    assert cards[1]["role"] == job


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
    ("لَا رَيْبَ فِيهِ", "خبر لا", None),
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


@pytest.mark.parametrize("sentence", ["هَرَبَ الْوَلَدُ خَوْفًا", "رَأَيْتُ زَيْدًا", "إِنَّ زَيْدًا قَائِمٌ", "كَانَ زَيْدٌ قَائِمًا",
                                      "نِعْمَ الرَّجُلُ سَعِيدٌ", "مَا أَجْمَلَ الرَّبِيعَ",
                                      "كُلُّ أُمَّتِي مُعَافًى إِلَّا الْمُجَاهِرِينَ"])
def test_a_noun_a_word_governs_gets_no_understood_verb(sentence):
    _, leaves = analysed(sentence)
    assert "فعل محذوف" not in leaves


@pytest.mark.parametrize("sentence, noun, pair", [
    ("لَا رَجُلَ فِي الدَّارِ", "رَجُلَ", ("اسم لا", "خبر لا")),
    ("لَا إِلَهَ إِلَّا اللَّهُ", "إِلَهَ", ("اسم لا", None)),
    ("إِنَّ زَيْدًا فِي الدَّارِ", "زَيْدًا", ("اسم إن", "خبر إن")),  # control: إنّ keeps its own name
])
def test_a_governor_of_the_inna_family_names_its_pair_by_its_own_name(sentence, noun, pair):
    cards, leaves = analysed(sentence)
    assert leaves[noun][0][0]["role"] == pair[0] and next(c for c in cards if c["word"] == noun)["role"] == pair[0]
    assert pair[1] is None or leaves["ثابت"][0][0]["role"] == pair[1]


def test_la_before_a_noun_in_raf_is_a_plain_negation_not_the_genus():
    cards, leaves = analysed("أَلَا إِنَّ أَوْلِيَاءَ اللَّهِ لَا خَوْفٌ عَلَيْهِمْ")
    assert leaves["لَا"][0][0]["role"] == "لا النافية"
    assert next(c for c in cards if c["word"] == "خَوْفٌ")["role"] == "مبتدأ"
    assert next(c for c in cards if c["word"] == "أَوْلِيَاءَ")["role"] == "اسم إن"  # control
    assert leaves["أَلَا"][0][0]["role"] == "حرف استفتاح وتنبيه"  # control


def test_alla_with_a_shadda_is_an_merged_with_la_and_its_verb_is_nasb():
    cards, leaves = analysed("أَمَرَ أَلَّا تَعْبُدُوا إِلَّا إِيَّاهُ")
    assert leaves["أَ"][0][0]["role"] == "حرف نصب ومصدر" and leaves["لَّا"][0][0]["role"] == "لا النافية"
    assert next(c for c in cards if c["word"] == "تَعْبُدُوا")["case"] == "nasb"
    control, _ = analysed("لَا تَذْهَبْ")
    assert control[1]["case"] == "jazm"  # لا الناهية is untouched
    _, noun_leaves = analysed("أَمَرَ أَلَّا الرَّجُلُ")  # لا before a noun: no merged nasb reading
    assert all(found[0][0]["role"] != "حرف نصب ومصدر" for found in noun_leaves.values())


@pytest.mark.parametrize("sentence, word", [("إِيَّاكَ نَعْبُدُ", "إِيَّاكَ"), ("مَا ضَرَبْتُ إِلَّا إِيَّاهُ", "إِيَّاهُ")])
def test_a_detached_pronoun_is_one_word_and_an_object_built_in_the_place_of_nasb(sentence, word):
    cards, leaves = analysed(sentence)
    assert len(leaves[word]) == 1 and leaves[word][0][0]["role"] == "مفعول به" and not leaves[word][0][0]["parts"]
    card = next(c for c in cards if c["word"] == word)
    assert card["role"] == "مفعول به" and card["case"] == "mabni" and "في محل نصب" in card["reason"]


def card_of(cards: list[dict], word: str) -> dict:
    return next(c for c in cards if c["word"] == word)


@pytest.mark.parametrize("sentence, word, case, sign", [
    ("جَاءَ الطُّلَّابُ غَيْرَ زَيْدٍ", "غَيْرَ", "nasb", "فتحة"),
    ("جَاءَ الْقَوْمُ سِوَى زَيْدٍ", "سِوَى", "nasb", "فتحة مقدرة على الألف للتعذر"),  # the alef hides the case
])
def test_ghayr_and_siwa_are_the_excepted_noun_and_say_so_themselves(sentence, word, case, sign):
    card = card_of(analysed(sentence)[0], word)
    assert (card["role"], card["case"], card["sign"]) == ("مستثنى", case, sign)
    assert "إلا" not in card["reason"] and "على الاستثناء" in card["reason"] and "مضاف" in card["reason"]
    control = card_of(analysed("جَاءَ الطُّلَّابُ إِلَّا زَيْدًا")[0], "زَيْدًا")
    assert control["role"] == "مستثنى" and "بعد إلا" in control["reason"]  # إلا keeps its own rule
    assert card_of(analysed("جَاءَ غَيْرُكَ")[0], "غَيْرُكَ")["role"] == "فاعل"


def test_a_ya_ending_takes_the_case_its_role_gives_it():
    cards, _ = analysed("كُلُّ أُمَّتِي مُعَافًى إِلَّا الْمُجَاهِرِينَ")
    assert (card_of(cards, "الْمُجَاهِرِينَ")["case"], card_of(cards, "الْمُجَاهِرِينَ")["sign"]) == ("nasb", "الياء، جمع مذكر سالم")
    assert card_of(analysed("رَأَيْتُ الْمُسْلِمِينَ")[0], "الْمُسْلِمِينَ")["case"] == "nasb"
    assert card_of(analysed("مَرَرْتُ بِالْمُسْلِمِينَ")[0], "بِالْمُسْلِمِينَ")["case"] == "jarr"  # control


@pytest.mark.parametrize("sentence, tool, noun, tool_role, noun_role", [
    ("جَاءَ الْقَوْمُ خَلَا زَيْدًا", "خَلَا", "زَيْدًا", "فعل", "مفعول به"),
    ("جَاءَ الْقَوْمُ خَلَا زَيْدٍ", "خَلَا", "زَيْدٍ", "حرف جر", "مجرور"),
    ("خَلَا الْبَيْتُ", "خَلَا", "الْبَيْتُ", "فعل", "فاعل"),  # control: the ordinary verb, no exception
])
def test_khala_is_a_verb_or_a_preposition_by_the_case_of_the_noun_after_it(sentence, tool, noun, tool_role, noun_role):
    cards, _ = analysed(sentence)
    assert (card_of(cards, tool)["role"], card_of(cards, noun)["role"]) == (tool_role, noun_role)


def test_ma_before_ada_is_the_masdar_particle_not_a_relative():
    cards, leaves = analysed("حَضَرَ الطُّلَّابُ مَا عَدَا خَالِدًا")
    assert leaves["مَا"][0][0]["role"] == "ما المصدرية، حرف مصدري" and "المصدرية" in card_of(cards, "مَا")["reason"]
    assert (card_of(cards, "عَدَا")["role"], card_of(cards, "خَالِدًا")["role"]) == ("فعل", "مفعول به")
    _, relative = analysed("أَعْجَبَنِي مَا قَرَأْتُ")
    assert relative["مَا"][0][0]["role"] == "اسم موصول"  # control


ILLA = "الصَّلَوَاتِ الْخَمْسَ إِلَّا أَنْ تَطَّوَّعَ شَيْئًا"
BUKHARI = "أَخْبِرْنِي مَاذَا فَرَضَ اللَّهُ عَلَيَّ مِنَ الصَّلَاةِ فَقَالَ " + ILLA


def test_a_noun_with_its_followers_and_no_governor_hangs_on_an_understood_verb():
    cards, leaves = analysed(ILLA)
    (verb, above), = leaves["فعل محذوف"]
    assert verb["hidden"] is True and above["label"] == "جُمْلَةٌ فِعْلِيَّةٌ"
    unit = next(kid for kid in above["children"] if kid.get("role") == "مفعول به")
    assert unit["label"] == "مُرَكَّبٌ تَوْصِيْفِيٌّ" and cards[0]["role"] == "مفعول به"
    # nothing settles who "you or she" is, so the doer is still said both ways
    assert "ضمير مستتر تقديره أنتَ أو هي" in [p["detail"] for p in leaves["تَطَّوَّعَ"][0][0]["parts"]]


def test_the_answer_to_a_question_hangs_on_the_questions_verb_and_is_said_to_the_asker():
    _, leaves = analysed(BUKHARI)
    (verb, above), = [pair for pair in leaves["فَرَضَ"] if pair[0].get("hidden")]
    assert verb["role"] == "فعل محذوف"
    assert (above["role"], above["detail"]) == ("مقول القول", "في محل نصب")
    unit = next(kid for kid in above["children"] if kid.get("role") == "مفعول به")
    assert unit["detail"] == "لـ«فَرَضَ» المحذوف"
    assert "ضمير مستتر تقديره أنتَ" in [p["detail"] for p in leaves["تَطَّوَّعَ"][0][0]["parts"]]
    body = client.post("/api/analyze", json={"sentence": BUKHARI}).json()["tree"]
    assert body["written"].count(-1) == 1


def test_the_reply_takes_the_verb_the_question_word_is_the_object_of():
    _, leaves = analysed("مَاذَا قَرَأْتَ؟ قَالَ الْقُرْآنَ")
    assert [leaf["hidden"] for leaf, _ in leaves["قَرَأْتَ"] if leaf.get("hidden")] == [True]


@pytest.mark.parametrize("sentence", ["قَالَ الْحَقَّ", "قَالَ الصَّلَوَاتِ الْخَمْسَ"])
def test_a_word_a_verb_of_saying_takes_with_no_question_before_stays_its_object(sentence):
    _, leaves = analysed(sentence)
    assert not any(leaf.get("hidden") for pairs in leaves.values() for leaf, _ in pairs)
