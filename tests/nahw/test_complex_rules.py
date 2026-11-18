"""The rules the complex set (backend/data/nahw_rules/complex_sentences.json, labelled blind)
exposed, each held by its sentence and by a sibling the same rule must leave alone: a fix
for one construction that also bent the other would fail here."""
import re

import pytest

from tests.nahw_helpers import analyze, cards, needs_parser, tree_roles


def card(sentence: str, word: str) -> dict:
    return next(c for c in cards(sentence) if c["word"] == word)


def units(sentence: str) -> list[tuple]:
    """(job, label) of every labelled unit in the picture, outermost first."""
    found = []

    def walk(node):
        if node.get("label"):
            found.append((node.get("role"), node["label"]))
        for child in node.get("children", []):
            walk(child)
    walk(analyze(sentence)["tree"]["tree"])
    return found


# A governor joined to و/ف (فلم، ولن) still governs the verb after it: يجزم ويَنصب.
@needs_parser
@pytest.mark.parametrize("sentence, word, case", [
    ("كَمْ مِنْ كِتَابٍ قَرَأْتُهُ فَلَمْ أَفْهَمْ مِنْهُ شَيْئًا", "أَفْهَمْ", "jazm"),
    ("وَلَنْ يَذْهَبَ", "يَذْهَبَ", "nasb"),
])
def test_a_governor_behind_a_joined_letter_still_governs(sentence, word, case):
    assert card(sentence, word)["case"] == case


# After لم only a verb can come, so أفهم there is no elative before مِن; with nothing
# governing it (هو أفهمُ منه) it stays the أفعل التفضيل خبر.
@needs_parser
@pytest.mark.parametrize("sentence, word, role", [
    ("لَمْ أَفْهَمْ مِنْهُ شَيْئًا", "أَفْهَمْ", "فعل"),
    ("هُوَ أَفْهَمُ مِنْهُ", "أَفْهَمُ", "خبر"),
    ("زَيْدٌ أَعْلَمُ مِنْ عَمْرٍو", "أَعْلَمُ", "خبر"),
])
def test_only_a_verb_follows_a_jazm_particle(sentence, word, role):
    assert card(sentence, word)["role"] == role


# مِنْ the preposition is no مَنْ of a condition, though both sit on the jazm family's word list.
@needs_parser
def test_min_the_preposition_is_not_a_jazm_word():
    said = card("لَمْ أَفْهَمْ مِنْهُ شَيْئًا", "مِنْهُ")
    assert said["role"] == "حرف جر" and "جزم" not in said["reason"]
    assert card("مَنْ يَدْرُسْ يَنْجَحْ", "مَنْ")["reason"].startswith("اسم شرط جازم")


# A counted number is the thing given (مفعول به); a number repeated for the manner (ثلاثةً ثلاثةً) is حال.
@needs_parser
def test_a_counted_number_is_an_object_not_a_haal():
    assert card("اشْتَرَى أَبِي عِشْرِينَ كِتَابًا وَأَهْدَى أَخِي الصَّغِيرَ خَمْسَةً مِنْهَا", "خَمْسَةً")["role"] == "مفعول به"
    assert cards("جَاءَ الطُّلَّابُ ثَلَاثَةً ثَلَاثَةً")[2]["role"] == "حال"


# A masdar of the heart giving the reason (خوفًا) is مفعول لأجله, never a second object; a
# verb of تصيير (ترك) does take two.
@needs_parser
def test_a_reason_masdar_is_not_a_second_object():
    assert card("يَا طَالِبَ الْعِلْمِ لَا تَتْرُكْ مُرَاجَعَةَ دُرُوسِكَ خَوْفًا مِنَ التَّعَبِ", "خَوْفًا")["role"] == "مفعول لأجله"
    assert [c["role"] for c in cards("تَرَكْتُ الْبَابَ مَفْتُوحًا")][1:] == ["مفعول به", "مفعول به"]


# A participle with تنوين/ين works like its verb: the ـات after it is its object, kasra in place of
# fatha; one in إضافة to it (مكرمُ الطالباتِ) is مضاف إليه.
@needs_parser
def test_a_working_participle_takes_an_at_plural_object():
    said = card("عَادَ الْجُنُودُ مِنَ الْمَعْرَكَةِ مُنْتَصِرِينَ رَافِعِينَ رَايَاتِهِمْ", "رَايَاتِهِمْ")
    assert (said["role"], said["sign"]) == ("مفعول به", "كسرة، نيابة عن الفتحة، جمع مؤنث سالم")
    assert card("زَيْدٌ مُكْرِمُ الطَّالِبَاتِ", "الطَّالِبَاتِ")["role"] == "مضاف إليه"


# A pronoun written onto أنّ is its اسم, so a verb after it (أنّنا اجتهدنا) is the khabar: the word
# is still the ناسخ, never أنْ that puts a verb in nasb.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("أَعْلَمُ أَنَّنَا اجْتَهَدْنَا", "أَنَّنَا", "حرف ناسخ مشبه بالفعل"),
    ("كَادَ الْقِطَارُ يَفُوتُنَا لَوْلَا أَنَّنَا أَسْرَعْنَا", "أَنَّنَا", "حرف ناسخ مشبه بالفعل"),
    ("أُرِيدُ أَنْ أَذْهَبَ", "أَنْ", "حرف نصب"),
])
def test_a_pronoun_on_anna_is_its_ism(sentence, word, said):
    assert card(sentence, word)["reason"].startswith(said)


