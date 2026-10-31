"""Every question book.py asks of a word spells the word itself (book_spelling), so a caller
passes a token's lemma or form as it is; and facts.reading is the one way to ask what
particles.stamp read a word as."""
import pytest

from backend.services.nahw.book import (book_spelling, condition_of, extra_ba_on, is_built_word, is_extra_ba, is_one,
                                        kaffa_sister, only_adverb, six_noun_case)
from backend.services.nahw.syntax import condition
from backend.services.nahw.syntax.facts import is_preposition, is_verb, reading
from backend.services.nahw.syntax.naming import NAMED

MADDAH = "ٓ"  # kept by the parser's own cleaning (dediac_ar), a mark to the book


@pytest.mark.parametrize("written, spelled", [
    ("ٱنفك", "انفك"),  # the wasl alif is written ا
    ("ب+", "ب"),  # a joined letter's + aside
    ("+ما", "ما"),
    ("لَيْسَ", "ليس"),  # vowels off
    ("جا" + MADDAH + "ء", "جاء"),  # the maddah too
    ("ذٰلك", "ذلك"),  # and the superscript alif
])
def test_book_spelling_is_bare_letters(written, spelled):
    assert book_spelling(written) == spelled


def test_each_book_question_spells_its_own_word():
    assert extra_ba_on("لَيْسَ") == extra_ba_on("ليس") is not None
    assert is_extra_ba("ب+") and is_extra_ba("بِ")
    assert kaffa_sister("إِنَّمَا") == "إن"
    assert condition_of("مَنْ") == condition_of("من") is not None
    assert is_one("كَانَ", "kana") and is_one("ٱنْفَكَّ", "kana", "needs_negation")
    assert only_adverb("قَبْل") == only_adverb("قبل")
    assert is_built_word("أَمْسِ") and is_built_word("أمس")
    assert six_noun_case("أخو", "أَخ") == six_noun_case("أخو", "أخ") == "u"


def test_reading_asks_what_the_word_was_read_as():
    read = {"family": "istifham", "kind": "ism", "named": None, "sense": "part_interrog"}
    assert reading({"reading": read}) == "istifham"
    assert reading({"reading": read}, "kind") == "ism"
    assert reading({"reading": None}) is None  # not read: its lists decide
    assert reading({}) is None and reading(None, "named") is None  # no word before the first


def test_a_reading_overrides_the_parser_verb_tag():
    """أَلَا tagged a verb but read as a particle is no verb; ما of wonder read as a fi'l is one."""
    ala = {"pos": "VRB", "typed": "أَلَا", "reading": {"family": "tanbih", "kind": "harf"}}
    wonder = {"pos": "PRT", "typed": "مَا", "reading": {"family": "wonder", "kind": "fil"}}
    assert not is_verb(ala) and is_verb(wonder)
    assert is_verb({**ala, "reading": None})  # not read: the parser's tag stands


def test_a_reading_overrides_the_parser_preposition_tag():
    """حتى before إذا is no جر, whatever the parser tagged it; a word read as جر is one."""
    hatta = {"pos": "PRT", "pos_camel": "prep", "lemma": "حَتَّى", "reading": {"family": "ibtida", "kind": "harf"}}
    assert not is_preposition(hatta) and is_preposition({**hatta, "reading": None})
    assert is_preposition({**hatta, "pos_camel": "conj", "reading": {"family": "jarr", "kind": "harf"}})


def _opened(pos: str, kind: str | None) -> list[dict]:
    """ما then two past verbs (مَا قَرَأَ فَهِمَ), ما tagged `pos` and read as a `kind`."""
    words = [{"id": 1, "form": "ما", "lemma": "ما", "pos": pos, "head": 2, "reading": {"family": "x", "kind": kind} if kind else None},
             {"id": 2, "form": "قرأ", "lemma": "قرأ", "pos": "VRB", "head": 0, "asp": "p"},
             {"id": 3, "form": "فهم", "lemma": "فهم", "pos": "VRB", "head": 2, "asp": "p"}]
    return condition.find(words, [None, NAMED.fil, NAMED.fil], [None] * 3, [[], [], []])


def test_a_conditional_noun_is_a_noun_by_its_reading_before_its_tag():
    """ما النافية puts no verb in jazm: read as a particle it opens no condition, however tagged;
    read as a noun it opens one before a past verb, however tagged."""
    assert _opened("NOM", "harf") == [] and _opened("NOM", None) != []
    assert _opened("PRT", "ism") != [] and _opened("PRT", None) == []


@pytest.mark.parametrize("vowelled, bare, mabni", [
    ("مُبْتَدَأٌ", "مبتدأ", True),  # قُلْ هُوَ: built, in the place of raf'
    ("خَبَرٌ", "خبر", False),
    ("بَدَلٌ", "بدل", False),
])
def test_a_role_written_vowelled_gives_the_bare_roles_reason(vowelled, bare, mabni):
    # a recorded ayah names its words vowelled; the reason is the book's for the bare name
    from backend.services.nahw.book import reason
    assert reason(vowelled, mabni=mabni) == reason(bare, mabni=mabni) != f"{bare}."
