"""The book's closed word lists and the teacher's checks (a leaf module: rule_engine and syntax both read it), loaded once from data/nahw_rules/closed_words.json and teacher.json."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

RULES = Path(__file__).parent.parent / "data" / "nahw_rules"
FILE = RULES / "closed_words.json"
TEACHER_FILE = RULES / "teacher.json"


@lru_cache(maxsize=1)
def _families() -> dict:
    return json.loads(FILE.read_text(encoding="utf-8"))["families"]


@lru_cache(maxsize=1)
def vetoes() -> dict[str, bool]:
    """Which link vetoes are switched on (see services/syntax/mask.py)."""
    data = json.loads(FILE.read_text(encoding="utf-8"))["vetoes"]
    return {k: v for k, v in data.items() if not k.startswith("_")}


def words(family: str, part: str = "words") -> frozenset[str]:
    """One list of a family: its `words`, or another list it keeps (`nouns`, `needs_ma`...)."""
    return frozenset(_families()[family][part])


def is_one(lemma: str, family: str, part: str = "words") -> bool:
    """True when the parser's lemma (an attached clitic's '+' aside) is on that list."""
    return lemma.strip("+") in words(family, part)


@lru_cache(maxsize=1)
def teacher() -> dict:
    """The teacher's checks and their reasons (services/syntax/teacher.py)."""
    return json.loads(TEACHER_FILE.read_text(encoding="utf-8"))
