"""Every word's card (type, case, reason) from CAMeL's tags: what the word is, never its job.

A card names only what the word itself shows: a verb, a particle (حرف جر، حرف عطف، لا
الناهية), a pronoun, a noun and the vowel typed on it. A noun's job (مبتدأ، فاعل،
مفعول به) needs the links between words, so only the book's tree names it
(syntax, then iraab.with_parser_roles); a word it leaves unnamed stays a gap, never
guessed by position. The sign is written last, once the case is final (signs.settle).
The words a card prints are the book's, in data/nahw_rules/teacher.json.
"""
from __future__ import annotations

from typing import Any

from backend.services.arabic_text import strip_diacritics
from backend.services import signs
from backend.services.harakat import PRESENT_PREFIX, SUKUN
from backend.services.nahw_book import book_words, reason, teacher_rules, term_ar

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


# ── Main engine ───────────────────────────────────────────────────────────────

def analyze(sentence: str, tags: list[dict[str, Any]]) -> dict[str, Any]:
    """{summary, words}: the sentence type and one card per word."""
    if not tags:
        return {"summary": "", "words": []}
    conditional = opens_condition(tags)
    is_inna = not conditional and _is(tags[0], "inna")
    summary = term_ar("jumlah_shartiyyah") if conditional else sentence_type(_opens_with_verb(tags, is_inna), is_inna)
    words = signs.settle([_card(tag, i, tags) for i, tag in enumerate(tags)])
    return {"summary": summary, "words": mark_condition(words) if conditional else words, "conditional": conditional}


def opens_condition(tags: list[dict]) -> bool:
    """إنْ with a verb straight after (إن كنتَ، إن تدرسْ): a condition, never إنّ, whose
    noun must come straight after it. The book's test, closed_words.json."""
    first = strip_diacritics(tags[0].get("word", ""))
    return (first in book_words("jazm", "conditional_particles")
            and len(tags) > 1 and tags[1].get("pos") == "verb")


def mark_condition(cards: list[dict]) -> list[dict]:
    """فعل الشرط on the first verb after the particle; جواب الشرط on the later verb the
    فاء ties to it (فاقبلها), else the next one in jazm (إن تدرسْ تنجحْ). Each is in
    jazm, or in its place when built (كُنْتَ). Runs after signs.settle wrote the reasons."""
    said = teacher_rules()["case_said"]["condition"]
    verbs = [card for card in cards[1:] if card.get("type") == "fi'l"]
    if not verbs:
        return cards
    tied = [card for card in verbs[1:] if _opened_by_fa(card)]
    answer = next(iter(tied), None) or next((card for card in verbs[1:] if card.get("case") == "jazm"), None)
    for card, part in ((verbs[0], "verb"), (answer, "answer")):
        if card is None:
            continue
        where = said["place"] if card.get("case") == "mabni" else said["jazm"]
        fa = f"{said['fa']}، " if card in tied else ""
        head, dot, rule = card["reason"].partition(". القاعدة")
        card["reason"] = f"{head}، {fa}{said[part]} {where}{dot}{rule}"
    return cards


def _opened_by_fa(card: dict) -> bool:
    """A joined فاء: the typed word opens with ف and its own word does not (فَاقْبَلْهَا, not فَتَحَ)."""
    base = strip_diacritics(card.get("camel", {}).get("base", ""))
    return strip_diacritics(card["word"]).startswith("ف") and not base.startswith("ف")


def _opens_with_verb(tags: list[dict], is_inna: bool) -> bool:
    """A verb first, or a particle then a verb (لم يكتب); the parser's names replace it."""
    if is_inna:
        return False
    first_pos = _pos(tags[0])
    return first_pos == "verb" or (len(tags) > 1 and first_pos in ("part", "det") and tags[1].get("pos") == "verb")


def sentence_type(is_verbal: bool, is_inna: bool) -> str:
    """The sentence type a summary prints, in the tree's own words (tarkeeb.json),
    so the line above the cards and the top of the picture say the same."""
    if is_verbal:
        return term_ar("jumlah_filiyyah")
    nominal = term_ar("jumlah_ismiyyah")
    return f"{nominal} · إنّ" if is_inna else nominal


def _card(tag: dict[str, Any], i: int, tags: list[dict]) -> dict:
    """One word's card by what the word is; a noun or a pronoun waits for its role."""
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
        return _harf_entry(tag, "حرف جر", "حرف جر")
    if i == 0 and opens_condition(tags):
        return _harf_entry(tag, "حرف", "حرف شرط")
    if _is(tag, "inna") and i == 0:
        return _harf_entry(tag, "حرف", "حرف ناسخ")
    if pos in ("part", "det"):
        return _harf_entry(tag, "حرف", "حرف")
    if pos == "pron":
        return _entry(tag, "damir", "–", None, "mabni", reason("ضمير"))
    if pos == "verb":
        return _verb_entry(tag)
    case = tag.get("case")
    return _entry(tag, tag.get("type") or "ism", "–", None, case, reason("–", mabni=case == "mabni"))
