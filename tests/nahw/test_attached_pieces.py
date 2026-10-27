"""What is written onto a word, and the doer inside a verb, as the analyser shows them.

Runs typed sentences through the real endpoint and parser: the cards and the
picture a reader sees, not the functions behind them. A piece written onto a word
(بِـ، وَ، ـهُ) is a word of its own in the picture, with its own column.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.syntax.catib_onnx import files_present

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


def thabit_in(leaves: dict) -> list[tuple[dict, dict]]:
    """The understood ثابت's leaves, however it is voweled."""
    return [pair for text, found in leaves.items() if strip_diacritics(text).removesuffix("ا") == "ثابت" for pair in found]  # ثَابِتًا writes its tanween on an alif


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


@pytest.mark.parametrize("sentence", ["اكْتُبِي الدَّرْسَ", "اشْرَبُوا المَاءَ", "اجْلِسْ هُنَا"])
def test_a_command_typed_with_its_hamzat_al_wasl_is_a_verb(sentence):
    """The bare alef before a sukun is hamzat al-wasl: never the أَفْعَل its letters also spell."""
    cards, _ = analysed(sentence)
    assert cards[0]["role"] == "فعل"


@pytest.mark.parametrize("sentence, verb", [
    ("افْعَلِي مَا يَفْعَلُ الحَاجُّ غَيْرَ أَنْ لَا تَطُوفِي بِالبَيْتِ", "تَطُوفِي"),
    ("ادْرُسُوا الكُتُبَ غَيْرَ أَنْ لَا تَسْهَرُوا", "تَسْهَرُوا"),
])
def test_ghair_before_an_masdar_is_the_mustathna_and_the_masdar_its_mudaf_ilayh(sentence, verb):
    """غَيْرَ أنْ لا ...: غير is the مستثنى, مضاف to the masdar أنْ and its verb make; no
    مفعول به inside a مفعول به. The لا after أنْ only negates: the verb is أنْ's, in nasb."""
    cards, leaves = analysed(sentence)
    ghair, unit = leaves["غَيْرَ"][0]
    assert ghair["role"] == "مستثنى"
    assert [kid["role"] for kid in unit["children"]] == ["مستثنى", "مضاف إليه"]
    card = {c["word"]: c for c in cards}
    assert card[verb]["case"] == "nasb"
    assert leaves["لَا"][0][0]["role"] == "لا النافية"


def test_la_after_an_negates_and_alone_forbids():
    cards, leaves = analysed("لَا تَذْهَبُوا")
    assert cards[1]["case"] == "jazm" and leaves["لَا"][0][0]["role"] == "لا الناهية"
    cards, _ = analysed("أُحِبُّ أَنْ لَا تَذْهَبُوا")
    assert cards[3]["case"] == "nasb"


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


@pytest.mark.parametrize("sentence, khabar, unit_job, drawn", [
    ("الْحَمْدُ لِلَّهِ", "خبر", None, "ثَابِتٌ"),
    ("زَيْدٌ فِي الدَّارِ", "خبر", None, "ثَابِتٌ"),
    ("زَيْدٌ عِنْدَكَ", "خبر", "مفعول فيه", "ثَابِتٌ"),
    ("لَا رَيْبَ فِيهِ", "خبر لا", None, "ثَابِتٌ"),
    ("إِنَّ زَيْدًا فِي الدَّارِ", "خبر إن", None, "ثَابِتٌ"),
])
def test_a_jar_or_zarf_in_the_khabar_slot_hangs_on_an_understood_thabit(sentence, khabar, unit_job, drawn):
    """The word no one writes is voweled for its place: a khabar in raf' is ثَابِتٌ."""
    _, leaves = analysed(sentence)
    (thabit, above), = leaves[drawn]
    assert thabit["role"] == khabar and thabit["hidden"] is True
    # the book's row: the subject, (ثابت) خبر, then the unit hung on it, side by side
    assert above["label"] == "جُمْلَةٌ اِسْمِيَّةٌ" and len(above["children"]) >= 3
    unit = next(kid for kid in above["children"] if kid.get("label"))
    assert unit["label"] == "متعلق بـثابت" and unit["role"] == unit_job
    body = client.post("/api/analyze", json={"sentence": sentence}).json()["tree"]
    assert body["written"].count(-1) == 1 and body["unwritten"]["note"]


