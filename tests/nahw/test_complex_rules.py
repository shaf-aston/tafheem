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
