"""The rules the complex set (backend/data/nahw_rules/complex_sentences.json, labelled blind)
exposed, each held by its sentence and by a sibling the same rule must leave alone: a fix
for one construction that also bent the other would fail here."""
import pytest

from tests.nahw_helpers import analyze, cards, needs_parser


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
