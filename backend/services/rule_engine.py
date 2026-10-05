"""Every word's card (type, case, reason) from CAMeL's tags: what the word is, never its job.

A card names only what the word itself shows: a verb, a particle (حرف جر، حرف عطف، لا
الناهية), a pronoun, a noun and the vowel typed on it. A noun's job (مبتدأ، فاعل،
مفعول به) needs the links between words, so only the book's tree names it
(syntax, then iraab.cards); a word it leaves unnamed stays a gap, never guessed by
position. Neither the sign nor the sentence type is decided here: iraab.cards writes
the sign once the case is final, and the summary is the picture's own label.
The words a card prints are the book's, in data/nahw_rules/teacher.json.
"""
from __future__ import annotations

from typing import Any

from backend.services.arabic_text import strip_diacritics
from backend.services.harakat import PRESENT_PREFIX, SUKUN
from backend.services.nahw_book import MABNI_KINDS, book_words, condition_of, named_roles, reason, teacher_rules

# Every entry below carries a `role_key` beside its Arabic role: the stable name
# the word grid colours by, the same idea as a tarkeeb node's `tone`. The names
# themselves are the contract's, `schemas.ROLE_KEYS`, and
# tests/test_rule_engine.py holds the two lists together.

# CAMeL's tags for each particle family; a word on the family's list counts too
# the role a card wears until the book's tree names its job
UNNAMED = "–"
NAMED = named_roles()

_FAMILY_POS = {"jarr": {"prep"}, "inna": {"conj_sub", "part_focus"}, "atf": {"conj"}}

# ── Verb case ─────────────────────────────────────────────────────────────────


def verb_card(base: str, aspect: str | None, case: str | None = None) -> dict:
    """A verb's tense and case: built for a past verb or a command, by its mood for a
    present one. iraab.cards calls it again when the parser reads a word
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
    """A preposition (jarr), إنّ or a sister (inna), or a joining word (atf). The family's
    list names a particle by its letters, never a word the reader read as a pronoun,
    pointer, relative or question word: مَنْ the relative is not مِنْ, though they share letters."""
    return _pos(tag) in _FAMILY_POS[family] or (
        not any(kind in _pos(tag) for kind in MABNI_KINDS) and strip_diacritics(tag.get("word", "")) in book_words(family))


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
    return {**_entry(tag, "fi'l", NAMED.fil, "fil", None, reason(NAMED.fil)),
            **verb_card(tag["base"], tag.get("aspect"), mood)}


# ── Main engine ───────────────────────────────────────────────────────────────

def cards(tags: list[dict[str, Any]]) -> list[dict]:
    """One card per word by what the word is, before any job is named or sign written."""
    return [_card(tag, i, tags) for i, tag in enumerate(tags)]


def opens_condition(tags: list[dict]) -> dict | None:
    """A conditional particle with a verb straight after (إن كنتَ، لو جاء): the condition
    it opens, never إنّ, whose noun must come straight after it. closed_words.json."""
    if len(tags) < 2 or tags[1].get("pos") != "verb":
        return None
    return condition_of(strip_diacritics(tags[0].get("word", "")))


def mark_condition(cards: list[dict]) -> list[dict]:
    """فعل الشرط on the first verb after the particle; جواب الشرط on the later verb a tying
    letter joins to it (فاقبلها، لأمرتُ), else the next one in jazm (إن تدرسْ تنجحْ). Each is
    in jazm, or in the place its particle gives it when built (كُنْتَ). Runs after signs.settle."""
    frame = condition_of(strip_diacritics(cards[0]["word"]))
    said = teacher_rules()["case_said"]["condition"]
    own = said["by_family"][frame["family"]]
    verbs = [card for card in cards[1:] if card.get("type") == "fi'l"]
    if not verbs:
        return cards
    tie_of = {id(card): tie for card in verbs[1:] if (tie := _tied_by(card, own["ties"]))}
    answer = next((card for card in verbs[1:] if id(card) in tie_of), None) or next(
        (card for card in verbs[1:] if card.get("case") == "jazm"), None)
    for card, part in ((verbs[0], "verb"), (answer, "answer")):
        if card is None:
            continue
        where = said["jazm"] if card.get("case") == "jazm" else own["place"]
        tie = f"{own['ties'][tie_of[id(card)]]}، " if id(card) in tie_of else ""
        head, dot, rule = card["reason"].partition(". القاعدة")
        card["reason"] = f"{head}، {tie}{where.format(part=said[part])}{dot}{rule}"
    return cards


def _tied_by(card: dict, ties: dict) -> str | None:
    """The tying letter written onto a verb: the typed word opens with it and its own word
    does not (فَاقْبَلْهَا، لَأَمَرْتُ; not فَتَحَ)."""
    word = strip_diacritics(card["word"])
    base = strip_diacritics(card.get("camel", {}).get("base", ""))
    return next((tie for tie in ties if word.startswith(tie) and not base.startswith(tie)), None)


def _card(tag: dict[str, Any], i: int, tags: list[dict]) -> dict:
    """One word's card by what the word is; a noun or a pronoun waits for its role."""
    pos = _pos(tag)
    if pos == "punc":
        return _entry(tag, "punc", UNNAMED, None, None, UNNAMED)
    if i == 0 and (frame := opens_condition(tags)):  # before حرف عطف: لو comes tagged as one
        return _harf_entry(tag, NAMED.harf, frame["particle"])
    if _is(tag, "atf"):
        # لا العاطفة joins single words; before a verb it negates (لا يكذبُ) or forbids (لا تكذبْ)
        verb = tags[i + 1] if i + 1 < len(tags) and tags[i + 1].get("pos") == "verb" else None
        if verb and strip_diacritics(tag["word"]) == "لا":
            forbids = verb.get("mood") == "j" or verb["word"].endswith(SUKUN)
            return _harf_entry(tag, NAMED.harf, "لا ناهية" if forbids else "لا نافية")
        return _harf_entry(tag, NAMED.harf, "حرف عطف")
    if _is(tag, "jarr"):
        return _harf_entry(tag, NAMED.harf_jarr, NAMED.harf_jarr)
    if _is(tag, "inna") and i == 0:
        return _harf_entry(tag, NAMED.harf, "حرف ناسخ")
    if pos in ("part", "det"):
        return _harf_entry(tag, NAMED.harf, NAMED.harf)
    if pos == "pron":
        return _entry(tag, "damir", UNNAMED, None, "mabni", reason("ضمير"))
    if pos == "verb":
        return _verb_entry(tag)
    case = tag.get("case")
    return _entry(tag, tag.get("type") or "ism", UNNAMED, None, case, reason(UNNAMED, mabni=case == "mabni"))
