"""Showing what a synonym means, without inventing it.

A synonym used to be a bare Arabic word with "Look up ..." behind it, which told
a reader nothing they could not already see. It now carries its own meaning,
looked up as the entry goes out.

The rule that matters is that a gap stays a gap. Roughly a fifth of the words
Wiktionary lists as synonyms are phrases or proper names with no entry of their
own; for those the meaning is empty and the app says so. A lookup that quietly
fell back to something near-enough, the root's other words, the next entry
along, would be the one failure nobody could see from the screen.
"""
from __future__ import annotations

import json

import pytest

from backend.services import dictionary_service as service


@pytest.fixture
def two_words(monkeypatch):
    """A dictionary of two words, indexed the way the service indexes."""
    kataba = {"arabic": "كَتَبَ", "root": "ك ت ب", "definitions": ["to write", "to record"]}
    kitaab = {"arabic": "كِتَاب", "root": "ك ت ب", "definitions": ["a book"]}
    index = {
        "كتب": [kataba, kitaab],  # the bare word, and the root naming both
        "كتاب": [kitaab],
    }
    monkeypatch.setattr(service, "_arabic_index", index)
    monkeypatch.setattr(service, "_loaded", True)
    return kataba, kitaab


def test_a_word_gives_its_first_definition(two_words):
    assert service.meaning_of("كَتَبَ") == "to write"


def test_diacritics_do_not_have_to_match(two_words):
    """Wiktionary's synonym lists are fully vowelled and its headwords vary."""
    assert service.meaning_of("كتب") == "to write"


def test_a_word_with_no_entry_says_nothing(two_words):
    assert service.meaning_of("سَعْدَان عَنْكَبُوتِيّ") == ""


def test_a_root_match_is_not_a_meaning(two_words, monkeypatch):
    """The index keys entries by their root as well as their word.

    Asking what ك ت ب means must not answer with the first word filed under it:
    the other words off a root mean related but different things, and a reader
    hovering a synonym would be told a meaning the word does not have.
    """
    monkeypatch.setattr(service, "_arabic_index", {"ك ت ب": [two_words[0]]})
    assert service.meaning_of("ك ت ب") == ""


def test_an_entry_with_no_definitions_is_skipped(monkeypatch):
    bare = {"arabic": "كَتَبَ", "definitions": []}
    full = {"arabic": "كَتَبَ", "definitions": ["to write"]}
    monkeypatch.setattr(service, "_arabic_index", {"كتب": [bare, full]})
    monkeypatch.setattr(service, "_loaded", True)
    assert service.meaning_of("كَتَبَ") == "to write"


def test_an_empty_word_is_not_looked_up(two_words):
    assert service.meaning_of("   ") == ""


def test_each_synonym_goes_out_with_its_meaning(two_words):
    entry = {"arabic": "سَطَرَ", "definitions": ["to write"], "synonyms": [["كَتَبَ", "كِتَاب"]]}
    assert service._with_synonym_meanings(entry)["synonyms"] == [
        [
            {"word": "كَتَبَ", "meaning": "to write"},
            {"word": "كِتَاب", "meaning": "a book"},
        ]
    ]


def test_a_synonym_with_no_entry_still_goes_out(two_words):
    """It is still worth showing and still worth pressing, it just cannot be
    explained. Dropping it would hide a word Wiktionary put there on purpose."""
    entry = {"arabic": "سَطَرَ", "definitions": ["to write"], "synonyms": [["أَبُو حُدَيْج"]]}
    assert service._with_synonym_meanings(entry)["synonyms"] == [
        [{"word": "أَبُو حُدَيْج", "meaning": ""}]
    ]


def test_the_lists_stay_in_step_with_the_definitions(two_words):
    entry = {
        "arabic": "سَطَرَ",
        "definitions": ["to write", "to rule a line"],
        "synonyms": [["كَتَبَ"], []],
    }
    shaped = service._with_synonym_meanings(entry)
    assert len(shaped["synonyms"]) == len(shaped["definitions"])
    assert shaped["synonyms"][1] == []


def test_the_loaded_dictionary_is_never_changed_in_place(two_words):
    """Every search hands out the same entry objects. Writing the meanings into
    one would rewrite the dictionary itself, and the second search for the same
    word would be reading a shape the first one left behind."""
    entry = {"arabic": "سَطَرَ", "definitions": ["to write"], "synonyms": [["كَتَبَ"]]}
    service._with_synonym_meanings(entry)
    assert entry["synonyms"] == [["كَتَبَ"]]


def test_an_entry_with_no_synonyms_is_passed_straight_through(two_words):
    entry = {"arabic": "سَطَرَ", "definitions": ["to write"], "synonyms": [[]]}
    assert service._with_synonym_meanings(entry) is entry


def test_most_of_the_shipped_synonyms_can_be_explained():
    """Measured over the real dictionary, not asserted from the code.

    5,474 of 6,697 (81.7%) at the time of writing. The floor is set well below
    that so a rebuild that gains or loses a few hundred does not fail here, but
    a change that broke the lookup outright, or an index that started answering
    with root matches, would drop far through it.
    """
    if not service._DICTIONARY_JSON.exists():
        pytest.skip("dictionary not built on this machine")
    with open(service._DICTIONARY_JSON, encoding="utf-8") as f:
        entries = json.load(f)

    service.load_dictionary()
    slots = [word for e in entries for words in e.get("synonyms", []) for word in words]
    explained = sum(bool(service.meaning_of(word))
                for word in slots)

    assert slots, "the shipped dictionary lists no synonyms at all"
    assert explained / len(slots) > 0.7, f"only {explained} of {len(slots)} carry a meaning"


def test_a_search_hands_back_synonyms_in_the_new_shape():
    """The whole point, through the front door the API uses."""
    if not service._DICTIONARY_JSON.exists():
        pytest.skip("dictionary not built on this machine")
    seen = 0
    for entry in service.search_arabic("كتب", limit=10):
        for words in entry.get("synonyms", []):
            for synonym in words:
                assert set(synonym) == {"word", "meaning"}, synonym
                seen += 1
    # Without this the test passes on a search that returned no synonyms at all,
    # which is exactly the failure it exists to catch.
    assert seen, "no synonyms came back, so the shape was never checked"
