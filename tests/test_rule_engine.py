"""The rule engine's roles, and the name the word grid colours each one by.

The grid used to work out its colour by searching the role text for English
words ('fail', 'mafool') while this engine writes that text in Arabic. Nothing
ever matched, so every noun and verb the engine identified was drawn in the
default grey and only the AI's answers were ever coloured.

So these check the two halves of the seam that replaced it: every entry the
engine builds carries a `role_key`, and every key it uses is one the contract
allows, because a key that is not in `schemas.ROLE_KEYS` is dropped at the
router and the colour is silently lost again.

Run: python -m pytest tests/test_rule_engine.py
"""
from __future__ import annotations

import pytest

from backend.models.schemas import ROLE_KEYS, WordAnalysis
from backend.services import rule_engine

# Two sentences, one of each kind, so both branches of the engine are walked.
VERBAL = "ذهب الولد إلى المدرسة"     # jumlah fi'liyyah
NOMINAL = "الكتاب جديد"              # jumlah ismiyyah


def analysed(sentence: str) -> list[dict]:
    from backend.services import morphology
    tags = morphology.analyze_sentence(sentence)
    return rule_engine.analyze(sentence, tags).get("words", [])


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
    """The AI answers a prompt and can return anything.

    An unknown name must become no colour, never a colour meaning another role.
    """
    word = WordAnalysis.from_raw({"word": "زيدٌ", "role": "فاعل", "role_key": "subject"})
    assert word.role_key is None
    assert word.role == "فاعل"


def test_a_role_key_the_grid_knows_survives():
    word = WordAnalysis.from_raw({"word": "زيدٌ", "role": "فاعل (مرفوع)", "role_key": "fail"})
    assert word.role_key == "fail"


def test_a_word_with_no_key_at_all_is_accepted_uncoloured():
    """An older AI reply, or one that skipped the field; not an error."""
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
    words = syntax.with_parser_roles(rules, syntax.read(sentence)["roles"])["words"]
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
]


@pytest.mark.parametrize("sentence, index, case, said", VERB_CARDS)
def test_verb_card_case_and_reason_agree(sentence: str, index: int, case: str, said: str):
    from backend.services import morphology, syntax
    rules = rule_engine.analyze(sentence, morphology.analyze_sentence(sentence))
    word = syntax.with_parser_roles(rules, syntax.read(sentence)["roles"])["words"][index]
    assert (word["case"], said in word["reason"]) == (case, True), word