@pytest.mark.parametrize("sentence, drawn", [("كَانَ زَيْدٌ فِي الدَّارِ", "ثَابِتًا"), ("أَصْبَحَ الْمَاءُ فِي الْبِئْرِ", "ثَابِتًا"),
                                            ("الْعِلْمُ فِي الصُّدُورِ", "ثَابِتٌ")])
def test_the_understood_thabit_wears_the_case_of_its_place(sentence, drawn):
    """كان's khabar stands in nasb, so the word no one writes is ثَابِتًا; a مبتدأ's is ثَابِتٌ."""
    _, leaves = analysed(sentence)
    (thabit, _), = thabit_in(leaves)
    assert thabit["hidden"] is True and leaves.get(drawn) == thabit_in(leaves)


@pytest.mark.parametrize("sentence", ["ذَهَبَ زَيْدٌ إِلَى السُّوقِ", "زَيْدٌ قَائِمٌ فِي الدَّارِ", "مَرَرْتُ بِزَيْدٍ"])
def test_a_jar_hanging_on_a_verb_or_a_khabar_gets_no_understood_word(sentence):
    _, leaves = analysed(sentence)
    assert not thabit_in(leaves)


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



@pytest.mark.parametrize("sentence, noun", [("سُبْحَانَ اللَّهِ", "سُبْحَانَ"), ("مَعَاذَ اللَّهِ", "مَعَاذَ")])
def test_a_masdar_added_to_a_noun_hangs_on_an_understood_verb(sentence, noun):
    """Its nasb is shown by the jarr of the noun it is added to (Ibn Jinni, al-Munsif: مصدرا فألزم
    النصب نحو سبحان الله ولبيك ومعاذ الله); معاذ, of the place measure مَفْعَل, is a heard masdar.
    The مضاف and its مضاف إليه together are the مفعول مطلق."""
    cards, leaves = analysed(sentence)
    (verb, _), = leaves["فعل محذوف"]
    leaf, unit = leaves[noun][0]
    assert verb["hidden"] is True and leaf["role"] == "مضاف"
    assert unit["role"] == cards[0]["role"] == "مفعول مطلق"

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
    assert pair[1] is None or thabit_in(leaves)[0][0]["role"] == pair[1]


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
    assert not unit["label"] and cards[0]["role"] == "مفعول به"  # its job says enough
    # nothing settles who "you or she" is, so the doer is still said both ways
    assert "ضمير مستتر تقديره أنتَ أو هي" in [p["detail"] for p in leaves["تَطَّوَّعَ"][0][0]["parts"]]


@pytest.mark.parametrize("sentence, subject, khabar", [
    ("قَالَ الضَّيْفُ سَلَامٌ عَلَيْكُمْ", "سَلَامٌ", "ثَابِتٌ"),
    ("قَالَ زَيْدٌ الْجَوُّ جَمِيلٌ", "الْجَوُّ", "جَمِيلٌ"),
])
def test_the_sentence_after_said_and_its_doer_is_one_unit_its_maqul_al_qawl(sentence, subject, khabar):
    """A verb has one doer, so the raf' sentence قال holds after it is its مقول القول, in the place of
    nasb: its مبتدأ and خبر (written or the understood ثابت) sit in that one unit."""
    _, leaves = analysed(sentence)
    (_, unit), = leaves[subject]
    assert (unit["role"], unit["detail"], unit["label"]) == ("مقول القول", "في محل نصب", "جُمْلَةٌ اِسْمِيَّةٌ")
    assert any(leaf["role"] == "خبر" and around is unit for leaf, around in leaves[khabar])


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


def _named(sentence: str) -> dict[str, tuple[str, str]]:
    """Each card's bare word → (its role, its reason)."""
    cards, _ = analysed(sentence)
    return {strip_diacritics(card["word"]): (card.get("name") or card.get("role") or "", card.get("reason") or "") for card in cards}


