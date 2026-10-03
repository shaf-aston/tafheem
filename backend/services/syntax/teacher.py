"""The teacher's second reading of a finished sentence.

`naming` gives every word a job; this module re-reads the whole set against the
rules a nahw book states outright (one doer per verb, the vowel matches the job,
a khabar has its mubtada...). A word whose job breaks one is not given a
different guess: it loses its name and is drawn as a gap, with the rule that
caught it, because a dash is better than a confident wrong name.

Pure: tokens and roles in, roles out. Which checks run, and the reason each one
gives, live in data/nahw_rules/teacher.json.
"""
from __future__ import annotations

from backend.services.arabic_text import bare_letters, strip_diacritics
from backend.services.nahw_book import case_of, is_mabni, is_one, named_roles, teacher_rules
from backend.services.syntax.facts import Sentence, is_called_noun, is_passive, is_verb, takes_tamyeez, typed_case_of
from backend.services.syntax.naming import base_tokens, roles_keyed
from backend.services.harakat import CASE_NAME

# the role groups are the card's colour keys (data/nahw_rules/roles.json), so a new role joins its group there
NAMED = named_roles()
DOERS = roles_keyed("fail")
SUBJECTS = roles_keyed("mubtada")
FOLLOWERS = roles_keyed("tabi", "sifah")


def _is_noun(token: dict) -> bool:
    """Unlike `nahw_book.is_plain_noun` a pointer counts: هذا can be copied by a follower,
    and so does the called أيها, which the parser tags a particle."""
    return (token["pos"] in ("NOM", "PROP") and not is_verb(token)) or is_called_noun(token)


def _kid_indices(token: dict, bases: list[dict]) -> list[int]:
    return [i for i, b in enumerate(bases) if b["head"] == token["id"]]


def _one_subject(bases, tokens, roles):
    """Two words claiming to be the same verb's doer: neither can be trusted."""
    for verb in filter(is_verb, bases):
        doers = [i for i in _kid_indices(verb, bases) if roles[i] in DOERS]
        if len(doers) > 1:
            yield from doers


def _passive_has_no_doer(bases, tokens, roles):
    for verb in filter(is_verb, bases):
        if is_passive(verb):
            yield from (i for i in _kid_indices(verb, bases) if roles[i] == NAMED.fail)


def _expected_case(role: str, mudaf: bool, cases: dict) -> str | None:
    return case_of(role) or ("a" if mudaf and role in cases["a_when_mudaf"] else None)


def _vowel_facts(token: dict, bases: list[dict], roles: list, by_id: dict) -> dict:
    """What decides whether the vowel typed on a word can be held against its job.

    `free` lists the (wanted, typed) case pairs that only look like a clash ("au":
    wanted nasb, typed damma); "*" frees all of them. Kept on a word the parser
    left unnamed, so `fallback_gap` judges the rule engine's name by the same facts."""
    bare = bare_letters(token.get("typed") or "")
    free = set()
    # a pronoun, pointer, relative or question word keeps one ending whatever its job
    if is_mabni(token):
        free.add("*")
    # the noun of لا is raf' when the لا works like ليس (لا رجلٌ في الدار), so its ending is open
    if is_one(by_id.get(token["head"], {}).get("lemma", ""), "la_jins"):
        free |= {"au", "ai"}
    # a sound feminine plural takes kasra for nasb too (رأيت المعلماتِ), and a
    # diptote takes fatha for jarr (مررت بأحمدَ): both look like a clash and are not
    if bare.endswith("ات"):
        free.add("ai")
    mudaf_ilayh = any(roles[k] == NAMED.mudaf_ilayh for k in _kid_indices(token, bases))
    if token.get("stt") == "i" and not bare.startswith("ال") and not mudaf_ilayh:
        free.add("ia")
    return {"free": sorted(free), "mudaf": any(b["rel"] == "IDF" for b in bases if b["head"] == token["id"])}


