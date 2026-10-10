"""The rule engine's roles, and the name the word grid colours each one by.

The grid used to work out its colour by searching the role text for English
words ('fail', 'mafool') while this engine writes that text in Arabic. Nothing
ever matched, so every noun and verb the engine identified was drawn in the
default grey.

So these check the two halves of the seam that replaced it: every entry the
engine builds carries a `role_key`, and every key it uses is one the contract
allows, because a key that is not in `models/analyze.py ROLE_KEYS` is dropped at the
router and the colour is silently lost again.

Run: python -m pytest tests/test_rule_engine.py
"""
from __future__ import annotations

import pytest

from backend.models.analyze import ROLE_KEYS, WordAnalysis
from backend.services import iraab, morphology, rule_engine, syntax
from backend.services.arabic_text import words
from backend.services.nahw_book import term_ar
from backend.services.syntax.catib_onnx import files_present

# Reading a sentence needs CAMeL's data and the parser's model files, neither in git.
pytestmark = pytest.mark.skipif(
    not (morphology._CAMEL_AVAILABLE and files_present()),
    reason="CAMeL data or CATiB parser files not present",
)

# Two sentences, one of each kind, so both branches of the engine are walked.
VERBAL = "ذهب الولد إلى المدرسة"     # jumlah fi'liyyah
NOMINAL = "الكتاب جديد"              # jumlah ismiyyah


def analysed(sentence: str) -> list[dict]:
    """The cards as the page gets them: the rule engine names no job, the book's tree does."""
    return _read(sentence)["words"]


@pytest.mark.parametrize("sentence", [VERBAL, NOMINAL])
def test_every_word_carries_a_role_key_field(sentence: str):
    """Present on every entry, including the ones deliberately left uncoloured.

    Missing and None are different: None says "this role was not settled", which
    the grid draws in grey on purpose. A missing field is a builder that forgot,
    and would read as the same thing.
    """
    words = analysed(sentence)
    assert words, "the engine returned nothing to check"
    for word in words:
        assert "role_key" in word, word


@pytest.mark.parametrize("sentence", [VERBAL, NOMINAL])
def test_keys_are_ones_the_contract_allows(sentence: str):
    """The list here and the list in models/analyze.py are the same list.

    Anything else is dropped to None by `WordAnalysis.from_raw`, so a typo in a
    key would not fail, it would just quietly go grey, which is the exact bug
    this file exists to stop coming back.
    """
    for word in analysed(sentence):
        key = word["role_key"]
        assert key is None or key in ROLE_KEYS, f"{key!r} in {word}"


def test_a_verbal_sentence_colours_its_verb_and_its_doer():
    """Not just "a key is present", the two roles a reader looks for are named."""
    keys = {w["role_key"] for w in analysed(VERBAL)}
    assert "fil" in keys, "the verb was not named"
    assert "fail" in keys, "the doer was not named"


# ── The router's half of the seam ────────────────────────────────────────────

def test_a_role_key_the_grid_does_not_know_is_dropped():
    """An unknown name must become no colour, never a colour meaning another role."""
    word = WordAnalysis.from_raw({"word": "زيدٌ", "role": "فاعل", "role_key": "subject"})
    assert word.role_key is None
    assert word.role == "فاعل"


def test_a_role_key_the_grid_knows_survives():
    word = WordAnalysis.from_raw({"word": "زيدٌ", "role": "فاعل (مرفوع)", "role_key": "fail"})
    assert word.role_key == "fail"


def test_a_word_with_no_key_at_all_is_accepted_uncoloured():
    """A word the engine gave no role; not an error."""
    assert WordAnalysis.from_raw({"word": "زيدٌ"}).role_key is None


# A card's reason must explain the role the card wears, whoever named it.
REASON_SENTENCES = ["مَتَى سَافَرَ الرَّجُلُ", "كُتِبَ الدَّرْسُ", "جاء محمد وعلي", "يا محمد اجلس",
                    "إِنَّ الطَّالِبَ مُجْتَهِدٌ", "كَتَبَ الطَّالِبُ الدَّرْسَ فِي الْبَيْتِ"]


