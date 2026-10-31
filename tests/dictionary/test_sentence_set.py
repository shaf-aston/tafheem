"""The dictionary's sentence reading over its 1000-input yardstick (data/dictionary/sentence_set.json):
nothing breaks, every input gets one row per typed word and a prompt line per row, a text asks
the model once, and no count falls below its baseline. The scoring itself is
backend/scripts/dictionary/score_sentences.py, the same one a person runs by hand."""
from __future__ import annotations

import json

import pytest

from backend.scripts.dictionary import score_sentences as yardstick
from backend.services.dictionary import sentence_meaning
from tests.nahw_helpers import needs_parser

pytestmark = needs_parser


@pytest.fixture(scope="module")
def scored() -> dict:
    return yardstick.score(yardstick.load_set()["inputs"])


def test_the_set_is_a_thousand_texts_each_once():
    inputs = yardstick.load_set()["inputs"]
    assert len(inputs) == 1000
    assert len({e["ar"] for e in inputs}) == 1000


def test_no_count_falls_below_its_baseline(scored):
    """The baseline holds broke 0, aligned 1000 and facts 1000, so this is also: nothing breaks,
    every input has a row per typed word and a prompt line per row."""
    baseline = json.loads(yardstick.BASELINE.read_text(encoding="utf-8"))
    assert yardstick.worse({"set": scored}, {"set": baseline["set"]}) == []


def test_a_text_asks_the_model_once_then_reads_what_was_filed():
    sample = [e["ar"] for e in yardstick.load_set()["inputs"][::100]]
    with yardstick.offline() as handed:
        first = [sentence_meaning.translate(text)["meaning"] for text in sample]
        again = [sentence_meaning.translate(text)["meaning"] for text in sample]
    assert len(handed) == len(sample)
    assert first == again == ["-"] * len(sample)


def test_worse_names_a_count_that_went_the_wrong_way():
    baseline = {"set": {"covered": 10, "junk": 2}}
    assert yardstick.worse({"set": {"covered": 10, "junk": 2}}, baseline) == []
    assert yardstick.worse({"set": {"covered": 9, "junk": 2}}, baseline) == ["set.covered: 9, was 10"]
    assert yardstick.worse({"set": {"covered": 11, "junk": 3}}, baseline) == ["set.junk: 3, was 2"]


def test_content_words_meet_across_endings_and_drop_filler():
    assert yardstick.content("The praises (of) Allah") == {"prais", "allah"}
    assert yardstick.content("praise") & yardstick.content("praises")