def _clashes(role: str | None, shown: str | None, ending: dict) -> bool:
    """The one test of a typed ending against a role: `shown` is u / a / i, or None when bare."""
    want = _expected_case(role or "", ending["mudaf"], teacher_rules()["case_of_role"])
    return bool(want and shown and shown != want
                and "*" not in ending["free"] and want + shown not in ending["free"])


def _typed_case_fits_role(bases, tokens, roles):
    by_id = {t["id"]: t for t in tokens}
    for i, (token, role) in enumerate(zip(bases, roles)):
        shown = typed_case_of(token)
        if not is_verb(token) and _clashes(role, shown, _vowel_facts(token, bases, roles, by_id)):
            yield i


def _khabar_needs_mubtada(bases, tokens, roles):
    if not any(role in SUBJECTS for role in roles):
        yield from (i for i, role in enumerate(roles) if role == NAMED.khabar)


def _ism_inna_needs_inna(bases, tokens, roles):
    s = Sentence(tokens)
    has_inna = any(s.family(t) == "inna" for t in tokens)
    if not has_inna:
        yield from (i for i, role in enumerate(roles) if role == NAMED.ism_inna)


def _follower_needs_noun(bases, tokens, roles):
    """A follower copies a noun, so some noun (a pointer like هذا counts) must come before it."""
    for i, (token, role) in enumerate(zip(bases, roles)):
        if role in FOLLOWERS and not any(_is_noun(t) for t in tokens if t["id"] < token["id"]):
            yield i


def _tamyeez_needs_number(bases, tokens, roles):
    s = Sentence(tokens)
    for i, (token, role) in enumerate(zip(bases, roles)):
        if role == NAMED.tamyeez and not takes_tamyeez(token, s):
            yield i


CHECKS = {
    "one_subject": _one_subject,
    "passive_has_no_doer": _passive_has_no_doer,
    "typed_case_fits_role": _typed_case_fits_role,
    "khabar_needs_mubtada": _khabar_needs_mubtada,
    "ism_inna_needs_inna": _ism_inna_needs_inna,
    "follower_needs_noun": _follower_needs_noun,
    "tamyeez_needs_number": _tamyeez_needs_number,
}


def review(words: list[str], tokens: list[dict], found: list[dict]) -> list[dict]:
    """`found` (what `naming.roles` returned) with each word that breaks a rule
    turned into a gap: role None, and `gap` = the rule's reason in Arabic and English."""
    bases = base_tokens(words, tokens)
    if len(bases) != len(found):
        return found
    roles = [entry["role"] for entry in found]
    rules = teacher_rules()["checks"]
    caught: dict[int, str] = {}
    for rule, check in CHECKS.items():
        if rules[rule]["on"]:
            for i in list(check(bases, tokens, roles)):
                caught.setdefault(i, rule)
            # the next check reads the sentence without the words already doubted:
            # a khabar whose mubtada was just dashed has lost its mubtada
            roles = [None if i in caught else role for i, role in enumerate(roles)]
    roles = [None if i in caught else role for i, role in enumerate(roles)]
    by_id = {t["id"]: t for t in tokens}
    return [{**entry, "role": None, "gap": {"ar": rules[caught[i]]["ar"], "en": rules[caught[i]]["en"]}}
            if i in caught else
            {**entry, "ending": _vowel_facts(bases[i], bases, roles, by_id)} if entry["role"] is None else entry
            for i, entry in enumerate(found)]


def fallback_gap(role: str | None, found: dict) -> dict | None:
    """The same typed-vowel check for a name the rule engine supplied where naming had
    none: the teacher never saw that role, so a typed fatha on a "mubtada" slipped by.
    `found` is the parser's entry for the word, its `case` the ending as the card prints
    it (raf' / nasb / jarr) and its `ending` the facts `review` left on it."""
    rule = teacher_rules()["checks"]["typed_case_fits_role"]
    plain = strip_diacritics(role or "").split(" (")[0].strip()
    shown = next((k for k, v in CASE_NAME.items() if v == found["case"]), None)
    if rule["on"] and found.get("ending") and _clashes(plain, shown, found["ending"]):
        return {"ar": rule["ar"], "en": rule["en"]}
    return None
