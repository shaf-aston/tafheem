"""Every word's card (type, role, case, reason) from CAMeL's tags, by fixed rule.

Its roles are a first guess by position; the parser's book-tree names replace them
wherever it has one (iraab.with_parser_roles). The sign is written last, once the
case is final (signs.settle). The words a card prints are the book's, in
data/nahw_rules/teacher.json; this file only decides which to use.
"""
from __future__ import annotations

from typing import Any

from backend.services.arabic_text import strip_diacritics
from backend.services import signs
from backend.services.harakat import CASE_NAME, PRESENT_PREFIX, SUKUN
from backend.services.nahw_book import book_words, case_of, reason, term_ar

# Every entry below carries a `role_key` beside its Arabic role: the stable name
# the word grid colours by, the same idea as a tarkeeb node's `tone`. The names
# themselves are the contract's, `schemas.ROLE_KEYS`, and
# tests/test_rule_engine.py holds the two lists together.

# CAMeL's tags for each particle family; a word on the family's list counts too
_FAMILY_POS = {"jarr": {"prep"}, "inna": {"conj_sub", "part_focus"}, "atf": {"conj"}}

# ── Verb case ─────────────────────────────────────────────────────────────────


def verb_card(base: str, aspect: str | None, case: str | None = None) -> dict:
    """A verb's tense and case: built for a past verb or a command, by its mood for a
    present one. iraab.with_parser_roles calls it again when the parser reads a word
    as a verb or the particle before a present verb settles its mood; signs.settle
    writes the sign and the reason from these. A "present" verb whose base word (its
    joined letters off) has no present prefix is a command (اِتَّقِ، read by CAMeL as
    يتقي's mood)."""
    if aspect == "i" and base[:1] not in PRESENT_PREFIX:
        aspect = "c"
    if aspect == "i":
        return {"aspect": aspect, "case": case if case in ("raf'", "nasb", "jazm") else "raf'"}
    return {"aspect": aspect, "case": "mabni"}


# ── Detection helpers ─────────────────────────────────────────────────────────

def _pos(tag: dict) -> str:
    return (tag.get("pos") or "").lower()


def _is(tag: dict, family: str) -> bool:
    """A preposition (jarr), إنّ or a sister (inna), or a joining word (atf)."""
    return _pos(tag) in _FAMILY_POS[family] or strip_diacritics(tag.get("word", "")) in book_words(family)


# ── Entry builders ────────────────────────────────────────────────────────────

def _entry(tag: dict, kind: str, role: str, key: str | None, case: str | None,
           reason_ar: str) -> dict:
    """One card, every field named once. `camel` is CAMeL's reading of the word, which
    signs.settle reads the sign from once the case is final; the page never shows it."""
    return {"word": tag["word"], "root": tag.get("root") or None, "type": kind, "role": role,
            "role_key": key, "case": case, "sign": None, "reason": reason_ar,
            "notes": tag.get("features") or "", "source": "rule_engine",
            "aspect": tag.get("aspect"), "camel": tag}


def _harf_entry(tag: dict, role: str, why: str) -> dict:
    return _entry(tag, "harf", role, "harf", "mabni", reason(why))


def _verb_entry(tag: dict) -> dict:
    mood = {"s": "nasb", "j": "jazm"}.get(tag.get("mood"), "raf'")
    return {**_entry(tag, "fi'l", "فعل", "fil", None, reason("فعل")),
            **verb_card(tag["base"], tag.get("aspect"), mood)}


def _noun_entry(tag: dict, role: str, key: str | None = None, why: str | None = None) -> dict:
    """A noun's card. A role with a case of its own (case_of_role) sets it; a follower
    keeps the one CAMeL or the typed vowel showed; a mabni word fills the place instead."""
    forced = case_of(role)
    case = CASE_NAME[forced] if forced else tag.get("case")
    mabni = case == "mabni"
    return _entry(tag, tag.get("type") or "ism", role, key, case, reason(why or role, mabni=mabni))


def _pron_entry(tag: dict, role: str, why: str, key: str | None = None) -> dict:
    return _entry(tag, "damir", role, key, "mabni", reason(why))


def _unknown_entry(tag: dict) -> dict:
    return _entry(tag, tag.get("type") or "ism", "–", None, tag.get("case"), reason("–"))


# ── Main engine ───────────────────────────────────────────────────────────────

def analyze(sentence: str, tags: list[dict[str, Any]]) -> dict[str, Any]:
    """{summary, words}: the sentence type and one card per word."""
    if not tags:
        return {"summary": "", "words": []}

    is_inna_sentence = _is(tags[0], "inna")
    is_verbal = _detect_verbal_sentence(tags, is_inna_sentence)
    summary = sentence_type(is_verbal, is_inna_sentence)
    state = _init_state(is_verbal, is_inna_sentence)

    words = [entry for i, tag in enumerate(tags) if (entry := _process_tag(tag, i, tags, state, is_verbal))]
    return {"summary": summary, "words": signs.settle(words)}


