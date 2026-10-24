"""Every question book.py asks of a word spells the word itself (book_spelling), so a caller
passes a token's lemma or form as it is; and facts.reading is the one way to ask what
particles.stamp read a word as."""
import pytest

from backend.services.nahw.book import (book_spelling, condition_of, extra_ba_on, is_built_word, is_extra_ba, is_one,
                                        kaffa_sister, only_adverb, six_noun_case)
from backend.services.nahw.syntax.facts import is_verb, reading

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