@pytest.mark.parametrize("sentence, noun, answer", [
    ("لَوْلَا الْعِلْمُ لَضَاعَ النَّاسُ", "العلم", "لضاع"),
    ("لَوْلَا خَالِدٌ لَخَسِرَ الْفَرِيقُ", "خالد", "لخسر"),
])
def test_laula_before_a_noun_opens_a_mubtada_whose_khabar_is_left_out(sentence, noun, answer):
    named = _named(sentence)
    assert named["لولا"][0] == "حرف امتناع لوجود"
    assert named[noun][0] == "مبتدأ" and "محذوف وجوبًا" in named[noun][1]
    assert "جواب لولا" in named[answer][1]


def test_laula_before_a_verb_urges():
    assert _named("لَوْلَا تَذْكُرُونَ اللَّهَ")["لولا"][0] == "حرف عرض وتحضيض"


@pytest.mark.parametrize("sentence, khabar, role", [
    ("ظَنَنْتُ أَنَّ الْبَيْتَ وَاسِعٌ", "واسع", "خبر أن"),
    ("لَعَلَّ الْمُسَافِرَ قَادِمٌ", "قادم", "خبر لعل"),
])
def test_the_khabar_is_named_for_its_own_governor(sentence, khabar, role):
    assert _named(sentence)[khabar][0] == role


@pytest.mark.parametrize("sentence", ["لَا إِلَٰهَ إِلَّا اللَّهُ", "لا إله إلا الله", "لَا إِلَٰهَ إِلَّا هُوَ"])
def test_the_shahada_draws_its_unsaid_khabar_and_names_its_badal(sentence):
    """Ibn Hishām: the khabar of لا is left out, known (مَعْبُودٌ بِحَقٍّ), and sits between
    إله and إلا; اللهُ is a بدل of the pronoun hidden in it, no بدل كل من كل of the منصوب noun."""
    cards, leaves = analysed(sentence)
    (khabar, _), = leaves["مَعْبُودٌ بِحَقٍّ"]
    assert khabar["role"] == "خبر لا" and khabar["hidden"] is True
    columns = client.post("/api/analyze", json={"sentence": sentence}).json()["tree"]["words"]
    assert [strip_diacritics(c) for c in columns][1:4] == ["إله", "معبود بحق", "إلا"]
    badal = cards[-1]
    assert badal["role"] == "بدل" and badal["case"] in ("raf'", "mabni") and "الضمير المستتر في الخبر المحذوف" in badal["reason"]


def test_another_noun_after_la_keeps_its_plain_badal():
    """The تقدير is chosen for إله alone: لا رجلَ إلا زيدٌ draws no khabar of it."""
    cards, leaves = analysed("لَا رَجُلَ إِلَّا زَيْدٌ")
    assert "مَعْبُودٌ بِحَقٍّ" not in leaves and cards[-1]["reason"].endswith("بدل كل من كل")


@pytest.mark.parametrize("sentence, kind, job", [
    ("أَكَلْتُ مَا طَبَخْتَ", "relative", "مفعول به"),       # طبخ wants an object it lacks: that gap is the عائد
    ("أَعْجَبَنِي مَا كَتَبْتَهُ", "relative", "فاعل"),      # the هـ written on the verb is the عائد
    ("سَرَّنِي مَا قُمْتَ", "masdar", "فاعل"),               # قام takes no object, its doer is written: no room for one
    ("أَدْهَشَ بِمَا تُرِكَ الْعَمَلُ", "masdar", "مجرور"),  # the passive's نائب فاعل is written
])
def test_ma_is_relative_only_when_its_sila_has_room_for_an_aid(sentence, kind, job):
    """مغني اللبيب: the relative's صلة holds a pronoun going back to ما, ما المصدرية's never does."""
    cards, leaves = analysed(sentence)
    (ma, unit), = [pair for text, found in leaves.items() if strip_diacritics(text).endswith("ما") for pair in found]
    assert unit["role"] == job
    if kind == "masdar":
        assert unit["label"] == "مَصْدَرٌ مُؤَوَّلٌ" and ma["role"] == "ما المصدرية، حرف مصدري"
        assert next(c for c in cards if strip_diacritics(c["word"]).endswith("ما"))["role"] == "حرف"
    else:
        assert ma["role"] == "اسم موصول"
        card = next(c for c in cards if strip_diacritics(c["word"]) == "ما")
        assert card["role"] == job and card["case"] == "mabni"


