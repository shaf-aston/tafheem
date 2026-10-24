"""Weighing an Arabic word against what its letters mean in Urdu.

The verdict itself is only ever a candidate, so what is worth pinning down is
the two things underneath it: that the two scripts are folded to one spelling,
and that a shared gloss word is what separates a cognate from a trap.
"""
from __future__ import annotations

from backend.scripts.build_urdu_links import fold, meaning_words, verdict_for


def word(ar: str, en: str) -> dict:
    return {"ar": ar, "en": en, "ur": "", "meaningKey": en.lower()}


def test_urdu_spelling_folds_onto_the_arabic_one():
    """Urdu writes four of these letters with its own code point. Without the
    fold مکان and مَكَان are two different words and nothing ever matches."""
    assert fold("مکان") == fold("مَكَان")
    assert fold("کتاب") == fold("كِتَاب")


def test_a_gloss_keeps_only_the_words_that_carry_meaning():
    """"to" and "the" are in nearly every gloss, so counting them would make
    every verb agree with every other verb."""
    assert meaning_words("to bear a load") == {"bear", "load"}
    assert meaning_words("the house of a person") == {"house"}


def test_a_shared_meaning_is_a_cognate():
    found = verdict_for(word("كِتَاب", "book"), ["book, manuscript, volume"], borrowed=True)
    assert found["verdict"] == "cognate"


def test_no_shared_meaning_is_a_false_friend_candidate():
    found = verdict_for(word("مَكَان", "place"), ["house", "space"], borrowed=False)
    assert found["verdict"] == "false-friend"


def test_both_glosses_travel_with_the_verdict():
    """A verdict with its evidence stripped off cannot be checked, and checking
    is the whole point: the test itself is wrong often."""
    found = verdict_for(word("مَكَان", "place"), ["house", "space"], borrowed=False)
    assert found["en"] == "place"
    assert found["urduSenses"] == ["house", "space"]


def test_a_word_with_no_urdu_entry_is_not_weighed_at_all():
    """Silence is not a verdict. Most words have no Urdu entry and must produce
    nothing rather than being filed as disagreeing with an empty list."""
    assert verdict_for(word("زهزه", "to shake"), [], borrowed=False) is None


def test_a_gloss_of_nothing_but_filler_is_not_weighed_either():
    """"the one who" has no word left after the filler is dropped, so it can
    neither agree nor disagree with anything."""
    assert verdict_for(word("ذُو", "the one of"), ["owner"], borrowed=True) is None