# A masdar (مُفاعَلة too) is no participle: its إضافة is معنوية, and it can be مفعول مطلق.
@needs_parser
def test_a_masdar_is_no_participle():
    assert "معنوية" in card("لَا تَتْرُكْ مُرَاجَعَةَ دُرُوسِكَ", "دُرُوسِكَ")["reason"]
    assert card("قَاتَلُوا مُقَاتَلَةً شَدِيدَةً", "مُقَاتَلَةً")["role"] == "مفعول مطلق"


# a participle at work governs its own masdar as its verb does (Alfiyya: بمثله أو فعل أو وصف نصب); another noun after it
# is its object, a describing word its state
@needs_parser
@pytest.mark.parametrize("sentence, word, role", [
    ("زَيْدٌ ضَارِبٌ ضَرْبًا شَدِيدًا", "ضَرْبًا", "مفعول مطلق"),
    ("الطَّالِبُ مُجْتَهِدٌ اجْتِهَادًا", "اجْتِهَادًا", "مفعول مطلق"),
    ("زَيْدٌ ضَارِبٌ بَكْرًا", "بَكْرًا", "مفعول به"),
    ("زَيْدٌ قَادِمٌ مُسْرِعًا", "مُسْرِعًا", "حال"),
    # كِتَاب، لِبَاس: the thing written or worn, of one root with the participle but no masdar of it
    ("أَنْتَ كَاتِبٌ كِتَابًا جَمِيلًا", "كِتَابًا", "مفعول به"),
    ("زَيْدٌ لَابِسٌ لِبَاسًا جَمِيلًا", "لِبَاسًا", "مفعول به"),
    ("كَتَبَ الطَّالِبُ كِتَابًا مُفِيدًا", "كِتَابًا", "مفعول به"),
])
def test_a_participles_own_masdar_is_its_mafool_mutlaq(sentence, word, role):
    assert card(sentence, word)["role"] == role


# اسم لا: a single noun or dual is built on what its nasb would show, in the place of nasb;
# a مضاف (لا طالبَ علمٍ) stays معرب منصوب. The card's sign and its reason say the same.
@needs_parser
@pytest.mark.parametrize("sentence, word, sign, said", [
    ("لَا رَجُلَ فِي الدَّارِ", "رَجُلَ", "مبني على الفتح في محل نصب", "مبني في محل نصب لأنه اسم لا"),
    ("لَا قَلَمَيْنِ عِنْدِي", "قَلَمَيْنِ", "مبني على الياء في محل نصب", "مبني في محل نصب لأنه اسم لا"),
    ("لَا طَالِبَ عِلْمٍ مُتَكَاسِلٌ فِي هَذَا الْفَصْلِ", "طَالِبَ", "فتحة", "منصوب لأنه اسم لا"),
])
def test_ism_la_is_built_unless_it_is_mudaf(sentence, word, sign, said):
    got = card(sentence, word)
    assert got["sign"] == sign and got["reason"].startswith(said)


# A raf' word after the اسم of لا/إنّ, where a صفة would be in nasb, is the khabar; a nasb one stays صفة.
@needs_parser
def test_a_raf_word_after_ism_la_is_its_khabar():
    assert card("لَا طَالِبَ عِلْمٍ مُتَكَاسِلٌ فِي هَذَا الْفَصْلِ", "مُتَكَاسِلٌ")["role"] == "خبر لا"
    assert card("لَا رَجُلَ ظَرِيفًا فِي الدَّارِ", "ظَرِيفًا")["role"] == "صفة"


# A جار ومجرور hangs on a verb or what carries its sense, never on إنّ or لا: on a وصف khabar
# when there is one, else it is the khabar itself (متعلق بمحذوف تقديره ثابت).
@needs_parser
@pytest.mark.parametrize("sentence, label", [
    ("لَا طَالِبَ عِلْمٍ مُتَكَاسِلٌ فِي هَذَا الْفَصْلِ", "متعلق بـمُتَكَاسِلٌ"),
    ("إِنَّ الطَّالِبَ مُجْتَهِدٌ فِي دُرُوسِهِ", "متعلق بـمُجْتَهِدٌ"),
    ("لَا رَجُلَ فِي الدَّارِ", "متعلق بـثابت"),
    ("إِنَّ زَيْدًا فِي الدَّارِ", "متعلق بـثابت"),
])
def test_a_jar_hangs_on_the_khabar_not_the_particle(sentence, label):
    assert label in [name for _, name in units(sentence)]


# أنّ with its pair is one مصدر مؤول, which takes the job of its place: مفعول به after علم, مبتدأ after لولا.
@needs_parser
@pytest.mark.parametrize("sentence, job", [
    ("عَلِمْتُ أَنَّكَ نَاجِحٌ", "مفعول به"),
    ("كَادَ الْقِطَارُ يَفُوتُنَا لَوْلَا أَنَّنَا أَسْرَعْنَا", "مبتدأ"),
    ("أُرِيدُ أَنْ أَذْهَبَ", "مفعول به"),
])
def test_anna_and_its_pair_are_one_masdar(sentence, job):
    assert (job, "مَصْدَرٌ مُؤَوَّلٌ") in units(sentence)