@pytest.mark.parametrize("sentence", ["أَنْ تَدْرُسُوا يُؤَدِّي إِلَى أَنْ تَنْجَحُوا", "أَسْلَمْتُ لِكَيْ أَدْخُلَ الْجَنَّةَ"])
def test_a_masdar_on_a_preposition_is_its_majrur(sentence):
    """إلى أن تنجحوا، لكي أدخل: the masdar the particle makes is the مجرور of the حرف جر before it."""
    _, leaves = analysed(sentence)
    units = [unit for found in leaves.values() for _, unit in found if unit.get("label") == "مَصْدَرٌ مُؤَوَّلٌ"]
    assert units and units[-1]["role"] == "مجرور"


def test_a_unit_with_a_job_leaves_off_what_it_is_made_of():
    """قرأت كتابَ الطالب: مفعول به, not مفعول به / مركب إضافي; كتابُ زيدٍ alone keeps its name."""
    _, leaves = analysed("قَرَأْتُ كِتَابَ الطَّالِبِ")
    (_, unit), = leaves["كِتَابَ"]
    assert unit["role"] == "مفعول به" and not unit["label"]
    body = client.post("/api/analyze", json={"sentence": "كِتَابُ زَيْدٍ"}).json()
    assert body["tree"]["tree"]["label"] == "مُرَكَّبٌ إِضَافِيٌّ"


def test_a_weak_radical_left_unpinned_is_still_one_root():
    """سارَ سَيْرًا: without the Qur'an corpus the analyser files سار under سور, its masdar
    under سير; the weak middle letter is the same radical, so the مفعول مطلق still shows."""
    from backend.services.nahw.syntax.facts import same_root
    assert same_root({"root": "سور", "lemma": "سار"}, {"root": "سير", "lemma": "سير"})
    assert not same_root({"root": "كتب", "lemma": "كتب"}, {"root": "كسب", "lemma": "كسب"})


def _reason(sentence: str, word: str) -> str:
    from backend.scripts.nahw.score_iraab import routed
    return next(w["reason"] for w in routed(sentence, None)["words"] if w["word"] == word)


def test_a_command_typed_with_a_bare_alif_speaks_to_you():
    """اضربْ: the card names it a فعل أمر, so its hidden doer is أنتَ, never the أنا of أضربُ."""
    assert "تقديره أنتَ" in _reason("اضرب الكرة", "اضرب")
    assert "تقديره أنا" in _reason("أضرب الكرة", "أضرب")


def test_the_answer_of_a_jazm_condition_is_never_a_command():
    """إن تضربْ أضربْ: the answer after إن and its verb is the jussive present, not a command."""
    assert "جواب الشرط مجزوم" in _reason("إِنْ تَضْرِبْ أَضْرِبْ", "أَضْرِبْ")


def test_a_word_with_its_owner_written_on_is_a_noun_not_the_particle():
    """أمُّكَ: the كَ is its مضاف إليه, so it is a noun (فاعل), not the particle أَمْ."""
    assert _reason("رُبَّ أَخٍ لَكَ لَمْ تَلِدْهُ أُمُّكَ", "أُمُّكَ").startswith("مرفوع لأنه فاعل")


@pytest.mark.parametrize("rel", ["OBJ", "MOD", "TMZ"])
def test_passive_giving_verb_keeps_its_second_object(monkeypatch, rel):
    """مُنِحَ الطَّالِبُ هَدِيَّةً: the نائب فاعل is the first object, so هدية is the second
    مفعول به however the parser hung it (a CPU's rounding tipped it to MOD on CI)."""
    from backend.services.nahw import iraab
    from backend.services.nahw.syntax import catib_onnx
    real = catib_onnx.parse

    def parse(typed, picks):
        tokens = real(typed, picks)
        tokens[2]["rel"] = rel
        return tokens

    monkeypatch.setattr(catib_onnx, "parse", parse)
    assert [w["role"] for w in iraab.analyze("مُنِحَ الطَّالِبُ هَدِيَّةً")["words"]] == ["فعل مجهول", "نائب فاعل", "مفعول به"]


