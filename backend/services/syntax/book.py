"""The book's closed word lists, loaded once from data/nahw_rules/closed_words.json."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

FILE = Path(__file__).parent.parent.parent / "data" / "nahw_rules" / "closed_words.json"


@lru_cache(maxsize=1)
def _families() -> dict:
    return json.loads(FILE.read_text(encoding="utf-8"))["families"]


def words(family: str, part: str = "words") -> frozenset[str]:
    """One list of a family: its `words`, or another list it keeps (`nouns`, `needs_ma`...)."""
    return frozenset(_families()[family][part])


def is_one(lemma: str, family: str, part: str = "words") -> bool:
    """True when the parser's lemma (an attached clitic's '+' aside) is on that list."""
    return lemma.strip("+") in words(family, part)