def _detect_verbal_sentence(tags: list[dict], is_inna: bool) -> bool:
    if is_inna:
        return False
    first_pos = _pos(tags[0])
    if first_pos == "verb":
        return True
    return (
        len(tags) > 1
        and first_pos in ("part", "det")
        and tags[1].get("pos") == "verb"
    )


def sentence_type(is_verbal: bool, is_inna: bool) -> str:
    """The sentence type a summary prints, in the tree's own words (tarkeeb.json),
    so the line above the cards and the top of the picture say the same."""
    if is_verbal:
        return term_ar("jumlah_filiyyah")
    nominal = term_ar("jumlah_ismiyyah")
    return f"{nominal} · إنّ" if is_inna else nominal


def _init_state(is_verbal: bool, is_inna: bool) -> dict[str, bool]:
    return {
        "after_jarr": False,
        "after_inna": is_inna,
        "ism_inna_done": False,
        "fail_done": not is_verbal,
        "mubtada_done": is_verbal,
        "khabar_done": is_verbal,
    }


def _process_tag(
    tag: dict[str, Any], i: int, tags: list[dict], state: dict, is_verbal: bool
) -> dict | None:
    """The rule engine's card for one word, or None for a word it drops."""
    pos = _pos(tag)

    if pos == "punc":
        return _entry(tag, "punc", "–", None, None, "–")

    if _is(tag, "atf"):
        # لا العاطفة joins single words; before a verb it negates (لا يكذبُ) or forbids (لا تكذبْ)
        verb = tags[i + 1] if i + 1 < len(tags) and tags[i + 1].get("pos") == "verb" else None
        if verb and strip_diacritics(tag["word"]) == "لا":
            forbids = verb.get("mood") == "j" or verb["word"].endswith(SUKUN)
            return _harf_entry(tag, "حرف", "لا ناهية" if forbids else "لا نافية")
        return _harf_entry(tag, "حرف", "حرف عطف")

    if _is(tag, "jarr"):
        state["after_jarr"] = True
        return _harf_entry(tag, "حرف جر", "حرف جر")

    if _is(tag, "inna") and i == 0:
        state["after_inna"] = True
        return _harf_entry(tag, "حرف", "حرف ناسخ")

    if pos in ("part", "det"):
        return _harf_entry(tag, "حرف", "حرف")

    if pos == "pron":
        return _process_pronoun(tag, state, is_verbal)

    if pos == "verb":
        return _verb_entry(tag)

    if pos in ("noun", "noun_prop", "adj", "adv", "abbrev", "unknown", ""):
        return _process_noun(tag, pos, state, is_verbal, tags)

    return _unknown_entry(tag)


def _process_pronoun(tag: dict, state: dict, is_verbal: bool) -> dict:
    if state["after_jarr"]:
        state["after_jarr"] = False
        return _pron_entry(tag, "مجرور", "مجرور ضمير", "harf")

    if is_verbal and not state["fail_done"]:
        state["fail_done"] = True
        return _pron_entry(tag, "فاعل", "فاعل ضمير", "fail")

    return _pron_entry(tag, "–", "ضمير", None)


def _process_noun(tag: dict, pos: str, state: dict, is_verbal: bool, tags: list[dict]) -> dict | None:
    if state["after_jarr"]:
        state["after_jarr"] = False
        return _noun_entry(tag, "مجرور", "harf")

    if state["after_inna"] and not state["ism_inna_done"]:
        state["ism_inna_done"] = True
        state["after_inna"] = False
        return _noun_entry(tag, "اسم إن", "mubtada")

    if state["ism_inna_done"] and not state["khabar_done"] and not is_verbal:
        state["khabar_done"] = True
        state["mubtada_done"] = True
        return _noun_entry(tag, "خبر إن", "khabar")

    if state["ism_inna_done"] and state["khabar_done"] and not is_verbal:
        if pos == "adj":
            return _noun_entry(tag, "خبر إن", "khabar", why="خبر إن ثانٍ")
        return _noun_entry(tag, "–", None)

    if is_verbal:
        return _process_noun_verbal(tag, state, tags, pos)

    return _process_noun_nominal(tag, state, pos)


def _process_noun_verbal(tag: dict, state: dict, tags: list[dict], pos: str) -> dict:
    if not state["fail_done"]:
        is_passive = any(t.get("voice") == "p" for t in tags if t.get("pos") == "verb")
        role = "نائب فاعل" if is_passive else "فاعل"
        state["fail_done"] = True
        return _noun_entry(tag, role, "fail")

    if pos == "adj":
        return _noun_entry(tag, "صفة", "sifah")

    return _noun_entry(tag, "مفعول به", "mafool")


def _process_noun_nominal(tag: dict, state: dict, pos: str) -> dict:
    if not state["mubtada_done"]:
        state["mubtada_done"] = True
        return _noun_entry(tag, "مبتدأ", "mubtada")

    if not state["khabar_done"]:
        state["khabar_done"] = True
        return _noun_entry(tag, "خبر", "khabar")

    if pos == "adj":
        return _noun_entry(tag, "صفة", "sifah")

    return _noun_entry(tag, "–", None)