@pytest.mark.parametrize("rooted", [False, True])
def test_a_verb_hung_under_its_fronted_object_heads_the_sentence(monkeypatch, rooted):
    """عِلْمًا طَلَبَ زَيْدٌ: the verb has no pronoun back to عِلْمًا, so it is no صفة of it; the noun is
    the fronted مفعول به however the parser rooted it (a CPU's rounding rooted the noun on CI)."""
    from backend.services.nahw import iraab
    from backend.services.nahw.syntax import catib_onnx
    real = catib_onnx.parse

    def parse(typed, picks):
        tokens = real(typed, picks)
        if rooted:
            tokens[0]["head"], tokens[0]["rel"] = 0, "---"
            tokens[1]["head"], tokens[1]["rel"] = 1, "MOD"
        return tokens

    monkeypatch.setattr(catib_onnx, "parse", parse)
    assert [w["role"] for w in iraab.analyze("عِلْمًا طَلَبَ زَيْدٌ")["words"]] == ["مفعول به", "فعل", "فاعل"]


@pytest.mark.parametrize("sentence, moved", [("عِلْمًا طَلَبَ زَيْدٌ", True), ("عِلْمًا طَلَبَهُ زَيْدٌ", False)])
def test_a_verb_with_a_pronoun_back_to_the_noun_may_describe_it(sentence, moved):
    """طَلَبَهُ has its pronoun back to عِلْمًا, so the parser's صفة reading stands; without one it cannot."""
    from backend.services.sarf import morphology
    from backend.services.nahw import syntax
    from backend.services.nahw.syntax import catib_onnx
    from backend.services.nahw.syntax.repair import correct
    words = sentence.split()
    tokens = catib_onnx.parse(words, morphology.pick(words, syntax.disambiguator()))
    tokens[0]["head"], tokens[0]["rel"] = 0, "---"
    tokens[1]["head"], tokens[1]["rel"] = 1, "MOD"
    correct(words, tokens)
    assert (tokens[0]["head"], tokens[1]["head"]) == ((2, 0) if moved else (0, 1))


