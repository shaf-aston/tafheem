"""The rule engine's roles, and the name the word grid colours each one by.

The grid used to work out its colour by searching the role text for English
words ('fail', 'mafool') while this engine writes that text in Arabic. Nothing
ever matched, so every noun and verb the engine identified was drawn in the
default grey.

So these check the two halves of the seam that replaced it: every entry the
engine builds carries a `role_key`, and every key it uses is one the contract
allows, because a key that is not in `schemas.ROLE_KEYS` is dropped at the
router and the colour is silently lost again.

Run: python -m pytest tests/test_rule_engine.py
"""
from __future__ import annotations

import pytest

from backend.models.schemas import ROLE_KEYS, WordAnalysis
from backend.services import iraab, rule_engine
from backend.services.nahw_book import term_ar

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
    """The list here and the list in schemas.py are the same list.

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
    from backend.services import morphology, syntax
    rules = rule_engine.analyze(sentence, morphology.analyze_sentence(sentence))
    words = iraab.with_parser_roles(rules, syntax.read(sentence)["roles"])["words"]
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
    from backend.services import morphology, syntax
    rules = rule_engine.analyze(sentence, morphology.analyze_sentence(sentence))
    word = iraab.with_parser_roles(rules, syntax.read(sentence)["roles"])["words"][index]
    assert (word["case"], said in word["reason"]) == (case, True), word


@pytest.mark.parametrize("sentence, lemma", [("قُمْ يَا وَلَدُ", "قام"), ("اُكْتُبْ الدَّرْسَ", "كتب")])
def test_a_command_is_described_as_one(sentence: str, lemma: str):
    """Not the قَمَّ or أَكْتُبُ CAMeL misread it as: its notes and lemma are the command's."""
    from backend.services import morphology
    word = morphology.analyze_sentence(sentence)[0]
    assert (word["lemma"], word["features"].startswith("command"), "perfect" in word["features"]) == (lemma, True, False)


@pytest.mark.parametrize("sentence, verbal", [
    ("لَمْ يَكْتُبْ الطَّالِبُ", True), ("قَدْ نَجَحَ الطَّالِبُ", True), ("مَتَى سَافَرَ الرَّجُلُ", True),
    ("إِنَّ الطَّالِبَ مُجْتَهِدٌ", False)])  # nearest case: a particle before a noun
def test_a_particle_before_the_verb_keeps_the_sentence_verbal(sentence: str, verbal: bool):
    from backend.services import morphology, syntax
    rules = rule_engine.analyze(sentence, morphology.analyze_sentence(sentence))
    summary = iraab.with_parser_roles(rules, syntax.read(sentence)["roles"])["summary"]
    assert (summary == term_ar("jumlah_filiyyah")) is verbal, summary


def _read(sentence: str) -> dict:
    """The route's two steps: the rules, then the parser over them."""
    from backend.services import morphology, syntax
    rules = rule_engine.analyze(sentence, morphology.analyze_sentence(sentence))
    return iraab.with_parser_roles(rules, syntax.read(sentence)["roles"])


# One card field each, found by typing the sentence in (backend/scripts/analyse.py).
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
    ("إِنْ تَدْرُسْ تَنْجَحْ", "jumlah_shartiyyah")])
def test_summary_and_tree_name_the_sentence_alike(sentence: str, term: str):
    answer = _read(sentence)
    from backend.services import syntax
    assert (answer["summary"], syntax.read(sentence)["tree"]["tree"]["label"]) == (term_ar(term), term_ar(term))


def test_a_relative_and_its_silah_are_one_unit():
    """جاء الذي نجح: the الذي unit does the فاعل's job, made of the relative and its صلة."""
    from backend.services import syntax
    doer = syntax.read("جَاءَ الَّذِي نَجَحَ")["tree"]["tree"]["children"][1]
    inside = [(kid.get("role"), kid.get("label")) for kid in doer["children"]]
    assert (doer["role"], doer["label"], inside) == (
        "فاعل", term_ar("mawsool_silah"), [("اسم موصول", None), ("صلة", term_ar("jumlah_filiyyah"))])


def test_word_types_are_the_pages():
    """The types a card may carry are the ones grammar.json labels, and the rules use no other."""
    import json
    from pathlib import Path
    from backend.models.schemas import WORD_TYPES
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
    ("إِنَّ الطَّالِبَ مُجْتَهِدٌ", 0, "ناسخ")])  # nearest case: إنّ before its noun
def test_a_verb_after_in_makes_it_a_condition(sentence: str, index: int, said: str):
    assert said in _read(sentence)["words"][index]["reason"]