# ياء المتكلم on a noun takes the kasra, so the case cannot show, whether CAMeL names it 1s_poss (كتابي) or 1s_pron
# (عندي, a ظرف); another pronoun leaves the vowel shown (عندكَ), and on a verb it is an object (أكرمني).
@needs_parser
@pytest.mark.parametrize("sentence, word, sign", [
    ("عِنْدِي كِتَابٌ", "عِنْدِي", "فتحة مقدرة على ما قبل ياء المتكلم"),
    ("كِتَابِي جَدِيدٌ", "كِتَابِي", "ضمة مقدرة على ما قبل ياء المتكلم"),
    ("جَلَسْتُ عِنْدَكَ", "عِنْدَكَ", "فتحة"),
    ("أَكْرَمَنِي زَيْدٌ", "أَكْرَمَنِي", "مبني على الفتح"),
])
def test_ya_of_the_speaker_hides_the_case(sentence, word, sign):
    assert card(sentence, word)["sign"] == sign


def _pronoun_said(sentence: str, word: str) -> str:
    return re.search("«([^»]+)» ضمير", card(sentence, word)["reason"]).group(1)


# The pronoun is named by the letters the word ends with: ي on a noun or particle (عندي، معي), ني on a verb, whose
# ن is نون الوقاية (أكرمني). Only the name changes: the parser still reads the pieces as it was trained on them, so
# بَعْدِي stays the ظرف of its verb, not a بدل of the word before it.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("عِنْدِي كِتَابٌ", "عِنْدِي", "ي"),
    ("مَعِي قَلَمٌ", "مَعِي", "ي"),
    ("أَكْرَمَنِي زَيْدٌ", "أَكْرَمَنِي", "ني"),
])
def test_a_pronoun_is_named_by_its_written_letters(sentence, word, said):
    assert _pronoun_said(sentence, word) == said


@needs_parser
def test_the_written_name_leaves_the_parse_alone():
    assert card("لَا تَتَّخِذُوهُمْ غَرَضًا بَعْدِي فَمَنْ أَحَبَّهُمْ", "بَعْدِي")["role"] == "مفعول فيه"


def _parts(sentence: str, at: int) -> list:
    """The roles of the pieces the picture draws inside word `at` (its verb, its doer, its object)."""
    def find(node):
        if node.get("word") == at:
            return node
        return next(filter(None, map(find, node.get("children", []))), None)
    return [p["role"] for p in find(analyze(sentence)["tree"]["tree"]).get("parts", [])]


# يَفُوتُنَا, filed whole as one verb, still has its object written onto it: the card and the tree name «نا» مفعول به;
# the verb with nothing written on it has no object.
@needs_parser
@pytest.mark.parametrize("sentence, has_object", [
    ("كَادَ الْقِطَارُ يَفُوتُنَا", True),
    ("كَادَ الْقِطَارُ يَفُوتُ", False),
])
def test_an_object_written_on_a_whole_verb(sentence, has_object):
    assert ("مفعول به" in _parts(sentence, 2)) == has_object


# No verb puts the word after it in jarr, only a preposition or a مضاف does (Ibn Aqil V1 p15: بالجر), so قَاضِي before
# a noun in jarr is the noun, never the command to a woman its letters also spell; before an object in nasb it is that
# command, and a feminine plural's kasra is its nasb.
@needs_parser
@pytest.mark.parametrize("sentence, word, role", [
    ("جَاءَ قَاضِي الْمَدِينَةِ", "قَاضِي", "فاعل"),
    ("قَاضِي الْخَصْمَ", "قَاضِي", "فعل"),
    ("اُذْكُرِي الصَّالِحَاتِ", "اُذْكُرِي", "فعل"),
    ("يَا هِنْدُ زُورِي الْجَارَاتِ", "زُورِي", "فعل"),
])
def test_a_mudaf_is_no_command(sentence, word, role):
    assert card(sentence, word)["role"] == role


# لَوْلَاكَ: لولا opens on a noun, and a pronoun written on it stands in that noun's place, the مبتدأ whose khabar is
# left out (al-Akhfash's reading; Sibawayh has the pronoun in jarr by لولا), and the verb after is its answer; a
# pronoun written on لعلّ is its اسم.
@needs_parser
@pytest.mark.parametrize("sentence, word, said, answer", [
    ("لَوْلَاكَ لَهَلَكْتُ", "لَوْلَاكَ", "«ك» ضمير متصل مبني في محل رفع مبتدأ", "لَهَلَكْتُ"),
    ("لَوْلَاهُ لَضَاعَ الْأَمْرُ", "لَوْلَاهُ", "«ه» ضمير متصل مبني في محل رفع مبتدأ", "لَضَاعَ"),
    ("لَعَلَّكَ نَاجِحٌ", "لَعَلَّكَ", None, None),
])
def test_a_pronoun_on_lawla_is_its_mubtada(sentence, word, said, answer):
    reason = card(sentence, word)["reason"]
    assert (said in reason) if said else "مبتدأ" not in reason
    assert answer is None or "جواب لولا" in card(sentence, answer)["reason"]


# بِرَافِعِي رَايَاتِهِمْ: a sound masculine plural drops its ن to be مضاف (Ibn Aqil V1 p62: نون المثنى والمجموع تحذف
# للإضافة), its ي still its sign; a singular whose own last letter is ي (قَاضِي) keeps its hidden kasra. Before a
# name that shows no jarr (صَدِيقِي سَامِر) nothing says إضافة, and the ي stays "my".
@needs_parser
@pytest.mark.parametrize("sentence, word, sign", [
    ("مَرَرْتُ بِرَافِعِي رَايَاتِهِمْ", "بِرَافِعِي", "الياء، جمع مذكر سالم"),
    ("جَاءَ مُعَلِّمُو الْمَدْرَسَةِ", "مُعَلِّمُو", "الواو، جمع مذكر سالم"),
    ("مَرَرْتُ بِقَاضِي الْمَدِينَةِ", "بِقَاضِي", "كسرة مقدرة على الياء للثقل"),
    ("هَذَا صَدِيقِي سَامِر", "صَدِيقِي", "فتحة مقدرة على ما قبل ياء المتكلم"),
])
def test_a_plural_loses_its_nun_to_be_mudaf(sentence, word, sign):
    assert card(sentence, word)["sign"] == sign