@pytest.mark.parametrize("sentence, word, want", [
    # و of company: the و's head is the verb's attached doer, not a particle
    ("سافرت والصديقَ", "والصديقَ", ("role", "مفعول معه")),
    # خُلُقُهُ is read as the noun (خُلْق), not the verb خَلَقَ, so it copies الطالب
    ("أَعْجَبَنِي الطَّالِبُ خُلُقُهُ", "خُلُقُهُ", ("role", "بدل")),
    # but a guessed name is never a verb two slips off: زَيْدًا is not زَيَّدَا
    ("رَأَيْتُ أَخَاكَ زَيْدًا", "زَيْدًا", ("role", "بدل")),
    # the manqus with tanween drops its ya: قاضٍ shows nothing, so nothing clashes
    ("هذا قاضٍ عادل", "قاضٍ", ("sign", "ضمة مقدرة على الياء المحذوفة")),
    # عسى names its own two, as كأنّ and أصبح do
    ("عَسَى اللَّهُ أَنْ يَرْحَمَنَا", "اللَّهُ", ("name", "اسم عسى")),
    # after لا النافية للجنس the missing tanween is لا's building, not a مضاف before a preposition
    ("هَذَا الْأَمْرُ لَا شَكَّ فِيهِ", "شَكَّ", ("role", "اسم لا")),
    ("الْعِلْمُ لَا حَدَّ لَهُ", "حَدَّ", ("role", "اسم لا")),
    # a مضاف إليه is مجرور, so a damma-typed الْجَوُّ cannot make بَرَدَ the noun "hail of"
    ("إِذَا جَاءَ الشِّتَاءُ بَرَدَ الْجَوُّ", "الْجَوُّ", ("role", "فاعل")),
    # كاد وأخواتها work as كان does (Alfiyya: ككان كاد وعسى), so the verb is فعل ناقص
    ("كَادَ الْقِطَارُ يَتَحَرَّكُ", "كَادَ", ("name", "فعل ناقص")),
    # جِدًّا is heard with its verb never said (جَدَّ جِدًّا): مفعول مطلق, not an object of مجتهدات
    ("الطَّالِبَاتُ مُجْتَهِدَاتٌ جِدًّا", "جِدًّا", ("role", "مفعول مطلق")),
    # ظنّ's two objects were a مبتدأ and خبر; the parser kept the pair, both typed in nasb
    ("حَسِبَ الرَّجُلُ الطَّرِيقَ قَصِيرًا", "الطَّرِيقَ", ("role", "مفعول به")),
    ("حَسِبَ الرَّجُلُ الطَّرِيقَ قَصِيرًا", "الرَّجُلُ", ("role", "فاعل")),
    # a plain noun takes no object: أكثر is زيد's khabar, مالا the elative's تمييز
    ("زَيْدٌ أَكْثَرُ مِنْكَ مَالًا", "زَيْدٌ", ("role", "مبتدأ")),
    ("زَيْدٌ أَكْثَرُ مِنْكَ مَالًا", "أَكْثَرُ", ("role", "خبر")),
    # a مضاف إليه is مجرور: a nasb noun the parser hung on an elative as one is its تمييز (Ibn Aqil V3 p174)
    ("زَيْدٌ أَكْبَرُ سِنًّا", "سِنًّا", ("role", "تمييز")),
    ("هُوَ أَفْضَلُ رَجُلٍ", "رَجُلٍ", ("role", "مضاف إليه")),  # nearest case: in jarr, the مضاف إليه
    # a doubled root's elative is أَفَلّ (أَشَدّ), its two like letters merged
    ("لَأَنْتُمْ أَشَدُّ رَهْبَةً", "رَهْبَةً", ("role", "تمييز")),
    ("هُوَ أَشَدُّ حُمْرَةً مِنْ زَيْدٍ", "حُمْرَةً", ("role", "تمييز")),
    ("هُوَ أَحَقُّ النَّاسِ بِهِ", "النَّاسِ", ("role", "مضاف إليه")),  # nearest case: in jarr
    ("هُوَ أَقَلُّ مَالًا", "مَالًا", ("role", "تمييز")),  # أَفَلّ read أَقَلّ
    ("هُوَ أَحَبُّ عَمَلًا", "عَمَلًا", ("role", "تمييز")),  # read أَحِبّ
    ("هو أفضل رجل", "رجل", ("role", "مضاف إليه")),  # nearest case: no nasb written
    ("هَذَا أَفْضَلُ مَسَاجِدَ", "مَسَاجِدَ", ("role", "مضاف إليه")),  # nearest case: a diptote's fatha is jarr
    ("سُبْحَانَكَ", "سُبْحَانَكَ", ("role", "مفعول مطلق")),  # a pronoun on a noun is in jarr's place
    ("أَطْفَأَ زَيْدٌ نَارًا", "نَارًا", ("role", "مفعول به")),  # nearest case: a verb on أَفْعَلَ, its object
    # a verb khabar needs a pronoun back to its مبتدأ, so أَنْفَعُ is the elative, not "I benefit"
    ("الْعِلْمُ أَنْفَعُ مِنَ الْمَالِ", "أَنْفَعُ", ("role", "خبر")),
    ("أَنَا أَكْتُبُ الدَّرْسَ", "أَكْتُبُ", ("role", "فعل")),
    # a hamza-final participle (قارئ) works as its verb like any other: its noun is its object
    ("يَا قَارِئًا الْقُرْآنَ تَدَبَّرْ", "الْقُرْآنَ", ("role", "مفعول به")),
    # a verb has one doer: the raf' word قال holds after its doer opens the sentence it says
    ("قَالَ الضَّيْفُ سَلَامٌ عَلَيْكُمْ", "سَلَامٌ", ("role", "مبتدأ")),
    ("قَالَ زَيْدٌ الْجَوُّ جَمِيلٌ", "الْجَوُّ", ("role", "مبتدأ")),
    ("قَالَ زَيْدٌ الْجَوُّ جَمِيلٌ", "جَمِيلٌ", ("role", "خبر")),
    ("قَالَ الرَّجُلُ الْحَقَّ", "الْحَقَّ", ("role", "مفعول به")),
    # Nahw Basics 4-5 (Fil, Musnad): a noun hung on the verb with no relation is still its argument
    ("نَصَرَ زَيْدٌ بَكْرًا", "زَيْدٌ", ("role", "فاعل")),
    ("نَصَرَ زَيْدٌ بَكْرًا", "بَكْرًا", ("role", "مفعول به")),
    ("نُصِرَ بَكْرٌ", "بَكْرٌ", ("role", "نائب فاعل")),
    # Jumla Filiyya p4: the مفعول به, no essential, may come before the verb
    ("عِلْمًا طَلَبَ زَيْدٌ", "عِلْمًا", ("role", "مفعول به")),
    # a tamyeez of the relation after a verb that takes no object (Maryam 4)
    ("اِشْتَعَلَ الرَّأْسُ شَيْبًا", "شَيْبًا", ("role", "تمييز")),
    # the doer is raf' and the object nasb: a damma the parser made the object is the doer
    ("أَحَبَّ زَيْدٌ عَمْرًا", "زَيْدٌ", ("role", "فاعل")),
    ("أَحَبَّ زَيْدٌ عَمْرًا", "عَمْرًا", ("role", "مفعول به")),
    # إنّ takes no object; a sound feminine plural's kasra, tanween or none, is its nasb
    ("إِنَّ فِي ذَلِكَ لَآيَاتٍ", "لَآيَاتٍ", ("role", "اسم إن")),
    ("إِنَّ فِي ذَلِكَ لَآيَاتٍ", "لَآيَاتٍ", ("sign", "كسرة، نيابة عن الفتحة، جمع مؤنث سالم")),
    # a noun puts nothing in nasb: the verb said of the مبتدأ is the عامل, its doer the pronoun back
    ("زَيْدٌ أَكْرَمَ ضَيْفًا", "أَكْرَمَ", ("role", "فعل")),
    ("زَيْدٌ أَكْرَمَ ضَيْفًا", "ضَيْفًا", ("role", "مفعول به")),
    ("زيد نصر بكرا", "بكرا", ("role", "مفعول به")),
    # a pronoun opening the line is a noun like زيد: its verb is past, its منصوب the object
    ("هُوَ أَكْرَمَ ضَيْفًا", "أَكْرَمَ", ("role", "فعل")),
    ("هُوَ أَكْرَمَ ضَيْفًا", "ضَيْفًا", ("role", "مفعول به")),
    ("هي كتبت الدرس", "الدرس", ("role", "مفعول به")),
    ("هذا نصر بكرا", "بكرا", ("role", "مفعول به")),  # a demonstrative is a pronoun-noun too
    # nearest case: after a مضاف the fatha is a diptote's jarr, no منصوب wanting a verb
    ("هَذَا كِتَابُ أَحْمَدَ بْنِ حَنْبَلٍ", "أَحْمَدَ", ("role", "مضاف إليه")),
    # nearest case: a typed damma keeps the elative, its منصوب the تمييز
    ("هُوَ أَكْرَمُ ضَيْفًا", "أَكْرَمُ", ("role", "خبر")),
    ("هُوَ أَكْرَمُ ضَيْفًا", "ضَيْفًا", ("role", "تمييز")),
    ("زَيْدٌ جَاءَ رَاكِبًا", "رَاكِبًا", ("role", "حال")),
    ("زَيْدٌ طَابَ نَفْسًا", "نَفْسًا", ("role", "تمييز")),
    # an opening مَنْ hung loose on its verb: the hidden هو goes back to it, the مبتدأ; a verb
    # with a doer of its own takes it as its fronted object
    ("مَنْ أَكْرَمَ ضَيْفًا", "مَنْ", ("role", "مبتدأ")),
    ("مَنْ أَكْرَمْتَ", "مَنْ", ("role", "مفعول به")),
    ("مَنْ نَصَرَ بَكْرًا", "مَنْ", ("role", "مبتدأ")),
    ("مَنْ نَصَرَ بَكْرًا", "بَكْرًا", ("role", "مفعول به")),
    # nearest case: a raf' word مَنْ hangs on answers the condition, it is not the verb's
    ("مَنْ أَكْرَمَ ضَيْفَهُ فَهُوَ كَرِيمٌ", "كَرِيمٌ", ("role", "خبر")),
    # a command's doer is the hidden أنت, so the raf' word after قُلْ heads the sentence it says
    ("قُلْ هُوَ اللَّهُ أَحَدٌ", "هُوَ", ("role", "مبتدأ")),
    ("قُلْ هُوَ اللَّهُ أَحَدٌ", "اللَّهُ", ("role", "خبر")),
    ("قُلْ هُوَ اللَّهُ أَحَدٌ", "أَحَدٌ", ("role", "خبر")),
    ("قُلِ الْحَقُّ مِنْ رَبِّكُمْ", "الْحَقُّ", ("role", "مبتدأ")),
    # nearest case: a raf' pronoun of the verb's own person repeats its doer
    ("ذَهَبْتُ أَنَا", "أَنَا", ("role", "توكيد")),
    ("قُمْ أَنْتَ", "أَنْتَ", ("role", "توكيد")),
    # a word typed in jarr with no جار is the مضاف إليه of the bare noun before it, never a khabar
    ("زَيْدٌ أَكْرَمُ رِجَالٍ", "أَكْرَمُ", ("role", "خبر")),
    ("زَيْدٌ أَكْرَمُ رِجَالٍ", "رِجَالٍ", ("role", "مضاف إليه")),
    # nearest case: a name is added to nothing, so the word after it is its صفة
    ("بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ", "الرَّحْمَنِ", ("role", "صفة")),
    # the word itself is that verb only by a typed fatha: أَبُوهُ's و is the raf' of the five nouns
    ("اَلتِّلْمِيذُ أَبُوهُ مُعَلِّمٌ", "أَبُوهُ", ("role", "مبتدأ")),
])
def test_sentence_check_fixes(sentence, word, want):
    from tests.nahw_helpers import cards
    card = next(w for w in cards(sentence) if w["word"] == word)
    assert card.get(want[0]) == want[1]



