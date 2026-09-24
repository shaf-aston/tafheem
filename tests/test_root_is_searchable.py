"""A root on screen has to be a word you can search for.

Every tab shows the root and every tab offers to carry it somewhere: Define
searches the dictionary with it, In the Qur'an searches the corpus with it. So
the string shown and the string searched are the same string, and it was being
written three ways that no index holds. The tagger returned "ف-ه-م", Wiktionary
stores "ف ه م", and pressing Define on either searched for punctuation and came
back with the letter ف.

The meaning shown beside it comes from the dictionary now, so the card is the
first line of the entry that Define opens, rather than a lexicon label from the
tagger written for a parser.
"""
from __future__ import annotations

import json

import pytest

from backend.services import dictionary_service as service
from backend.services import morphology


def test_the_tagger_root_is_plain_letters():
    """'ktb' comes out as كتب, not ك-ت-ب."""
    assert morphology._bw_root_to_arabic("ktb") == "كتب"


def test_an_already_arabic_root_loses_its_separators_too():
    assert morphology._bw_root_to_arabic("ك-ت-ب") == "كتب"


def test_a_root_with_an_unknown_radical_is_still_no_root():
    """The gap stays a gap: '#' is a radical the database could not pin down."""
    assert morphology._bw_root_to_arabic("#.l.d") == ""


def test_the_dictionary_root_is_plain_letters(tmp_path, monkeypatch):
    """Wiktionary spells a root out, "ف ه م"; the entry that goes out does not."""
    written = [{"arabic": "فَهِمَ", "root": "ف ه م", "definitions": ["to understand"]}]
    path = tmp_path / "arabic_dictionary.json"
    path.write_text(json.dumps(written, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(service, "_DICTIONARY_JSON", path)
    monkeypatch.setattr(service, "_loaded", False)
    monkeypatch.setattr(service, "_dictionary", [])

    service.load_dictionary()

    assert service._dictionary[0]["root"] == "فهم"
    # And the index is keyed by it, so Define, which searches with exactly the
    # root it showed, finds the entry rather than nothing.
    assert service.search_arabic("فهم")


@pytest.fixture
def one_word(monkeypatch):
    entry = {"arabic": "فَهِمَ", "root": "فهم", "definitions": ["to understand", "to realise"]}
    monkeypatch.setattr(service, "_arabic_index", {"فهم": [entry]})
    monkeypatch.setattr(service, "_loaded", True)
    return entry


def test_the_meaning_is_the_dictionarys_first_sense(one_word):
    assert service.meaning_of("فهم") == "to understand"


def test_a_word_the_dictionary_does_not_hold_says_nothing(one_word):
    """Which is what leaves the router free to fall back to the tagger's gloss."""
    assert service.meaning_of("زهزه") == ""