# The two a sister of إنّ or كان governs are called after that sister, not the family's mother: a word (اسم ليت), a
# pronoun written onto it (كَأَنَّهُ: «ه» اسم كأن) and a clause that is its khabar (يَنْزِلُ: خبر ليت), on the card and in
# the tree alike; under the mother itself (إِنَّهُ) the name stays اسم إن.
@needs_parser
@pytest.mark.parametrize("sentence, word, said, drawn", [
    ("كَأَنَّهُ أَسَدٌ", "كَأَنَّهُ", "في محل نصب اسم كأن", ["اسم كأن", "خبر كأن"]),
    ("عَلِمْتُ أَنَّكَ نَاجِحٌ", "أَنَّكَ", "في محل نصب اسم أن", ["اسم أن", "خبر أن"]),
    ("لَيْتَ الْمَطَرَ يَنْزِلُ", "الْمَطَرَ", "لأنه اسم ليت", ["اسم ليت", "خبر ليت"]),
    ("إِنَّهُ كَرِيمٌ", "إِنَّهُ", "في محل نصب اسم إن", ["اسم إن", "خبر إن"]),
])
def test_a_sister_lends_its_name_to_what_it_governs(sentence, word, said, drawn):
    roles = tree_roles(analyze(sentence)["tree"]["tree"])
    assert said in card(sentence, word)["reason"] and all(name in roles for name in drawn)


@pytest.mark.parametrize("named, mother", [("خبر لعل", "خبر إن"), ("اسم كأن", "اسم إن"), ("خبر ليس", "خبر كان"), ("اسم عسى", "اسم كاد")])
def test_a_sisters_name_keeps_its_mothers_colour(named, mother):
    from backend.services.nahw.syntax.naming import role_key, tone
    assert (tone(named), role_key(named)) == (tone(mother), role_key(mother)) != (None, None)
    assert tone("حرف لعل") is None  # only a job the mother names: no such role, no colour


# كلا وكلتا (Ibn Aqil V1 p55: وكلا إذا بمضمر مضافا وصلا): joined to a pronoun ملحق بالمثنى, its letters the sign; joined
# to a noun like the مقصور, its vowel assumed on the alif; a true dual keeps its own sign.
@needs_parser
@pytest.mark.parametrize("sentence, word, sign", [
    ("رَأَيْتُ الرَّجُلَيْنِ كِلَيْهِمَا", "كِلَيْهِمَا", "الياء، ملحق بالمثنى"),
    ("جَاءَ الرَّجُلَانِ كِلَاهُمَا", "كِلَاهُمَا", "الألف، ملحق بالمثنى"),
    ("جَاءَ كِلَا الرَّجُلَيْنِ", "كِلَا", "ضمة مقدرة على الألف للتعذر"),
    ("مَرَرْتُ بِكِلْتَا الْمَرْأَتَيْنِ", "بِكِلْتَا", "كسرة مقدرة على الألف للتعذر"),
    ("جَاءَ الرَّجُلَانِ كِلَاهُمَا", "الرَّجُلَانِ", "الألف، مثنى"),
])
def test_kila_is_a_dual_only_by_its_pronoun(sentence, word, sign):
    assert card(sentence, word)["sign"] == sign


# تُحِبُّكَ opens on a damma with a kasra inside, like فُعِلَ, but the shadda after the kasra is the present's
# doubled root (أَحَبَّ يُحِبُّ): never the past تَحَبَّكَ the passive shape once picked; a true فُعِلَ stays past
@needs_parser
@pytest.mark.parametrize("sentence, word, aspect", [
    ("هِنْدٌ تُحِبُّكَ", "تُحِبُّكَ", "i"),
    ("ضُرِبَ زَيْدٌ", "ضُرِبَ", "p"),
])
def test_a_present_with_a_kasra_inside_is_no_past_passive(sentence, word, aspect):
    assert card(sentence, word)["aspect"] == aspect


# a verb whose doer is a clause (أَنْ تَصْدُقَ، المصدر المؤول) hides no هو; with no doer after it, it does
@needs_parser
@pytest.mark.parametrize("sentence, hidden", [
    ("أَعْجَبَنِي أَنْ تَصْدُقَ", False),
    ("زَيْدٌ أَعْجَبَنِي", True),
])
def test_a_clause_doer_leaves_no_hidden_one(sentence, hidden):
    assert ("ضمير مستتر" in card(sentence, "أَعْجَبَنِي")["reason"]) is hidden


