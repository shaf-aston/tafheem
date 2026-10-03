"""The book's rules as data (a leaf module: rule_engine, syntax and tarkeeb all read it).

Every file in data/nahw_rules is read once, by `book_file`: the closed word lists,
the roles, the teacher's checks, the naming tree and the bracket tree's vocabulary."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

RULES = Path(__file__).parent.parent / "data" / "nahw_rules"

# a pronoun, pointer, relative or question word keeps one ending whatever its job
MABNI_KINDS = ("pron", "dem", "rel", "interrog")


@lru_cache(maxsize=None)
def book_file(name: str) -> dict:
    """One file of data/nahw_rules, parsed once."""
    return json.loads((RULES / name).read_text(encoding="utf-8"))


def _closed() -> dict:
    return book_file("closed_words.json")


def vetoes() -> dict[str, bool]:
    """Which link vetoes are switched on (see services/syntax/mask.py)."""
    return _closed()["vetoes"]


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


def _roles() -> dict:
    return book_file("roles.json")


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


def teacher_rules() -> dict:
    """The teacher's checks and their reasons (services/syntax/teacher.py)."""
    return book_file("teacher.json")


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


# ── The bracket tree's vocabulary (tarkeeb.json): one wording for every tree ──

def tarkeeb_rules() -> dict:
    """The bracket tree's vocabulary: its terms, tones and treebank wording."""
    return book_file("tarkeeb.json")


def term(key: str) -> dict:
    """One grammatical term: the Arabic the diagram prints and the colour it uses."""
    term = tarkeeb_rules()["terms"][key]
    out = {"ar": term["ar"], "tone": term["tone"]}
    if "detail" in term:
        out["detail"] = term["detail"]
    return out


def shown(term: dict) -> dict:
    """A term as a node wears it: its wording, its colour and its note, if any."""
    return {"role": term["ar"], "tone": term["tone"],
            **({"detail": term["detail"]} if "detail" in term else {})}


def term_ar(key: str) -> str:
    """Just the Arabic of a term, for comparing against what a tree printed."""
    return tarkeeb_rules()["terms"][key]["ar"]


def relation_wording(relation: str | None) -> tuple[str, bool]:
    """What to call a treebank relation, and whether any of it is still unchecked wording.

    Three cases, in order: the app has a wording for the whole name; the name is
    "خبر / اسم" plus the word that governs it, so the frame is the app's and the
    governing word is spelled the app's way when it is one a book names; or
    nothing is known, and the treebank's own wording is used and said to be so,
    its wording beats no wording, but it must not read as a finished term.

    The recorded treebank and the rules below both name a governed word through
    this, so اِسْمُ إِنَّ is spelled one way whichever path drew it.
    """
    settings = tarkeeb_rules()["treebank"]
    if not relation:
        return "", False
    if known := settings["relation_terms"].get(relation):
        return known, False

    head, _, rest = relation.partition(" ")
    frame = settings["relation_frames"].get(head)
    if frame and rest:
        governor = settings["governors"].get(rest)
        return f"{frame} {governor or rest}", governor is None
    return relation, True


def relation_tone(relation: str | None) -> str:
    """A relation's colour: the first listed name it contains, else the default."""
    for needle, tone in tarkeeb_rules()["treebank"]["relation_tones"]:
        if relation and needle in relation:
            return tone
    return "default"
