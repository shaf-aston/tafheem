"""Sentence context must decide undiacritised homographs.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import pytest

from backend.services import morphology

VERB_SENTENCE = "ذهب الولد إلى المدرسة"  # "the boy went to school"
NOUN_SENTENCE = "الذهب غالٍ"  # "gold is expensive"

needs_camel = pytest.mark.skipif(
    not morphology._CAMEL_AVAILABLE, reason="CAMeL Tools not installed"
)


def _pos_of(sentence: str, word: str) -> str:
    tags = morphology.analyze_sentence(sentence)
    return next(t["pos"] for t in tags if t["word"] == word)


@needs_camel
def test_homograph_reads_as_verb_when_the_sentence_needs_one():
    # ذهب on its own ranks as the noun "gold"; only the sentence makes it a verb.
    assert _pos_of(VERB_SENTENCE, "ذهب") == "verb"


@needs_camel
def test_following_noun_keeps_its_noun_reading():
    assert _pos_of(VERB_SENTENCE, "الولد") == "noun"


@needs_camel
def test_same_root_stays_a_noun_when_the_sentence_has_no_verb():
    assert _pos_of(NOUN_SENTENCE, "الذهب") == "noun"


@needs_camel
def test_fully_diacritised_input_settles_its_own_reading():
    # Exact-diacritic match must win over the disambiguator's ranking.
    tags = morphology.analyze_sentence("ذَهَبَ الوَلَدُ")
    assert tags[0]["pos"] == "verb"


def test_empty_sentence_returns_no_tags():
    assert morphology.analyze_sentence("   ") == []


@needs_camel
def test_incomplete_root_is_reported_as_no_root_not_as_a_placeholder():
    # The database gives ولد the root "#.ل.د", an unresolved first radical.
    tags = morphology.analyze_sentence(VERB_SENTENCE)
    roots = [t["root"] for t in tags]
    assert all("#" not in r for r in roots), roots


@needs_camel
def test_a_fully_known_root_still_renders():
    tags = morphology.analyze_sentence(VERB_SENTENCE)
    # Plain letters, no hyphens: the same string is what the Define and
    # In-the-Qur'an buttons search with, and "د-ر-س" is in no index.
    assert next(t for t in tags if t["word"] == "المدرسة")["root"] == "درس"


@needs_camel
def test_typed_vowels_overrule_the_statistics():
    # Ranked alone, فَتَحَ is the noun فَتْح; its vowels say it is the verb.
    assert _pos_of("فَتَحَ زَيْدٌ الْبَابَ", "فَتَحَ") == "verb"


@needs_camel
def test_glued_punctuation_no_longer_hides_the_word():
    tags = morphology.analyze_sentence("مَرْحَبًا، كَيْفَ حَالُكَ؟")
    assert [t["word"] for t in tags] == ["مَرْحَبًا", "كَيْفَ", "حَالُكَ"]
    assert all(t["gloss"] != "NO_ANALYSIS" for t in tags)


def test_vowel_agreement():
    agree = morphology._vowel_agreement
    assert agree("فَتَحَ", "فَتْحَ") is None          # fatha typed where the reading has sukun
    assert agree("فَتَحَ", "فَتَحَ") == 3
    assert agree("زَيْدٌ", "زَيْد") == 2               # a bare letter in the reading agrees
    assert agree("كتب", "كَتَبَ") == 0                 # nothing typed, nothing to weigh
    assert agree("زَيْدٌ", "زَيْدٍ") is None          # the same letter, a different ending
    assert agree("زَيْدٌ", "زَيْدًا") == 0             # the tanween alef adds a letter: no verdict