# a هي must go back to a noun said before it (ضمير الغائب لا بد له من مرجع متقدم): with none, the ت is أنتَ
@needs_parser
@pytest.mark.parametrize("sentence, word, doer", [
    ("إِنْ تَزُرْنَا نُكْرِمْكَ", "تَزُرْنَا", "أنتَ"),
    ("أَعْجَبَنِي أَنْ تَصْدُقَ", "تَصْدُقَ", "أنتَ"),
    ("رَأَيْتُهَا تَكْتُبُ", "تَكْتُبُ", "أنتَ أو هي"),  # ـها before it: either
    ("قَالَتْ هِنْدٌ إِنَّهَا تُحِبُّ الْعِلْمَ", "تُحِبُّ", "هي"),
    ("هِنْدٌ تَصْدُقُ", "تَصْدُقُ", "هي"),
])
def test_ta_is_she_only_with_someone_to_go_back_to(sentence, word, doer):
    assert re.search(rf"تقديره {doer}[.،]", card(sentence, word)["reason"])


# a masdar hung on a passive verb is its نائب فاعل only when the verb has no deputy of its own: أُمِرْتُ's تُ is it
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("أُمِرْتُ أَنْ أَكُونَ صَادِقًا", "أُمِرْتُ", "ونائب فاعله ضمير متصل (أنا)"),
    ("غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ", "مَا", "لأنه نائب فاعل"),
])
def test_a_masdar_is_the_deputy_only_with_none_on_the_verb(sentence, word, said):
    assert said in card(sentence, word)["reason"]


# the بدل after إلا in a denied whole sentence is بدل بعض من كل, pronoun or none: the one excepted is a part of
# those it is taken out of; away from إلا a pronoun on a non-part still makes it اشتمال, none makes it كل من كل
@needs_parser
@pytest.mark.parametrize("sentence, word, kind", [
    ("مَا رَأَيْتُ أَحَدًا فِي الْمَسْجِدِ إِلَّا إِمَامَهُ", "إِمَامَهُ", "بدل بعض من كل"),
    ("مَا قَامَ أَحَدٌ إِلَّا زَيْدٌ", "زَيْدٌ", "بدل بعض من كل"),
    ("أَعْجَبَنِي الْمُعَلِّمُ عِلْمُهُ", "عِلْمُهُ", "بدل اشتمال"),
    ("جَاءَ أَخُوكَ زَيْدٌ", "زَيْدٌ", "بدل كل من كل"),
])
def test_the_badal_after_illa_is_a_part(sentence, word, kind):
    assert card(sentence, word)["reason"].endswith(kind)


# لولا + المصدر المؤول: the masdar is the مبتدأ and its خبر موجود is left out as after any noun; with no answer
# written after it, the answer is left out too, told by the sentence before (جواب لولا محذوف دلّ عليه ما قبله)
@needs_parser
@pytest.mark.parametrize("sentence, khabar, unsaid", [
    ("كَادَ الْقِطَارُ يَفُوتُنَا لَوْلَا أَنَّنَا أَسْرَعْنَا", True, True),
    ("لَوْلَا أَنَّكَ صَدِيقِي لَعَاقَبْتُكَ", True, False),
    ("لَوْلَا زَيْدٌ لَأَتَيْتُكَ", True, False),
])
def test_lawla_leaves_out_its_khabar_and_an_answer_said_before(sentence, khabar, unsaid):
    tree = analyze(sentence)["tree"]["tree"]
    roles = tree_roles(tree)
    assert ("خبر" in roles) is khabar
    assert ("دلّ عليه ما قبله" in tree_roles(tree, "detail")) is unsaid
    assert roles.count("جواب لولا") == 1
    assert [label for _, label in units(sentence)].count("جُمْلَةٌ شَرْطِيَّةٌ") == 1  # one condition, the خبر inside it


# مِن after كم brings what it counts: the jar-majroor is its تمييز, hung on no word, and the verb after it is
# said of كم as after كَمْ كِتَابًا: its خبر when it holds its own object back to كم, else كم is its object
@needs_parser
@pytest.mark.parametrize("sentence, said", [
    ("كَمْ مِنْ كِتَابٍ قَرَأْتُهُ فَلَمْ أَفْهَمْ مِنْهُ شَيْئًا", [("مبتدأ", None), ("تمييز", "جَارٌّ وَمَجْرُوْرٌ"), ("خبر", "جُمْلَةٌ فِعْلِيَّةٌ")]),
    ("كَمْ مِنْ رَجُلٍ جَاءَ", [("مبتدأ", None), ("تمييز", "جَارٌّ وَمَجْرُوْرٌ"), ("خبر", "جُمْلَةٌ فِعْلِيَّةٌ")]),
    ("كَمْ مِنْ كِتَابٍ قَرَأْتُ", [("مفعول به", None), ("تمييز", "جَارٌّ وَمَجْرُوْرٌ")]),
    ("كَمْ كِتَابًا قَرَأْتَهُ", [("مبتدأ", None), ("تمييز", None), ("خبر", "جُمْلَةٌ فِعْلِيَّةٌ")]),
])
def test_min_after_kam_brings_its_tamyeez(sentence, said):
    tree = analyze(sentence)["tree"]["tree"]
    top = [(kid.get("role"), kid.get("label") or None) for kid in tree["children"]]
    if top and top[0][0] == "مفعول به":  # كم the object: it and its تمييز are one unit
        top = [top[0]] + [(kid.get("role"), kid.get("label") or None) for kid in tree["children"][0]["children"][1:]]
    assert [pair for pair in top if pair[0] in {"مبتدأ", "مفعول به", "تمييز", "خبر"}] == said
    assert "متعلق بـكَمْ" not in tree_roles(tree, "label")


