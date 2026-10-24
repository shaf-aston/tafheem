"""What an Anki card has to say before it may join the quiz.

These rules used to sit inside the loop that walks a deck file, so checking one
meant having the .apkg. They are the rules that decide whether a card becomes a
quiz question, and a wrong one either drops good words or lets a card note in as
if it were a meaning.
"""
from __future__ import annotations

import pytest

from backend.scripts.build_lexicon import anki_note

SPEC = {
    "word_type": "noun",
    "pair": ("Arabic", "English"),
    "set_id": "bayna",
    "source": "Bayna Yadayk",
}
TAGS = "Bayna_Yadayk::Book3::Ch.8::Nouns"


def test_a_good_card_becomes_a_word():
    word = anki_note({"Arabic": "كِتَاب", "English": "book"}, SPEC, TAGS, "deck.apkg")
    assert word.ar == "كِتَاب"
    assert word.en == "book"
    assert word.wordType == "noun"
    assert word.source == "Bayna Yadayk"
    assert word.sets == {"bayna"}
    assert word.groups == {"bayna:book3-ch8"}


def test_the_meaning_key_is_the_gloss_lowered():
    """Two cards glossed the same way are one meaning, which is what stops both
    being offered as options in the same question."""
    word = anki_note({"Arabic": "كِتَاب", "English": "Book"}, SPEC, TAGS, "deck.apkg")
    assert word.meaningKey == "book"


def test_a_card_whose_english_is_still_arabic_is_not_a_meaning():
    """The deck writes some cards as a note in Arabic. Quizzing on one asks the
    reader to pick Arabic as the meaning of Arabic."""
    assert anki_note({"Arabic": "كِتَاب", "English": "كتاب"}, SPEC, TAGS, "deck.apkg") is None


def test_a_card_with_no_meaning_at_all_is_left_out():
    assert anki_note({"Arabic": "كِتَاب", "English": ""}, SPEC, TAGS, "deck.apkg") is None


def test_a_card_with_no_arabic_is_left_out():
    assert anki_note({"Arabic": "", "English": "book"}, SPEC, TAGS, "deck.apkg") is None


def test_a_card_that_names_no_chapter_stops_the_build():
    """It would join silently and weaken every question that draws a wrong
    option from its group, so it is loud instead."""
    with pytest.raises(SystemExit, match="deck.apkg"):
        anki_note({"Arabic": "كِتَاب", "English": "book"}, SPEC, "", "deck.apkg")


def test_the_chapter_may_come_from_the_reference_field_instead_of_the_tags():
    word = anki_note(
        {"Arabic": "كِتَاب", "English": "book", "reference": "Book2::Ch.5"},
        SPEC, "", "deck.apkg",
    )
    assert word.groups == {"bayna:book2-ch5"}


def test_the_other_tag_spelling_is_read_too():
    word = anki_note({"Arabic": "كِتَاب", "English": "book"}, SPEC,
                     "Arabiyyah_Bayna_Yadayk_1::Chapter_04", "deck.apkg")
    assert word.groups == {"bayna:book1-ch04"}


def test_a_root_is_kept_only_when_the_deck_states_one():
    """A missing field stays empty rather than becoming a guessed fact."""
    assert anki_note({"Arabic": "كِتَاب", "English": "book"}, SPEC, TAGS, "d").root == ""
    # Spaced out as the deck writes it. Only the harakat and the HTML go here;
    # who joins the letters up is the reader of the root, not this.
    word = anki_note({"Arabic": "كِتَاب", "English": "book", "Root": "كِ تَ بْ"}, SPEC, TAGS, "d")
    assert word.root == "ك ت ب"
