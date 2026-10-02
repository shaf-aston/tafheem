"""The book's closed word lists, its roles and the teacher's checks (a leaf module: rule_engine and syntax both read it), loaded once from data/nahw_rules/closed_words.json, roles.json and teacher.json."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

RULES = Path(__file__).parent.parent / "data" / "nahw_rules"
FILE = RULES / "closed_words.json"
TEACHER_FILE = RULES / "teacher.json"
ROLES_FILE = RULES / "roles.json"

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


def book_map(family: str, part: str) -> dict[str, str]:
    """A family's word -> value table (the place a question noun fills, ...)."""
    return _closed()["families"][family][part]


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
def _roles() -> dict:
    return json.loads(ROLES_FILE.read_text(encoding="utf-8"))


def role_table() -> dict[str, tuple[str | None, str | None]]:
    """Every role the page can name, as (card colour key, bracket tone)."""
    return {role: (drawn["key"], drawn["tone"]) for role, drawn in _roles()["roles"].items()}


@lru_cache(maxsize=1)
def named_roles() -> SimpleNamespace:
    """The roles the code itself tests for, by id (`named_roles().mubtada`); roles.json spells them."""
    return SimpleNamespace(**_roles()["named"])


def clause_of(role: str | None) -> dict | None:
    """{job, case} of the verb clause hung on a word wearing this role, or None."""
    return _roles()["roles"].get(role, {}).get("clause_of")


def role_units() -> list[dict]:
    """The units a role heads in the bracket picture, in the order they are tested."""
    return _roles()["units"]


@lru_cache(maxsize=1)
def teacher_rules() -> dict:
    """The teacher's checks and their reasons (services/syntax/teacher.py)."""
    return json.loads(TEACHER_FILE.read_text(encoding="utf-8"))


def book_path(path: list[str], book: str) -> str:
    """The book's divisions a word was named through, below كلمة, with the leaf's section
    and page (`book` as the tree writes it, "3.1 p60"); فعل ← فعل is said once."""
    words = teacher_rules()["book_path"]
    said = [branch for i, branch in enumerate(path) if i and branch != path[i - 1]]
    section, page = book.split(" p")
    return words["said"].format(path=words["joint"].join(said), section=section, page=page)


def case_of(role: str) -> str | None:
    """u / a / i, the case a role takes (teacher.json case_of_role), or None for a
    follower or a role whose case depends on more than its name."""
    cases = teacher_rules()["case_of_role"]
    return next((case for case in "uai" if role in cases[case]), None)


def reason(role: str, mabni: bool = False) -> str:
    """The reason a card wearing this role shows; a role with no entry is just named, never
    given another role's text. A mabni word (الذي، هذا) fills the place of its case
    rather than wearing it, so its reason says so and keeps only the rule."""
    said = teacher_rules()["reasons"].get(role) or f"{role}."
    place = case_of(role)
    if not (mabni and place):
        return said
    words = teacher_rules()["case_said"]
    rule = said[said.find("القاعدة"):] if "القاعدة" in said else ""
    return f"{words['mabni_noun'].format(place=words['place'][place], role=role)}. {rule}".strip()
