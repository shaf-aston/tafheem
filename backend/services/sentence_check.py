"""Is every word of a sentence one the learner has learnt?

A plain program, not AI: it checks what the AI wrote. A word passes when its
letters, or its dictionary form (lemma), match a learnt word's spelling or
Qur'an lemma. Tashkeel and spelling variants are folded away for the lookup.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.config import get_settings
from backend.services import morphology
from backend.services.arabic_text import alef_written_out, words

WORDS = Path(__file__).parent.parent.parent / "frontend" / "public" / "words" / "words.json"
COVERAGE = WORDS.with_name("coverage.json")

fold = alef_written_out


def lemma_of(word: str) -> str | None:
    """The dictionary form, from whichever analyser is installed."""
    return morphology.analyze_word(word).get("lemma") or None


def check(sentence: str, allowed: set[str], lemma_of=lemma_of) -> list[str]:
    """The words that are not learnt; empty means the sentence passes."""
    free = {fold(word) for word in get_settings().sentence_free_words}
    bad = []
    for word in words(sentence):
        if fold(word) in free | allowed:
            continue
        lemma = lemma_of(word)
        if lemma is None or fold(lemma) not in allowed:
            bad.append(word)
    return bad


@lru_cache(maxsize=1)
def _table() -> tuple[list[dict], list[str]]:
    return (json.loads(WORDS.read_text("utf-8"))["words"],
            json.loads(COVERAGE.read_text("utf-8"))["lemmas"])


def learnt_words(meaning_keys: list[str]) -> list[dict]:
    """The quiz's words behind these meaningKeys."""
    keys = set(meaning_keys)
    return [word for word in _table()[0] if word["meaningKey"] in keys]


def allowed(learnt: list[dict]) -> set[str]:
    """Every folded spelling and Qur'an lemma the learnt words bring."""
    lemmas = _table()[1]
    return {fold(word["ar"]) for word in learnt} | {
        fold(lemmas[at]) for word in learnt for at in word.get("lemmas", ())
    }