# a jar-majroor or ظرف between a known subject and its وصف khabar hangs on that khabar (ظرف لغو), not on an
# unwritten ثابت said as the subject's حال; with no such khabar, or after an unknown subject (its صفة), ثابت stays
@needs_parser
@pytest.mark.parametrize("sentence, invented", [
    ("أَصْبَحَ الْجَوُّ بَعْدَ الْمَطَرِ لَطِيفًا نَسِيمُهُ", False),
    ("زَيْدٌ فِي الدَّارِ جَالِسٌ", False),
    ("إِنَّ زَيْدًا فِي الدَّارِ جَالِسٌ", False),
    ("زَيْدٌ فِي الدَّارِ", True),
    ("كَانَ رَجُلٌ مِنَ الْأَنْصَارِ صَالِحًا", True),
])
def test_a_jar_before_a_describing_khabar_hangs_on_it(sentence, invented):
    assert ("متعلق بـثابت" in tree_roles(analyze(sentence)["tree"]["tree"], "label")) is invented


# a subject that does a verb's work itself, a masdar or a participle, is what the jar after it hangs on, not the khabar
@needs_parser
@pytest.mark.parametrize("sentence, label", [
    ("السَّفَرُ إِلَى مَكَّةَ مُمْتِعٌ", "متعلق بـالسَّفَرُ"),
    ("الْجَالِسُ فِي الدَّارِ مَسْرُورٌ", "متعلق بـالْجَالِسُ"),
    ("زَيْدٌ فِي الدَّارِ جَالِسٌ", "متعلق بـجَالِسٌ"),
    # a فِعَال plural or a جامد noun is no masdar: the jar after it hangs on the khabar
    ("الرِّجَالُ فِي الدَّارِ", "متعلق بـثابت"),
    ("الرِّجَالُ فِي الْمَسْجِدِ كَثِيرُونَ", "متعلق بـكَثِيرُونَ"),
    ("الْجِبَالُ فِي الْيَمَنِ عَالِيَةٌ", "متعلق بـعَالِيَةٌ"),
])
def test_a_jar_after_a_working_subject_stays_on_it(sentence, label):
    assert label in tree_roles(analyze(sentence)["tree"]["tree"], "label")


# a ظرف is منصوب, so a time or place word in raf' (السَّاعَةُ) or with its case unseen (الْعُلْيَا) is no ظرف and
# stays the صفة of the noun before it, not hung on the khabar after it
@needs_parser
@pytest.mark.parametrize("sentence, word, role", [
    ("تِلْكَ السَّاعَةُ ثَمِينَةٌ", "السَّاعَةُ", "صفة"),
    ("الْيَدُ الْعُلْيَا الْمُنْفِقَةُ", "الْعُلْيَا", "صفة"),
])
def test_a_time_or_place_word_out_of_nasb_is_no_zarf(sentence, word, role):
    assert card(sentence, word)["role"] == role


# a sound feminine plural's kasra is also its nasb (Alfiyya: وما بتا وألف قد جمعا يكسر في الجر وفي النصب معا), so an
# indefinite ـات word after a definite noun, with or without its own object, is a حال; one agreeing with its noun stays its صفة;
# after a verb of giving, active or passive, it is the second object, as a fatha word would be
@needs_parser
@pytest.mark.parametrize("sentence, word, role", [
    ("رَأَيْتُ النِّسَاءَ حَامِلَاتٍ", "حَامِلَاتٍ", "حال"),
    ("رَأَيْتُ النِّسَاءَ حَامِلَاتٍ الْجِرَارَ", "حَامِلَاتٍ", "حال"),
    ("رَأَيْتُ الْمَرْأَةَ حَامِلَةً الْجَرَّةَ", "حَامِلَةً", "حال"),
    # after a jar too: a describing ـات word is the حال, a name after a noun with ال stays its بدل
    ("مَرَرْتُ بِالنِّسَاءِ حَامِلَاتٍ", "حَامِلَاتٍ", "حال"),
    ("مَرَرْتُ بِالْأَمِيرِ خَالِدٍ", "خَالِدٍ", "بدل"),
    ("مَرَرْتُ بِنِسَاءٍ مُسْلِمَاتٍ", "مُسْلِمَاتٍ", "صفة"),
    ("أَعْطَيْتُ الْفُقَرَاءَ صَدَقَاتٍ", "صَدَقَاتٍ", "مفعول به"),
    ("أُعْطِيَ الْفُقَرَاءُ صَدَقَاتٍ", "صَدَقَاتٍ", "مفعول به"),
])
def test_a_feminine_plurals_kasra_is_its_nasb_as_a_hal(sentence, word, role):
    found = card(sentence, word)
    assert found["role"] == role
    assert ("نيابة عن الفتحة" in (found["sign"] or "")) is (role not in ("صفة", "بدل") and "ات" in word)



# a ـات plural the dictionary lacks reads as its singular with ة (الجارة، مسرعة), so its kasra is still its nasb; a
# word whose singular is no word with ة (مَرْضَاة) is no such plural
@needs_parser
def test_an_unread_feminine_plural_reads_as_its_singular():
    from backend.services.nahw.syntax import catib_onnx
    from backend.services.sarf import morphology
    assert card("جَاءَتِ الْجَارَاتُ مُسْرِعَاتٍ", "مُسْرِعَاتٍ")["role"] == "حال"
    read = morphology.pick(["الْجَارَاتُ", "مُسْرِعَاتٍ", "مَرْضَاتِ"], catib_onnx.disambiguator())
    assert [(r.get("num"), r.get("cas")) for r in read[:2]] == [("p", "n"), ("p", "g")]
    assert read[2].get("num") != "p"


