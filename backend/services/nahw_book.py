"""The book's closed word lists and the teacher's checks (a leaf module: rule_engine and syntax both read it), loaded once from data/nahw_rules/closed_words.json and teacher.json."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

RULES = Path(__file__).parent.parent / "data" / "nahw_rules"
FILE = RULES / "closed_words.json"
TEACHER_FILE = RULES / "teacher.json"

# a pronoun, pointer, relative or question word keeps one ending whatever its job
MABNI_KINDS = ("pron", "dem", "rel", "interrog")


@lru_cache(maxsize=1)
def _closed() -> dict:
    return json.loads(FILE.read_text(encoding="utf-8"))


def vetoes() -> dict[str, bool]:
    """Which link vetoes are switched on (see services/syntax/mask.py)."""
    return {k: v for k, v in _closed()["vetoes"].items() if not k.startswith("_")}


@lru_cache(maxsize=None)
def book_words(family: str, part: str = "words") -> frozenset[str]:
    """One list of a family: its `words`, or another list it keeps (`nouns`, `needs_ma`...)."""
    return frozenset(_closed()["families"][family][part])


def is_one(lemma: str, family: str, part: str = "words") -> bool:
    """True when the parser's lemma (an attached clitic's '+' aside) is on that list."""
    return lemma.strip("+") in book_words(family, part)


def is_mabni(token: dict) -> bool:
    """A pronoun, pointer, relative or question word: its ending is not a case."""
    return any(kind in token.get("pos_camel", "") for kind in MABNI_KINDS)


def is_plain_noun(token: dict) -> bool:
    """A noun that can take a case ending."""
    return token["pos"] in ("NOM", "PROP") and not is_mabni(token)


@lru_cache(maxsize=1)
def teacher_rules() -> dict:
    """The teacher's checks and their reasons (services/syntax/teacher.py)."""
    return json.loads(TEACHER_FILE.read_text(encoding="utf-8"))
