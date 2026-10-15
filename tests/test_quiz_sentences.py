"""The everyday sentence shown under an answered word that has no ayah.

The card splits each sentence on its braces and marks the middle part, so a
sentence with no braces, or two pairs, would mark the wrong text. And a word
the file forgets simply shows nothing, which nobody would notice.
"""
from __future__ import annotations

import json
from pathlib import Path

WORDS = Path(__file__).resolve().parents[1] / "frontend" / "public" / "words"


def _load(name: str):
    return json.loads((WORDS / name).read_text("utf-8"))


def test_every_everyday_word_has_a_sentence():
    words = _load("words.json")["words"]
    everyday = {words[i]["ar"] for i in _load("cuts.json")["everyday"]}
    sentences = _load("sentences.json")["sentences"]
    assert sorted(everyday - set(sentences)) == []


def test_each_sentence_marks_one_word_and_has_english():
    for word, (arabic, english) in _load("sentences.json")["sentences"].items():
        assert arabic.count("{") == 1 and arabic.count("}") == 1, word
        assert arabic.index("{") < arabic.index("}") - 1, word
        assert english.strip() and "{" not in english, word