def test_every_role_has_a_reason():
    from backend.services.nahw_book import teacher_rules
    from backend.services.syntax.naming import ROLES
    assert [role for role in ROLES if role not in teacher_rules()["reasons"]] == []


@pytest.mark.parametrize("sentence", REASON_SENTENCES)
def test_each_reason_explains_its_own_role(sentence: str):
    words = iraab.analyze(sentence)["words"]
    for word in words:
        role = word["role"]
        if word["type"] == "punc" or role == "–":
            continue
        assert role in word["reason"] or (role == "فعل" and word["type"] == "fi'l"), (word["word"], role, word["reason"])


# The verb's card: a command by its typed shape, a present verb's case by its ending or the particle before it.
VERB_CARDS = [
    ("اُكْتُبْ الدَّرْسَ", 0, "mabni", "فعل أمر"),
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


@pytest.mark.parametrize("sentence, lemma", [("قُمْ يَا وَلَدُ", "قام"), ("اُكْتُبْ الدَّرْسَ", "كتب")])
def test_a_command_is_described_as_one(sentence: str, lemma: str):
    """Not the قَمَّ or أَكْتُبُ CAMeL misread it as: its notes and lemma are the command's."""
    from backend.services import morphology
    word = morphology.analyze_sentence(sentence)[0]
    assert (word["lemma"], word["features"].startswith("command"), "perfect" in word["features"]) == (lemma, True, False)


@pytest.mark.parametrize("sentence, verbal", [
    ("لَمْ يَكْتُبْ الطَّالِبُ", True), ("قَدْ نَجَحَ الطَّالِبُ", True), ("لَنْ يَذْهَبَ زَيْدٌ", True),
    ("إِنَّ الطَّالِبَ مُجْتَهِدٌ", False)])  # nearest case: a particle before a noun
def test_a_particle_before_the_verb_keeps_the_sentence_verbal(sentence: str, verbal: bool):
    summary = iraab.analyze(sentence)["summary"]
    assert (summary == term_ar("jumlah_filiyyah")) is verbal, summary


def _syntax_read(sentence: str) -> dict:
    return syntax.read(sentence, morphology.pick(words(sentence), syntax.disambiguator()))


def _read(sentence: str) -> dict:
    return iraab.analyze(sentence)


# One card field each, found by typing the sentence in (backend/scripts/analyze.py).
CARDS = [
    ("الدِّينُ النَّصِيحَةُ", 1, "role", "خبر"),           # nothing else is said of the mubtada
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


@pytest.mark.parametrize("sentence, index, wrong", [
    ("اِهْدِنَا الصِّرَاطَ", 0, "حذف النون"),
    ("هُوَ يَظُنُّ ذَلِكَ", 1, "مبني"),                       # a root's doubled nun is no nun of emphasis
])
def test_card_sign_is_not(sentence: str, index: int, wrong: str):
    assert wrong not in (_read(sentence)["words"][index]["sign"] or "")


@pytest.mark.parametrize("sentence, index, field, expected", CARDS)
def test_card_field(sentence: str, index: int, field: str, expected: str):
    word = _read(sentence)["words"][index]
    assert expected in (word[field] or ""), word


@pytest.mark.parametrize("sentence, term", [
    ("يَا عَبْدَ اللهِ", "jumlah_nidaiyyah"),
    ("الطُّلَّابُ يَدْرُسُونَ فِي المَكْتَبَةِ", "jumlah_ismiyyah"),  # a مبتدأ before the verb
    ("هَذَا البَيْتُ كَبِيرٌ", "jumlah_ismiyyah"),
    ("قُمْ يَا وَلَدُ", "jumlah_filiyyah"),  # nearest case: a command before the call
    ("إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا", "jumlah_shartiyyah"),
    ("إِنْ تَدْرُسْ تَنْجَحْ", "jumlah_shartiyyah"),
    ("مَتَى سَافَرَ الرَّجُلُ", "jumlah_istifhamiyyah")])  # a question, in the picture and above it
def test_summary_and_tree_name_the_sentence_alike(sentence: str, term: str):
    answer = _read(sentence)
    assert (answer["summary"], _syntax_read(sentence)["tree"]["tree"]["label"]) == (term_ar(term), term_ar(term))


def _picture_roles(node: dict) -> list:
    return [node.get("role"), node.get("detail"), *(r for kid in node.get("children", []) + node.get("parts", [])
                                                     for r in _picture_roles(kid))]


def test_an_action_after_illa_is_a_munqati_excepted_and_its_hidden_doer_is_said_either_way():
    shown = _picture_roles(_syntax_read("الصَّلَوَاتِ الْخَمْسَ إِلَّا أَنْ تَطَّوَّعَ شَيْئًا")["tree"]["tree"])
    assert "مستثنى منقطع" in shown and "ضمير مستتر تقديره أنتَ أو هي" in shown


def test_the_same_masdar_with_no_illa_stays_an_object():
    shown = _picture_roles(_syntax_read("أُرِيدُ أَنْ تَطَّوَّعَ")["tree"]["tree"])
    assert "مفعول به" in shown and "مستثنى منقطع" not in shown


def test_the_summary_is_the_pictures_own_label_never_a_second_guess():
    # a hadith whose word the parser misnamed اسم إن once printed "· إنّ" with no إنّ in it
    answer = _read("الظُّهْرَ وَالْعَصْرَ جَمِيعًا بِالْمَدِينَةِ فِي غَيْرِ خَوْفٍ وَلاَ سَفَرٍ")
    assert answer["summary"] == answer["tree"]["tree"]["label"] and "إنّ" not in answer["summary"]


def test_a_relative_and_its_silah_are_one_unit():
    """جاء الذي نجح: the الذي unit does the فاعل's job, made of the relative and its صلة."""
    doer = _syntax_read("جَاءَ الَّذِي نَجَحَ")["tree"]["tree"]["children"][1]
    inside = [(kid.get("role"), kid.get("label")) for kid in doer["children"]]
    assert (doer["role"], doer["label"], inside) == (
        "فاعل", term_ar("mawsool_silah"), [("اسم موصول", None), ("صلة", term_ar("jumlah_filiyyah"))])


def test_word_types_are_the_pages():
    """The types a card may carry are the ones grammar.json labels, and the rules use no other."""
    import json
    from pathlib import Path
    from backend.models.analyze import WORD_TYPES
    labelled = json.loads((Path(__file__).parent.parent / "frontend/src/grammar.json").read_text(encoding="utf-8"))["types"]
    assert WORD_TYPES - {"punc"} == set(labelled)
    for sentence in (VERBAL, NOMINAL, "جَاءَ الَّذِي نَجَحَ، هُوَ فِي البَيْتِ"):
        assert {w["type"] for w in _read(sentence)["words"]} <= WORD_TYPES
    assert WordAnalysis.from_raw({"word": "زيدٌ", "type": "noun"}).type is None


def test_the_glossary_explains_every_term_the_page_prints():
    """Every role a card can carry, every tarkeeb term and every label in the book's worked
    examples is in grammar.json, as an entry or named in one's meaning, so the glossary is never short."""
    import json
    from pathlib import Path
    from backend.services.arabic_text import strip_diacritics
    from backend.services.nahw_book import role_table
    from backend.services.syntax.naming import ROLES
    root = Path(__file__).parent.parent
    grammar = json.loads((root / "frontend/src/grammar.json").read_text(encoding="utf-8"))
    tarkeeb = json.loads((root / "backend/data/nahw_rules/tarkeeb.json").read_text(encoding="utf-8"))["terms"]
    entries = [*grammar["types"].values(), *grammar["cases"].values(),
               *(t for s in grammar["sections"] for t in s.get("terms", []))]
    names = {t["arabic"] for t in entries}
    meanings = " ".join(t["meaning"] for t in entries)

    def labels(node):
        yield from (node[k] for k in ("role", "label") if node.get(k))
        for child in node.get("children", []) + node.get("parts", []):
            yield from labels(child)

    book = root / "backend/data/tarkeeb/examples"
    worked = {strip_diacritics(label) for f in book.glob("*.json")
              for e in json.loads(f.read_text(encoding="utf-8"))["examples"] for label in labels(e["tree"])}
    printed = set(role_table()) | set(ROLES) | worked | {
        strip_diacritics(t["ar"]) for k, t in tarkeeb.items() if k != "unresolved"}
    assert sorted(label for label in printed - names if label not in meanings) == []


@pytest.mark.parametrize("sentence, index, said", [
    ("إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا", 0, "حرف شرط"),
    ("إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا", 1, "فعل الشرط في محل جزم"),
    ("إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا", 8, "رابطة لجواب الشرط"),
    ("إِنْ تَدْرُسْ تَنْجَحْ", 2, "جواب الشرط مجزوم"),
    # لو governs nothing: its clauses have no place, and a لام ties on its answer
    ("لَوْ جَاءَ زَيْدٌ لَأَكْرَمْتُهُ", 0, "حرف شرط غير جازم"),
    ("لَوْ جَاءَ زَيْدٌ لَأَكْرَمْتُهُ", 1, "فعل الشرط، وجملته لا محل لها"),
    ("لَوْ جَاءَ زَيْدٌ لَأَكْرَمْتُهُ", 3, "واللام واقعة في جواب الشرط، وهو جواب الشرط"),
    ("إِنَّ الطَّالِبَ مُجْتَهِدٌ", 0, "ناسخ")])  # nearest case: إنّ before its noun
def test_a_verb_after_a_conditional_particle_makes_it_a_condition(sentence: str, index: int, said: str):
    assert said in _read(sentence)["words"][index]["reason"]


@pytest.mark.parametrize("sentence, index, role", [
    ("زَيْدٌ ضَارِبٌ بَكْرًا", 2, "مفعول به"),  # the notes' own example of شبه الفعل
    ("لَوْ كُنْتُ آمِرًا أَحَدًا أَنْ يَسْجُدَ لأَحَدٍ", 3, "مفعول به"),  # آمِر: فاعل of a hamza root
    ("هَلْ أَنْتَ فَاهِمٌ الدَّرْسَ", 3, "مفعول به"),  # linked as idafa, but its fatha says object
    ("زَيْدٌ قَادِمٌ مُسْرِعًا", 2, "حال")])  # nearest case: a describing word stays a حال
def test_an_active_participle_takes_its_object_as_its_verb_does(sentence: str, index: int, role: str):
    assert _read(sentence)["words"][index]["role"] == role


def test_two_conditions_joined_by_waw_are_two_conditions_not_one_verb_governing_another():
    # مَنْ leads, a verb follows, an answer follows: a conditional noun, not the relative;
    # the second مَنْ governs أَفْطَرَ, the first answer does not
    read = _read("مَنْ شَاءَ فَلْيَصُمْهُ وَمَنْ شَاءَ أَفْطَرَ")
    words = read["words"]
    assert read["summary"] == term_ar("jumlah_shartiyyah")
    assert [words[i]["role"] for i in (0, 3)] == ["اسم شرط جازم"] * 2
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


# One reading per small word (particles.stamp): the card names what the word does here.
PARTICLE_ROLES = [
    ("إِذَا قَالَ الْعَبْدُ لاَ إِلَهَ إِلاَّ اللَّهُ وَاللَّهُ أَكْبَرُ",
     ["مفعول فيه", "فعل", "فاعل", "حرف", "اسم لا", "حرف", "بدل", "مبتدأ", "خبر"]),
    ("لاَ ضَرَرَ وَلاَ ضِرَارَ", ["حرف", "اسم لا", "حرف", "اسم لا"]),
    ("جَاءَ زَيْدٌ لَا خَالِدٌ", ["فعل", "فاعل", "حرف", "معطوف"]),
    ("جَاءَ زَيْدٌ لَا عَمْرٌو", ["فعل", "فاعل", "حرف", "معطوف"]),  # the written و of عمرو hides no case
    ("الْحَلاَلُ بَيِّنٌ وَالْحَرَامُ بَيِّنٌ", ["مبتدأ", "خبر", "مبتدأ", "خبر"]),
    ("أَىُّ الأَعْمَالِ أَفْضَلُ", ["مبتدأ", "مضاف إليه", "خبر"]),
    ("مَتَى السَّفَرُ", ["خبر", "مبتدأ"]),  # nearest case: a built question word takes no مضاف إليه
]


@pytest.mark.parametrize("sentence, expected", PARTICLE_ROLES)
def test_a_small_word_is_read_once_by_what_surrounds_it(sentence: str, expected: list[str]):
    assert [w["role"] for w in iraab.analyze(sentence)["words"]] == expected


def test_each_reading_names_the_particle():
    words = iraab.analyze("إِذَا قَالَ الْعَبْدُ لاَ إِلَهَ إِلاَّ اللَّهُ وَاللَّهُ أَكْبَرُ")["words"]
    assert "ظرف شرط غير جازم" in words[0]["reason"]
    assert "لا النافية للجنس" in words[3]["reason"] and "أداة استثناء" in words[5]["reason"]
    assert "ويجوز أن تكون استئنافية" in words[7]["reason"]
    assert "أداة حصر" in iraab.analyze("مَا جَاءَ إِلَّا زَيْدٌ")["words"][2]["reason"]


@pytest.mark.parametrize("sentence, expected", [
    ("لَا تَعْبُدُوا إِلَّا اللَّهَ", ["حرف", "فعل", "حرف", "مفعول به"]),  # the parser hangs the noun on إلا
    ("لَا تَضْرِبْ إِلَّا زَيْدًا", ["حرف", "فعل", "حرف", "مفعول به"]),
    ("لَا تَقُلْ إِلَّا الْحَقَّ", ["حرف", "فعل", "حرف", "مفعول به"]),
    ("مَا ذَهَبَ إِلَّا إِلَى الْمَدْرَسَةِ", ["حرف", "فعل", "حرف", "حرف جر", "مجرور"]),
    ("لَا إِلَهَ إِلَّا اللَّهُ", ["حرف", "اسم لا", "حرف", "بدل"]),  # control: after a noun in its case, a بدل
])
def test_the_word_after_a_restricting_illa_takes_the_place_the_sentence_leaves(sentence: str, expected: list[str]):
    assert [w["role"] for w in iraab.analyze(sentence)["words"]] == expected


def _shape(node: dict) -> tuple:
    """A picture as the book draws it: each unit's label and job, each leaf's role."""
    from backend.services.arabic_text import strip_diacritics
    if node.get("word") is not None:
        return (strip_diacritics(node["role"]),)
    return (strip_diacritics(node.get("label") or ""), strip_diacritics(node.get("role") or ""),
            *(_shape(kid) for kid in node["children"]))


def test_the_wonder_form_is_drawn_as_the_books_own_example():
    """ما أحسن زيدًا (Tasheel 1.4.2 p8): ما the مبتدأ, the verb's clause its khabar, the verb with its hidden doer."""
    import json
    from backend.services.nahw_book import RULES
    book = next(e for e in json.loads((RULES.parent / "tarkeeb" / "examples" / "tasheel-al-nahw.json")
                                      .read_text(encoding="utf-8"))["examples"] if e["id"] == "1.4.2-taajjub")
    ours = _syntax_read(book["sentence"])
    assert _shape(ours["tree"]["tree"]) == _shape(book["tree"])
    assert "ضمير مستتر وجوبًا تقديره هو يعود على ما" in _picture_roles(ours["tree"]["tree"])
    card = _read(book["sentence"])["words"][1]
    assert card["role"] == "فعل" and "فعل ماضٍ جامد للتعجب مبني على الفتح" in card["reason"]


@pytest.mark.parametrize("sentence, expected", [
    ("مَا أَجْمَلَ السَّمَاءَ", ["مبتدأ", "فعل", "مفعول به"]),
    ("ما اجمل السماء", ["مبتدأ", "فعل", "مفعول به"]),  # plain text: the shape is read from the letters
    ("ما اشد الحر", ["مبتدأ", "فعل", "مفعول به"]),  # the doubled root, from the analyser's root
    ("مَا أَطْوَلَ اللَّيْلَ", ["مبتدأ", "فعل", "مفعول به"]),
    ("مَا أَكْرَمَ زَيْدٌ عَمْرًا", ["حرف", "فعل", "فاعل", "مفعول به"]),  # a noun in raf': the ordinary negation
    ("ما أكرم زيد عمرا", ["حرف", "فعل", "فاعل", "مفعول به"]),
    ("مَا أُكْرِمَ زَيْدٌ", ["حرف", "فعل", "نائب فاعل"]),  # the typed damma says it is not the wonder shape
    ("مَا أَعْطَى الرَّجُلَ كِتَابًا", ["حرف", "فعل", "مفعول به", "مفعول به"]),  # two objects: not the wonder form
    ("ما أنزل الله بها من سلطان", ["حرف", "فعل", "فاعل", "حرف جر", "حرف جر", "مجرور"]),  # أنزل gives no comparative
    ("مَا أَجْمَلَهَا", ["مبتدأ", "فعل"]),  # the pronoun on the verb is its one object
    ("مَا أَعْظَمَكَ", ["مبتدأ", "فعل"]),
    ("ما أحلاها", ["مبتدأ", "فعل"]),
    ("مَا أَجْمَلَهَا مِنْ لَيْلَةٍ", ["مبتدأ", "فعل", "حرف جر", "مجرور"]),  # a preposition after it is no question word
    ("مَا أَعْطَاهَا كِتَابًا", ["حرف", "فعل", "مفعول به"]),  # a second object: not the wonder form
])
def test_the_wonder_form_is_told_by_its_shape_and_its_noun(sentence: str, expected: list[str]):
    assert [w["role"] for w in iraab.analyze(sentence)["words"]] == expected


@pytest.mark.parametrize("sentence, expected", [
    ("مَا اسْمُكَ", ["خبر", "مبتدأ"]),  # the question word is the khabar brought to the front (Tasheel 2.4.7 p47)
    ("مَا هَذَا", ["خبر", "مبتدأ"]),
    ("مَا الْإِيمَانُ", ["خبر", "مبتدأ"]),
    ("مَنْ أَنْتَ", ["خبر", "مبتدأ"]),
    ("مَنْ هَذَا؟", ["خبر", "مبتدأ"]),
    ("مَنْ أَبُوكَ", ["خبر", "مبتدأ"]),
    ("قَالَ مَا اسْمُكَ", ["فعل", "خبر", "مبتدأ"]),
    ("يَا أَخِي مَا اسْمُكَ", ["حرف", "منادى", "خبر", "مبتدأ"]),
    ("وَمَا أَدْرَاكَ مَا يَوْمُ الدِّينِ", ["مبتدأ", "فعل", "خبر", "مبتدأ", "مضاف إليه"]),  # a verb of informing, its second object a question
    ("مَا أَجْمَلَ السَّمَاءَ", ["مبتدأ", "فعل", "مفعول به"]),
    # not a question: ما الحجازية, a negation, a relative before a ظرف or a verb, من before a preposition
    ("مَا هَذَا بَشَرًا", ["حرف", "اسم كان", "خبر كان"]),
    ("ما زيدٌ قائمًا", ["حرف", "اسم كان", "خبر كان"]),
    ("وَمَا زَيْدٌ قَائِمًا", ["حرف", "اسم كان", "خبر كان"]),  # a وَ or فَ before it leaves it ما الحجازية
    ("فَمَا هَذَا بَشَرًا", ["حرف", "اسم كان", "خبر كان"]),
    ("مَا جَاءَ إِلَّا زَيْدٌ", ["حرف", "فعل", "حرف", "فاعل"]),
    ("مَنْ جَاءَ", ["مبتدأ", "فعل"]),
    ("مَنْ فِي الْبَيْتِ", ["مبتدأ", "حرف جر", "مجرور"]),
    ("إِنَّ مَا عِنْدَ اللَّهِ هُوَ خَيْرٌ لَكُمْ", ["حرف", "اسم إن", "مفعول فيه", "مضاف إليه", "مبتدأ", "خبر إن", "حرف جر"]),
])
def test_a_question_word_before_its_mubtada_is_the_khabar(sentence: str, expected: list[str]):
    assert [w["role"] for w in iraab.analyze(sentence)["words"]] == expected


@pytest.mark.parametrize("sentence, negations", [
    ("مَا أَنْتَ إِلَّا بَشَرٌ", 1),
    ("قَالُوا مَا أَنْتُمْ إِلَّا بَشَرٌ", 1),  # quoted speech: a verb of saying does not take the ما as its object
    ("ما قلت لهم إلا ما أمرتني به", 1),  # the first ما negates, the second is the relative
    ("لَا يَعْلَمُ مَا فِي الْغَيْبِ إِلَّا اللَّهُ", 0),  # the verb takes the ما as its object
    ("قَرَأْتُ مَا كَتَبَ الطُّلَّابُ إِلَّا زَيْدًا", 0),
])
def test_only_a_ma_that_opens_its_clause_is_the_negation_before_illa(sentence: str, negations: int):
    shown = _picture_roles(_syntax_read(sentence)["tree"]["tree"])
    assert shown.count("ما النافية") == negations


def test_the_wonder_verbs_noun_after_its_pronoun_is_no_second_object():
    words = iraab.analyze("مَا أَجْمَلَهَا لَيْلَةً")["words"]
    assert [w["role"] for w in words[:2]] == ["مبتدأ", "فعل"] and "للتعجب" in words[1]["reason"]


def test_a_relative_before_a_zarf_and_its_verb_is_no_question():
    words = iraab.analyze("مَا عِنْدَكُمْ يَنْفَدُ")["words"]
    assert words[0]["role"] == "مبتدأ" and words[-1]["role"] == "فعل" and "اسْتِفْهَامِيَّةٌ" not in _sentence_label("مَا عِنْدَكُمْ يَنْفَدُ")


def _sentence_label(sentence: str) -> str:
    return _syntax_read(sentence)["tree"]["tree"].get("label") or ""


@pytest.mark.parametrize("sentence", ["مَا أَنْتَ إِلَّا بَشَرٌ", "وَمَا مُحَمَّدٌ إِلَّا رَسُولٌ", "ما أنت إلا بشر"])
def test_ma_before_illa_is_the_negation_and_illa_restricts_the_khabar(sentence: str):
    words = iraab.analyze(sentence)["words"]
    assert [w["role"] for w in words] == ["حرف", "مبتدأ", "حرف", "خبر"]
    assert "أداة حصر" in words[2]["reason"]


@pytest.mark.parametrize("sentence", ["هَلْ أَنْتَ تَكْتُبُ", "ما أنت إلا بشر", "هَلِ الْوَلَدُ نَائِمٌ", "يَا أَخِي مَا اسْمُكَ",
                                      "مَنْ أَنْتَ فِي هَذِهِ الْمَدِينَةِ"])
def test_the_picture_keeps_the_order_the_words_were_typed(sentence: str):

    def leaves(node: dict) -> list[int]:
        return ([node["word"]] if node.get("word") is not None else []) + [i for kid in node.get("children", []) for i in leaves(kid)]
    order = leaves(_syntax_read(sentence)["tree"]["tree"])
    assert order == sorted(order)


@pytest.mark.parametrize("sentence, name", [
    ("مَا هَذَا بَشَرًا", "ما الحجازية"),  # a particle that works like ليس is no فعل ناقص
    ("كَانَ زَيْدٌ قَائِمًا", "فعل ناقص"),
])
def test_the_picture_names_the_governor_of_kana(sentence: str, name: str):

    def roles(node: dict) -> list[str]:
        return [node.get("role")] + [r for kid in node.get("children", []) for r in roles(kid)]
    assert name in roles(_syntax_read(sentence)["tree"]["tree"])


@pytest.mark.parametrize("sentence, doer", [
    ("أَنْتَ تَكْتُبُ", "ضمير مستتر تقديره أنتَ"),  # the khabar's pronoun goes back to its mubtada
    ("هِيَ تَكْتُبُ", "ضمير مستتر تقديره هي"),
    ("أَنْتِ تَكْتُبِينَ", "ضمير متصل (أنتِ)"),  # the ياء is the doer, not a hidden أنتَ أو هي
    ("تَكْتُبِينَ", "ضمير متصل (أنتِ)"),
    ("تَكْتُبُ", "ضمير مستتر تقديره أنتَ أو هي"),  # nothing settles it
])
def test_a_detached_pronoun_is_the_mubtada_and_settles_the_verbs_doer(sentence: str, doer: str):
    shown = _picture_roles(_syntax_read(sentence)["tree"]["tree"])
    assert doer in shown
    if sentence.startswith(("أَنْتَ", "هِيَ", "أَنْتِ")):
        assert [w["role"] for w in iraab.analyze(sentence)["words"]][0] == "مبتدأ" and "خبر" in shown


@pytest.mark.parametrize("sentence, roles", [
    # a typed case clash rules out the نعت: the fatha makes الفقير the first object
    ("أَعْطَى الرَّجُلُ الْفَقِيرَ دِرْهَمًا", ["فعل", "فاعل", "مفعول به", "مفعول به"]),
    # آتى takes two objects, so the second is never a حال
    ("لَا يُؤْتُونَ النَّاسَ نَقِيرًا", ["حرف", "فعل", "مفعول به", "مفعول به"]),
    # nearest case: an indefinite word after one object stays the حال
    ("جَاءَ الرَّجُلُ ضَاحِكًا", ["فعل", "فاعل", "حال"])])
def test_two_objects_of_a_verb_of_giving_are_both_objects_and_a_case_clash_is_no_naat(sentence: str, roles: list[str]):
    assert [w["role"] for w in _read(sentence)["words"]] == roles


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


@pytest.mark.parametrize("sentence, particle, verb", [
    ("وَلَا تَأْكُلُوهَا", "لا الناهية", "فعل مضارع للنهي"),
    ("وَلَا تَأْكُلُوهَآ", "لا الناهية", "فعل مضارع للنهي"),  # the Qur'an's spelling of the same ending
    ("لِيَكْتُبْ زَيْدٌ", "لام الأمر", "فعل مضارع للأمر"),
    ("اكْتُبِ الدَّرْسَ", None, "فعل أمر"),
])
def test_a_verb_that_gives_an_order_is_named_for_it_in_the_picture(sentence: str, particle: str | None, verb: str):
    shown = _picture_roles(_syntax_read(sentence)["tree"]["tree"])
    assert verb in shown and (particle is None or particle in shown)


def test_the_pronoun_on_a_verb_is_no_nun_of_the_five_verbs():
    # لا يَدْعُوهُ keeps its root و (not the dropped nun), لا تَأْكُلُونَهَا keeps its nun: neither is jussive
    assert [w["case"] for w in analysed("لَا يَدْعُوهُ زَيْدٌ")][1] == "raf'"
    assert [w["case"] for w in analysed("لَا تَأْكُلُونَهَا")][1] == "raf'"


@pytest.mark.parametrize("sentence, word, role", [
    ("فَإِنْ آنَسْتُمْ مِنْهُمْ رُشْدًا فَادْفَعُوا إِلَيْهِمْ أَمْوَالَهُمْ", "فَادْفَعُوا", "فعل"),  # the word list has no such command
    ("فَإِنْ آنَسْتُمْ مِنْهُمْ رُشْدًا فَادْفَعُوا إِلَيْهِمْ أَمْوَالَهُمْ", "أَمْوَالَهُمْ", "مفعول به"),
])
def test_a_command_the_word_list_lacks_is_read_by_sarf_under_its_joined_fa(sentence: str, word: str, role: str):
    got = {w["word"]: w for w in analysed(sentence)}
    assert got[word]["role"] == role


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