# a word with tanween is never a مضاف, so the noun in nasb straight after a working participle is its object, however
# the parser hung it; without tanween the noun after it is its مضاف إليه, and an indefinite state word stays a حال.
# A ـات kasra is a jarr too, so after a participle in jarr it is its نعت, not its object
@needs_parser
@pytest.mark.parametrize("sentence, word, role", [
    ("زَيْدٌ مُكْرِمٌ الطُّلَّابَ", "الطُّلَّابَ", "مفعول به"),
    ("زَيْدٌ مُكْرِمٌ الطَّالِبَاتِ", "الطَّالِبَاتِ", "مفعول به"),
    ("زَيْدٌ مُكْرِمُ الطَّالِبَاتِ", "الطَّالِبَاتِ", "مضاف إليه"),
    ("زَيْدٌ قَادِمٌ مُسْرِعًا", "مُسْرِعًا", "حال"),
    ("مَرَرْتُ بِرَجُلٍ مُكْرِمٍ الطَّالِبَاتِ", "الطَّالِبَاتِ", "مفعول به"),
    ("مَرَرْتُ بِنِسَاءٍ صَالِحَاتٍ مُؤْمِنَاتٍ", "مُؤْمِنَاتٍ", "صفة"),
    ("رَأَيْتُ طَالِبَاتٍ مُجْتَهِدَاتٍ مَاهِرَاتٍ", "مَاهِرَاتٍ", "صفة"),
])
def test_the_nasb_noun_after_a_tanween_participle_is_its_object(sentence, word, role):
    assert card(sentence, word)["role"] == role

# لمّا before a past verb opens a condition (حرف وجود لوجود), its answer جواب لمّا; before a present verb
# it is the jazm particle and opens none (لَمَّا يَذْهَبْ)
@needs_parser
@pytest.mark.parametrize("sentence, lamma, opens", [
    ("فَلَمَّا سَارُوا فِيهِ وَجَدُوهُ طَوِيلًا", "فَلَمَّا", True),
    ("لَمَّا جَاءَ زَيْدٌ أَكْرَمْتُهُ", "لَمَّا", True),
    ("لَمَّا يَذْهَبْ زَيْدٌ", "لَمَّا", False),
])
def test_lamma_before_a_past_verb_opens_a_condition(sentence, lamma, opens):
    roles = tree_roles(analyze(sentence)["tree"]["tree"])
    assert ("جواب لمّا" in roles) is opens
    assert [label for _, label in units(sentence)].count("جُمْلَةٌ شَرْطِيَّةٌ") == int(opens)
    assert ("حرف نفي وجزم وقلب" in card(sentence, lamma)["reason"]) is not opens


@needs_parser
def test_lamma_opens_no_condition_on_a_present_verb_whatever_its_ending():
    # the parser may read the verb in raf' (no jazm to show لمّا the particle): the tense alone says no condition
    assert "جُمْلَةٌ شَرْطِيَّةٌ" not in [label for _, label in units("لَمَّا يَكْتُبُ زَيْدٌ يَفْرَحُ")]


def drawn_roles(node: dict) -> list[str]:
    """Every role in the picture, the parts drawn inside a leaf too (the ه of وجدوه)."""
    return [r for r in [node.get("role"), *(part.get("role") for part in node.get("parts", []))] if r] + [
        r for kid in node.get("children", []) for r in drawn_roles(kid)]


# a verb of ظن or of giving: an object pronoun written onto it is nearer than any written word, so it is
# the first object and the written one the second; with no pronoun the written words go in their order
@needs_parser
@pytest.mark.parametrize("sentence, first, second", [
    ("وَجَدُوهُ طَوِيلًا", "وَجَدُوهُ", "طَوِيلًا"),
    ("أَعْطَيْتُهُ كِتَابًا", "أَعْطَيْتُهُ", "كِتَابًا"),
    ("ظَنَنْتُ الْمُعَلِّمَ حَاضِرًا", "الْمُعَلِّمَ", "حَاضِرًا"),
])
def test_the_pronoun_on_a_two_object_verb_is_its_first(sentence, first, second):
    assert card(sentence, first)["reason"].split(". القاعدة")[0].endswith("مفعول به أول")
    assert card(sentence, second)["reason"].split(". القاعدة")[0].endswith("مفعول به ثانٍ")
    roles = drawn_roles(analyze(sentence)["tree"]["tree"])
    assert roles.count("مفعول به أول") == roles.count("مفعول به ثانٍ") == 1


@needs_parser
def test_a_one_object_verb_keeps_its_plain_object():
    assert card("ضَرَبْتُهُ", "ضَرَبْتُهُ")["reason"].split(". القاعدة")[0].endswith("مفعول به")
    assert "مفعول به" in (roles := drawn_roles(analyze("ضَرَبْتُهُ")["tree"]["tree"])) and "مفعول به أول" not in roles


