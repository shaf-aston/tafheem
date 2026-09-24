"""Searching a word whose spelling carries a hamza.

Nobody types أَخَذَ with its hamza seat, and Wiktionary files its root as ءخذ,
which no keyboard types at all. Typed plainly as اخذ, the search used to miss
every one of those entries and fall through to a substring scan, where the
single letters ا, خ and ذ each sit inside the query: the screen answered a
search for "he took" with the alphabet.

So: fold hamza and alif together when matching, and never offer a scrap shorter
than a word as a partial match.
"""
from __future__ import annotations

import pytest

from backend.services import dictionary_service as service


@pytest.fixture
def took(monkeypatch):
    """Four entries, indexed exactly as load_dictionary() indexes them."""
    entries = [
        {"arabic": "أخذ", "root": "ءخذ", "definitions": ["to take"]},
        {"arabic": "مؤاخذة", "root": "ءخذ", "definitions": ["blame"]},
        {"arabic": "ا", "root": "", "definitions": ["the letter alif"]},
        {"arabic": "خ", "root": "", "definitions": ["the letter khaa"]},
    ]
    arabic, _ = service._build_indices(entries)
    monkeypatch.setattr(service, "_dictionary", entries)
    monkeypatch.setattr(service, "_arabic_index", arabic)
    monkeypatch.setattr(service, "_loaded", True)
    service._arabic_matches.cache_clear()
    yield entries
    service._arabic_matches.cache_clear()


def found(query: str) -> list[str]:
    return [entry["arabic"] for entry in service.search_arabic(query)]


def test_plain_alif_finds_the_hamza_word(took):
    assert found("اخذ")[0] == "أخذ"


def test_the_hamza_word_finds_itself(took):
    assert found("أخذ")[0] == "أخذ"


def test_the_root_brings_its_family(took):
    assert "مؤاخذة" in found("اخذ")


def test_single_letters_are_not_partial_matches(took):
    assert "ا" not in found("اخذ") and "خ" not in found("اخذ")


def test_a_single_letter_is_still_found_when_it_is_the_search(took):
    # The nearest case the bug report does not name: the cure for letters
    # crowding a word must not make the letters themselves unsearchable.
    assert found("ا") == ["ا"]
