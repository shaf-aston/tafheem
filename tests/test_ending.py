"""The three facts that decide an ending, each stated once (nahw_book.py).

Facts (base, lemma, root, number, CAMeL pos and aspect) are what the pipeline hands over for the typed word;
the lemmas and roots below are CAMeL's own for these words.
"""
import pytest

from backend.services.nahw_book import is_diptote, is_fem_plural, is_mabni

PLAIN = dict(pos="noun", lemma="x", attached=False, annexed=False)


@pytest.mark.parametrize("base, number, plural", [
    ("المعلمات", "p", True),
    ("بنات", "p", True),            # بنت is feminine: its plural is sound, the kasra is nasb too
    ("القانتات", "na", True),       # CAMeL gives the plural itself as lemma, number unread
    ("سوآت", "p", True),            # the madda holds the alef
    ("امرأت", "s", False),          # a singular written with ت in an idafa: no alef
    ("ذات", "s", False),
    ("مرضات", "-", False),          # CAMeL could not read it
    ("كتاب", "s", False),
])
def test_sound_feminine_plural_ends_in_alef_ta(base, number, plural):
    assert is_fem_plural(base, number) is plural


@pytest.mark.parametrize("typed, flags, diptote", [
    ("مَسَاجِدَ", {}, True),                      # fatha for jarr: بِمَسَاجِدَ (a broken plural is no sound one)
    ("أَحْمَدَ", {}, True),
    ("جَهَنَّمَ", {}, True),
    ("فِرْعَوْنَ", {}, True),                      # ends like a plural's ـون but is one name
    ("إِلْيَاسَ", {}, True),                       # إل is not ال
    ("طَرِيقَ", {"annexed": True}, False),         # طَرِيقَ جَهَنَّمَ: a مضاف, the fatha is its nasb
    ("مَسَاجِدِكُمْ", {"attached": True}, False),   # a pronoun on it
    ("الْمَسَاجِدَ", {}, False),                    # ال
    ("ٱلْمَسَاجِدَ", {}, False),                    # wasla alef
    ("مَسَاجِدًا", {}, False),                      # tanween
    ("مَسَاجِدِ", {}, False),                       # a kasra is jarr itself
    ("ثَلَاثَةَ", {"lemma": "عشرين"}, False),         # a number's build
    ("هَذَا", {"pos": "pron_dem"}, False),            # a pointer is built
])
def test_diptote_fatha_stands_for_the_kasra(typed, flags, diptote):
    assert is_diptote(typed, **{**PLAIN, **flags}) is diptote


@pytest.mark.parametrize("args, mabni", [
    (("pron",), True),
    (("pron_dem",), True),
    (("pron_rel",), True),
    (("pron_interrog",), True),
    (("noun",), False),
    (("verb",), False),                          # no aspect asked: a word list, not a verb's build
    (("verb", "p", "كتب"), True),
    (("verb", "c", "اكتب"), True),
    (("verb", "i", "يكتب"), False),
    (("verb", "i", "اكتب"), True),                # CAMeL says present, the shape is a command
])
def test_mabni_covers_the_built_words_and_verbs(args, mabni):
    assert is_mabni(*args) is mabni
