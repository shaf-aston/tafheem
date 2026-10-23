"""A rootless Wiktionary entry takes the root of the word it says it comes from.

Run: python -m pytest tests/test_dictionary_build_roots.py
"""
from __future__ import annotations

from backend.scripts.build_dictionary import fits, inherit_roots, root_of, source_words


def test_the_word_named_in_the_etymology_is_read_bare():
    entry = {"etymology_text": "Derived from the active participle of اِشْتَاقَ (ištāqa, “to long for”)."}
    assert source_words(entry) == ["اشتاق"]


def test_a_rootless_entry_takes_its_source_words_root():
    by_word = {"مشتاق": {"root": ""}, "اشتاق": {"root": "ش و ق"}}
    assert inherit_roots(by_word, {"مشتاق": ["اشتاق"]}) == 1
    assert by_word["مشتاق"]["root"] == "ش و ق"


def test_a_root_not_in_the_words_letters_is_not_taken():
    """إله is "a variant of" a word on another root: that root is not its own."""
    assert not fits("ن ف ق", "إحراق")
    assert fits("ق و ل", "قال")
    by_word = {"إحراق": {"root": ""}, "إنفاق": {"root": "ن ف ق"}}
    assert inherit_roots(by_word, {"إحراق": ["إنفاق"]}) == 0


def row(word: str, roots: list[str], forms: list[str] = (), sense_root: str = "") -> dict:
    """A dump row: its roots tagged, as Wiktionary does, on the page and on a sense."""
    tagged = [{"name": f"Arabic terms belonging to the root {r}"} for r in roots]
    sense = [{"name": f"Tunisian Arabic terms belonging to the root {sense_root}"}] if sense_root else []
    return {"word": word, "categories": tagged, "senses": [{"categories": sense}],
            "forms": [{"form": f, "tags": ["non-past"]} for f in forms] + [{"form": "inflected", "tags": ["plural"]}]}


def test_only_arabics_own_root_is_read():
    assert root_of(row("قال", ["ق و ل"], sense_root="ق ي ل")) == "ق و ل"


def test_of_two_roots_on_one_page_a_row_keeps_the_one_its_forms_spell():
    """قَالَ (say) and قَالَ (nap) share a page, and each row is handed both roots."""
    assert root_of(row("قال", ["ق ي ل", "ق و ل"], ["يَقُولُ", "قَوْل"])) == "ق و ل"
    assert root_of(row("زاد", ["ز و د", "ز ي د"], ["يَزِيدُ", "زِيَادَة"])) == "ز ي د"


def test_a_doubled_root_is_spelled_by_its_shadda_not_an_ending():
    entry = row("معتل", ["ع ل ي", "ع ل ل"])
    # The plural's ي is its ending, no radical: only the stems are read.
    entry["forms"] = [{"form": "مُعْتَلّ", "tags": ["canonical"]}, {"form": "مُعْتَلِّين", "tags": ["plural"]}]
    assert root_of(entry) == "ع ل ل"


def test_a_root_is_inherited_down_a_chain_of_source_words():
    by_word = {"مرتين": {"root": ""}, "مرة": {"root": ""}, "مر": {"root": "م ر ر"}}
    assert inherit_roots(by_word, {"مرتين": ["مرة"], "مرة": ["مر"]}) == 2
    assert by_word["مرتين"]["root"] == "م ر ر"
