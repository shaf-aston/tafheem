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

from backend.services.arabic_text import bare_letters
from backend.services.nahw_book import is_one, teacher
from backend.services.syntax.naming import (
    base_tokens, family_of, is_passive, is_verb, takes_tamyeez, typed_case)

DOERS = ("فاعل", "نائب فاعل")
SUBJECTS = ("مبتدأ", "اسم كان", "اسم إن", "اسم كاد")
FOLLOWERS = ("معطوف", "توكيد", "صفة", "بدل")
# a pronoun, pointer, relative or question word keeps one ending whatever its job
MABNI = ("pron", "dem", "rel", "interrog")


def _is_noun(token: dict) -> bool:
    return token["pos"] in ("NOM", "PROP") and not is_verb(token)


def _kids(token: dict, bases: list[dict]) -> list[int]:
    return [i for i, b in enumerate(bases) if b["head"] == token["id"]]


def _one_subject(bases, tokens, roles):
    """Two words claiming to be the same verb's doer: neither can be trusted."""
    for verb in filter(is_verb, bases):
        doers = [i for i in _kids(verb, bases) if roles[i] in DOERS]
        if len(doers) > 1:
            yield from doers


def _passive_has_no_doer(bases, tokens, roles):
    for verb in filter(is_verb, bases):
        if is_passive(verb):
            yield from (i for i in _kids(verb, bases) if roles[i] == "فاعل")


def _expected_case(role: str, token: dict, bases: list[dict], cases: dict) -> str | None:
    for case in "uai":
        if role in cases[case]:
            return case
    if role in cases["a_when_mudaf"] and any(b["rel"] == "IDF" for b in bases if b["head"] == token["id"]):
        return "a"
    return None


def _typed_case_fits_role(bases, tokens, roles):
    cases = teacher()["case_of_role"]
    by_id = {t["id"]: t for t in tokens}
    for i, (token, role) in enumerate(zip(bases, roles)):
        want = _expected_case(role or "", token, bases, cases)
        shown = typed_case(token.get("typed"), token.get("stuck_on", 0))
        if not want or not shown or shown == want or is_verb(token):
            continue
        # the noun of لا is raf' when the لا works like ليس (لا رجلٌ في الدار), so its ending is open
        if role == "اسم إن" and is_one(by_id.get(token["head"], {}).get("lemma", ""), "la_jins"):
            continue
        if any(kind in token.get("pos_camel", "") for kind in MABNI):
            continue
        bare = bare_letters(token.get("typed") or "")
        # a sound feminine plural takes kasra for nasb too (رأيت المعلماتِ), and a
        # diptote takes fatha for jarr (مررت بأحمدَ): both look like a clash and are not
        if want == "a" and shown == "i" and bare.endswith("ات"):
            continue
        if want == "i" and shown == "a" and token.get("stt") == "i" and not bare.startswith("ال") \
                and not any(roles[k] == "مضاف إليه" for k in _kids(token, bases)):
            continue
        yield i


def _khabar_needs_mubtada(bases, tokens, roles):
    if not any(role in SUBJECTS for role in roles):
        yield from (i for i, role in enumerate(roles) if role == "خبر")


def _ism_inna_needs_inna(bases, tokens, roles):
    has_inna = any(family_of(t, tokens) == "inna" for t in tokens)
    if not has_inna:
        yield from (i for i, role in enumerate(roles) if role == "اسم إن")


def _follower_needs_noun(bases, tokens, roles):
    """A follower copies a noun, so some noun (a pointer like هذا counts) must come before it."""
    for i, (token, role) in enumerate(zip(bases, roles)):
        if role in FOLLOWERS and not any(_is_noun(t) for t in tokens if t["id"] < token["id"]):
            yield i


def _tamyeez_needs_number(bases, tokens, roles):
    for i, (token, role) in enumerate(zip(bases, roles)):
        if role != "تمييز":
            continue
        if not takes_tamyeez(token, tokens):
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
    rules = teacher()["checks"]
    caught: dict[int, str] = {}
    for rule, check in CHECKS.items():
        if rules[rule]["on"]:
            for i in list(check(bases, tokens, roles)):
                caught.setdefault(i, rule)
            # the next check reads the sentence without the words already doubted:
            # a khabar whose mubtada was just dashed has lost its mubtada
            roles = [None if i in caught else role for i, role in enumerate(roles)]
    return [{**entry, "role": None, "gap": {"ar": rules[caught[i]]["ar"], "en": rules[caught[i]]["en"]}}
            if i in caught else entry for i, entry in enumerate(found)]