def test_a_definite_noun_on_an_elative_is_no_tamyeez():
    """التمييز لا يكون إلا نكرة (Ibn Yaʿish, Sharh al-Mufassal): النَّاسَ written in nasb stays off it."""
    from backend.services.nahw import iraab
    card = next(w for w in iraab.analyze("هُوَ أَكْرَمُ النَّاسَ")["words"] if w["word"] == "النَّاسَ")
    assert card.get("role") != "تمييز"

@pytest.mark.parametrize("hung", [{}, {4: (2, "MOD")}, {4: (2, "MOD"), 2: (1, "SBJ")}, {2: (1, "SBJ"), 3: (4, "TPC")}])
def test_zanna_pair_whatever_tree_the_parser_gives(hung):
    """ظنّ's two objects come out the same however the parser hung the old مبتدأ and خبر:
    machines differ in the tree they read (CI hung قصيرا on الرجل)."""
    from backend.services.sarf import morphology
    from backend.services.nahw import syntax
    from backend.services.nahw.syntax import catib_onnx
    from backend.services.nahw.syntax.naming import roles
    from backend.services.nahw.syntax.repair import correct
    words = "حَسِبَ الرَّجُلُ الطَّرِيقَ قَصِيرًا".split()
    tokens = catib_onnx.parse(words, morphology.pick(words, syntax.disambiguator()))
    for word_id, (head, rel) in hung.items():
        tokens[word_id - 1]["head"], tokens[word_id - 1]["rel"] = head, rel
    correct(words, tokens)
    assert [r.get("role") for r in roles(words, tokens)] == ["فعل", "فاعل", "مفعول به", "مفعول به"]
