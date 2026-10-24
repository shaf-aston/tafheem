"""Reading Wiktionary's synonym lists.

The rule that matters is alignment: synonyms[n] belongs to definitions[n]. A
list that slips by one would put نَقَشَ under "to write", a wrong answer that
looks exactly like a right one.
"""

import json
from pathlib import Path

import pytest

from backend.scripts.build_dictionary import OUTPUT, senses_of, synonyms_of


def _sense(gloss, *synonyms):
    return {"glosses": [gloss], "synonyms": [{"word": w} for w in synonyms]}


def test_a_synonym_is_read_off_the_sense_it_belongs_to():
    assert synonyms_of(_sense("to draw", "رَسَمَ", "خَطَّ"), "كتب") == ["رَسَمَ", "خَطَّ"]


def test_the_word_is_never_its_own_synonym():
    """Wiktionary builds these from thesaurus pages that list every member."""
    assert synonyms_of(_sense("desert", "صَحْرَاء", "بَيْدَاء"), "صحراء") == ["بَيْدَاء"]


def test_english_and_empty_entries_are_dropped_not_printed():
    assert synonyms_of(_sense("to write", "", "write", "خَطَّ"), "كتب") == ["خَطَّ"]


def test_the_same_synonym_twice_is_listed_once():
    assert synonyms_of(_sense("to write", "خَطَّ", "خَطَّ"), "كتب") == ["خَطَّ"]


def test_a_sense_with_no_synonyms_gets_an_empty_list_not_a_missing_one():
    definitions, synonyms = senses_of({"word": "كتب", "senses": [_sense("to write")]})
    assert definitions == ["to write"]
    assert synonyms == [[]]


def test_each_definition_keeps_its_own_synonyms():
    definitions, synonyms = senses_of({
        "word": "كتب",
        "senses": [_sense("to write", "خَطَّ"), _sense("to cut", "نَقَشَ")],
    })
    assert definitions == ["to write", "to cut"]
    assert synonyms == [["خَطَّ"], ["نَقَشَ"]]


def test_a_repeated_definition_does_not_shift_the_ones_after_it():
    """The duplicate gloss is skipped, so both lists must skip the same one."""
    definitions, synonyms = senses_of({
        "word": "كتب",
        "senses": [_sense("to write", "خَطَّ"), _sense("to write", "رَسَمَ"), _sense("to cut", "نَقَشَ")],
    })
    assert definitions == ["to write", "to cut"]
    assert synonyms == [["خَطَّ"], ["نَقَشَ"]]


built = pytest.mark.skipif(
    not Path(OUTPUT).is_file(), reason="dictionary not built, run scripts/build_dictionary.py"
)


@built
def test_the_shipped_dictionary_has_one_synonym_list_per_definition():
    entries = json.loads(Path(OUTPUT).read_text(encoding="utf-8"))
    slipped = [e["arabic"] for e in entries if len(e["synonyms"]) != len(e["definitions"])]
    assert not slipped, f"{len(slipped)} entries have their synonyms out of step: {slipped[:5]}"