# من and ما serve every gender and number, so no noun takes them as its صفة but its بدل; hung on a noun with a past verb after it,
# ما is the span of that verb (ما المصدرية الظرفية: فاتقوا الله ما استطعتم). The relative stays where it fills a place.
@needs_parser
@pytest.mark.parametrize("sentence, at, role", [
    ("أَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ", 4, "حرف"),
    ("أَعْطَيْتُهُ مَا أَرَادَ", 1, "مفعول به"),
    ("أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ", 4, "مضاف إليه"),
    ("قَرَأْتُ الْكِتَابَ الَّذِي اشْتَرَيْتُهُ", 2, "صفة"),
    ("رَأَيْتُ الرَّجُلَ مَنْ أَكْرَمْتُهُ", 2, "بدل"),
    ("زُرْتُ صَدِيقِي مَنْ يُحِبُّنِي", 2, "بدل"),
    ("فَاتَّقُوا اللَّهَ مَا اسْتَطَعْتُمْ", 2, "حرف"),
    ("أَخَذْتُ مِنْهُ مَا أَعْطَانِي", 2, "مفعول به"),
    ("لَكُمُ الْخِيَارُ مَا دُمْتُمْ هُنَا", 2, "حرف"),
    ("فَرِحْتُ بِمَا قُلْتَ", 1, "مجرور"),
])
def test_ma_after_a_noun_is_no_sifa(sentence, at, role):
    assert [w["role"] for w in analyze(sentence)["words"]][at] == role


# a called noun takes no object, and a pronoun opening the sentence or the words after a call is the mubtada, so the
# noun after it is its khabar (اللهم أنت ربي، هو الحي); inside a sentence, after إلا, the noun after it is its بدل.
# The khabar of لا never stands before it, so a word hung on it from before is told of the noun before that word.
@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("اللَّهُمَّ أَنْتَ الْمَلِكُ", ["منادى", "مبتدأ", "خبر"]),
    ("اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ خَلَقْتَنِي", ["منادى", "مبتدأ", "خبر", "حرف", "اسم لا", "حرف", "بدل", "فعل"]),
    ("هُوَ الْحَيُّ لَا إِلَهَ إِلَّا هُوَ", ["مبتدأ", "خبر", "حرف", "اسم لا", "حرف", "بدل"]),
    ("اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ",
     ["منادى", "مبتدأ", "خبر", "حرف", "اسم لا", "حرف", "بدل", "فعل", "مبتدأ", "خبر", "مبتدأ", "حرف جر", "مجرور", "معطوف", "حرف", "فعل"]),
    ("يَا رَبِّ أَنْتَ الْكَرِيمُ", ["حرف", "منادى", "مبتدأ", "خبر"]),
    ("ذَلِكَ الْكِتَابُ لَا رَيْبَ فِيهِ", ["مبتدأ", "صفة", "حرف", "اسم لا", "حرف جر"]),
    ("اللَّهُمَّ إِنِّي أَسْأَلُكَ الْهُدَى", ["منادى", "حرف", "فعل", "مفعول به"]),
])
def test_the_words_after_a_call_and_before_la(sentence, roles):
    assert [w["role"] for w in analyze(sentence)["words"]] == roles


# a particle is told of nothing: ما with a mubtada hung on it is the noun, its khabar, though the verb after it
# carries a pronoun (its عائد); with no mubtada on it, before a verb with its object, ما negates
@needs_parser
@pytest.mark.parametrize("sentence, at, role", [
    ("الْخَيْرُ مَا اخْتَارَهُ اللَّهُ", 1, "خبر"),
    ("الْحَقُّ مَا شَهِدَتْ بِهِ الْأَعْدَاءُ", 1, "خبر"),
    ("مَا رَأَيْتُهُ", 0, "حرف"),
    ("الطَّالِبُ مَا فَهِمَ الدَّرْسَ", 1, "حرف"),
])
def test_ma_told_of_is_a_noun(sentence, at, role):
    assert [w["role"] for w in analyze(sentence)["words"]][at] == role


# ما is for what has no mind, so a person's name is told of by no relative ما: ما after it, before a verb holding the ه
# back to the name, negates, and the verb is the khabar, card and tree alike
@needs_parser
@pytest.mark.parametrize("sentence", ["زَيْدٌ مَا رَأَيْتُهُ", "مُحَمَّدٌ مَا كَتَبَهُ", "خَالِدٌ مَا عَرَفْتُهُ"])
def test_ma_after_a_name_negates(sentence):
    result = analyze(sentence)
    assert [w["role"] for w in result["words"]] == ["مبتدأ", "حرف", "فعل"]
    roles = drawn_roles(result["tree"]["tree"])
    assert "خبر" in roles and "اسم موصول" not in roles and "صلة" not in roles


# a verb has one doer (Tasheel 2.4.1): a relative the parser hung as a second doer straight after the first follows it,
# من and ما as its بدل; one the verb still owes as its object is that object, and a lone relative is the doer
@needs_parser
@pytest.mark.parametrize("sentence, at, role", [
    ("سَرَّنِي الطَّالِبُ مَنْ نَجَحَ", 2, "بدل"),
    ("جَاءَ الرَّجُلُ الَّذِي رَأَيْتُهُ", 2, "صفة"),
    ("قَرَأَ الطَّالِبُ مَا كَتَبَهُ", 2, "مفعول به"),
    ("أَعْجَبَنِي مَا قَرَأْتُهُ", 1, "فاعل"),
    # a حرف has no عائد: a ه on the verb after ما makes it the relative, the بدل of the noun it is hung on, no ظرفية
    ("أَعْجَبَنِي الْكِتَابُ مَا قَرَأْتُهُ", 2, "بدل"),
    ("سَرَّنِي الْخَبَرُ مَا سَمِعْتُهُ", 2, "بدل"),
    ("أَحْبَبْتُ الطَّعَامَ مَا طَبَخْتَهُ", 2, "بدل"),
])
def test_a_verb_has_one_doer(sentence, at, role):
    assert [w["role"] for w in analyze(sentence)["words"]][at] == role
