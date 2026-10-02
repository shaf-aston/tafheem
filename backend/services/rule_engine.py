"""Deterministic Nahw rule engine for Arabic I'raab analysis.

Converts morphological tags (from morphology.py) into a structured I'raab
result using classical grammar rules, no API call needed.

Coverage:
  * fi'l, fa'il / na'ib fa'il, maf'ul bihi  (jumlah fi'liyyah)
  * mubtada, khabar                          (jumlah ismiyyah)
  * inna and sisters  (ism mansub / khabar marfu')
  * harf jarr + majrur
  * sifah / na't
  * harf 'atf (conjunctions)

The words a card prints (signs, reasons, what a past verb is built on) are the
book's, in data/nahw_rules/teacher.json; this file only decides which to use.
"""
from __future__ import annotations

import logging
from typing import Any

from backend.services.arabic_text import strip_diacritics
from backend.services.nahw_book import book_words, case_of, reason, teacher_rules
from backend.services.syntax.vowels import CASE_NAME, SUKUN, letters, typed_case
from backend.services.tarkeeb import term_ar

logger = logging.getLogger(__name__)

# Every entry below carries a `role_key` beside its Arabic role: the stable name
# the word grid colours by, the same idea as a tarkeeb node's `tone`. The names
# themselves are the contract's, `schemas.ROLE_KEYS`, and
# tests/test_rule_engine.py holds the two lists together.

# CAMeL POS tags for inna/sisters (conj_sub = subordinating conjunction)
_INNA_POS = {"conj_sub", "part_focus"}

# CAMeL POS tags for prepositions
_JARR_POS = {"prep"}

# ── Case signs ────────────────────────────────────────────────────────────────


def sign(case: str | None, kind: str = "vowel") -> str | None:
    """The sign a card prints for a case; `kind` names the letter that shows it
    instead of a vowel (dual, sound_plural, five_verbs)."""
    return teacher_rules()["signs"][kind].get(case)


def resign(old_sign: str | None, case: str) -> str | None:
    """The sign for a new case, from the table the old sign came from, so a dual or a
    كِتَابِي keeps its kind of sign when the parser moves its case."""
    tables = {k: t for k, t in teacher_rules()["signs"].items() if not k.startswith("_")}
    kind = next((k for k, table in tables.items() if old_sign in table.values()), "vowel")
    return sign(case, kind) or sign(case)


def _noun_kind(tag: dict) -> str:
    """Which sign table a noun's case is read from."""
    num = tag.get("number")
    bare = strip_diacritics(tag.get("word", ""))
    if num == "p" and tag.get("gender") == "m" and bare.endswith(("ون", "ين")):
        return "sound_plural"
    if num == "d":
        return "dual"
    if tag.get("enclitic") == "1s_poss":
        return "before_ya"  # كِتَابِي: the kasra belongs to the ya, the case cannot show
    marked = letters(tag.get("word", ""))
    # no root read (key absent): the old test, a final ى is مقصور
    weak = tag.get("weak_last", bare.endswith("ى"))
    if bare.endswith(("ا", "ى")) and weak:
        return "on_alef"  # الفَتَى، العَصَا: an alef cannot carry a vowel (كِتَابًا's root ends in a strong letter)
    if "weak_last" in tag and weak and len(marked) > 1 and bare.endswith("ي") and not (
            marked[-1][1] & {"ّ"} or marked[-2][1] & {"َ", "ُ", "ّ", SUKUN}):
        return "manqus"  # القَاضِي: a damma or kasra is too heavy for the ya, the fatha shows
    return "vowel"


def _past_ending(word: str) -> str:
    """What a past verb is built on, from its last letters (teacher.json past_ending)."""
    bare = strip_diacritics(word)
    marked = letters(word)
    for ending, tails in teacher_rules()["past_ending"].items():
        if ending.startswith("_"):
            continue
        tail = next((t for t in tails if bare.endswith(t)), None)
        # كَتَبَتْ: a ت the reader closed with a sukun is تاء التأنيث, not a pronoun
        if tail and not (tail == "ت" and marked and SUKUN in marked[-1][1]):
            return ending
    return teacher_rules()["case_said"]["past_on"]


def _five_verbs(word: str, case: str) -> bool:
    """يكتبون، تكتبين، يكتبان (and يكتبوا، يكتبا، تكتبي once the nun is dropped): case by
    the nun. A damma typed on the nun makes it the verb's own letter (يَبِينُ), and a
    fatha on a last ي makes it a weak root letter (لن يَمْشِيَ), not the ya of تكتبي."""
    bare = strip_diacritics(word)
    shown = typed_case(word)
    if shown == "u" or len(bare) < 4:
        return False
    if case == "raf'":
        return bare.endswith(("ون", "ين", "ان"))
    return bare.endswith(("وا", "ا")) or (bare.startswith("ت") and bare.endswith("ي") and shown != "a")


def verb_card(word: str, aspect: str | None, case: str | None = None) -> dict:
    """Case, sign and reason of a verb by its tense, so the three always agree.
    syntax.with_parser_roles calls it again when the parser reads a word as a verb
    or the particle before a present verb settles its mood."""
    words = teacher_rules()["case_said"]
    tense = words["tense"].get(aspect)
    if aspect in ("p", "c"):
        built = words["built_on"].format(ending=_past_ending(word) if aspect == "p" else words["command_on"])
        return {"case": "mabni", "sign": built, "reason": f"{tense} {built}. {reason(tense)}"}
    if aspect == "i":
        case = case if case in teacher_rules()["signs"]["five_verbs"] else "raf'"
        return {"case": case, "sign": sign(case, "five_verbs" if _five_verbs(word, case) else "vowel"),
                "reason": f"{tense} {words['word'][case]}. {reason(tense)}"}
    return {"case": "mabni", "sign": sign("mabni"), "reason": reason("فعل")}


# ── Detection helpers ─────────────────────────────────────────────────────────

def _is_jarr_particle(tag: dict) -> bool:
    """True if the word is a preposition (harf jarr)."""
    pos = (tag.get("pos") or "").lower()
    if pos in _JARR_POS:
        return True
    return strip_diacritics(tag.get("word", "")) in book_words("jarr")


def _is_inna_sister(tag: dict) -> bool:
    """True if the word is إنّ or one of her sisters."""
    pos = (tag.get("pos") or "").lower()
    if pos in _INNA_POS:
        return True
    return strip_diacritics(tag.get("word", "")) in book_words("inna")


def _is_conjunction(tag: dict) -> bool:
    pos = (tag.get("pos") or "").lower()
    if pos == "conj":
        return True
    return strip_diacritics(tag.get("word", "")) in book_words("atf")


# ── Entry builders ────────────────────────────────────────────────────────────

def _entry(tag: dict, kind: str, role: str, key: str | None, case: str | None,
           sign_ar: str | None, reason_ar: str) -> dict:
    """One card, every field named once."""
    return {"word": tag["word"], "root": tag.get("root") or None, "type": kind, "role": role,
            "role_key": key, "case": case, "sign": sign_ar, "reason": reason_ar,
            "notes": tag.get("features") or "", "source": "rule_engine"}


def _harf_entry(tag: dict, role: str, why: str, key: str | None = "harf") -> dict:
    return _entry(tag, "harf", role, key, "mabni", sign("mabni"), reason(why))


def _verb_entry(tag: dict, key: str | None = "fil") -> dict:
    mood = {"s": "nasb", "j": "jazm"}.get(tag.get("mood"), "raf'")
    card = verb_card(tag.get("word", ""), tag.get("aspect"), mood)
    return _entry(tag, "fi'l", "فعل", key, card["case"], card["sign"], card["reason"])


def _noun_entry(tag: dict, role: str, key: str | None = None, why: str | None = None) -> dict:
    """A noun's card. A role with a case of its own (case_of_role) sets it; a follower
    keeps the one CAMeL or the typed vowel showed; a mabni word fills the place instead."""
    forced = case_of(role)
    case = CASE_NAME[forced] if forced else tag.get("case")
    mabni = case == "mabni"
    return _entry(tag, tag.get("type") or "ism", role, key, case,
                  sign(case, "vowel" if mabni else _noun_kind(tag)), reason(why or role, mabni=mabni))


def _pron_entry(tag: dict, role: str, why: str, key: str | None = None) -> dict:
    return _entry(tag, "damir", role, key, "mabni", sign("mabni"), reason(why))


def _unknown_entry(tag: dict) -> dict:
    return _entry(tag, tag.get("type") or "ism", "–", None, tag.get("case"), None, reason("–"))


# ── Main engine ───────────────────────────────────────────────────────────────

def with_engine_roots(words: list[dict[str, Any]], engine_words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The AI's word dicts, each carrying the analyzer's root instead of its own.

    A root is the analyzer's finding, not a thing to ask a language model for:
    it wrote "ل-م-" for لم and dropped roots at random between two runs of the
    same sentence. Matched on the bare word so a stray harakah does not unpair
    them; a word the analyzer never saw keeps no root rather than a guessed one.
    """
    roots = {strip_diacritics(w.get("word", "")): w.get("root") for w in engine_words}
    return [{**w, "root": roots.get(strip_diacritics(w.get("word", "")))} for w in words]


def analyze(sentence: str, tags: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Apply classical Nahw rules to produce an I'raab analysis.

    Returns::
        {
          "summary":    str,
          "words":      list[dict],
          "confidence": float,   # 0-1; routers use this to decide AI call
        }
    """
    if not tags:
        return {"summary": "", "words": [], "confidence": 0.0}

    is_inna_sentence = _is_inna_sister(tags[0])
    is_verbal = _detect_verbal_sentence(tags, is_inna_sentence)
    summary = sentence_type(is_verbal, is_inna_sentence)
    state = _init_state(is_verbal, is_inna_sentence)

    words, scores = [], []
    for i, tag in enumerate(tags):
        entry, score = _process_tag(tag, i, tags, state, is_verbal)
        if entry:
            words.append(entry)
            scores.append(score)

    confidence = round(sum(scores) / len(scores), 2) if scores else 0.0
    return {"summary": summary, "words": words, "confidence": confidence}


def _detect_verbal_sentence(tags: list[dict], is_inna: bool) -> bool:
    """Detect if sentence is verbal (fi'liyyah) or nominal (ismiyyah)."""
    if is_inna:
        return False
    first_pos = (tags[0].get("pos") or "").lower()
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
    """Initialize analysis state flags."""
    return {
        "after_jarr": False,
        "after_inna": is_inna,
        "ism_inna_done": False,
        "fail_done": not is_verbal,
        "mubtada_done": is_verbal,
        "khabar_done": is_verbal,
        "verb_done": not is_verbal,
    }


def _process_tag(
    tag: dict[str, Any], i: int, tags: list[dict], state: dict, is_verbal: bool
) -> tuple[dict | None, float]:
    """Process a single tag and return (entry, score) tuple."""
    pos = (tag.get("pos") or "").lower()

    if pos == "punc":
        return (_entry(tag, "punc", "–", None, None, None, "–"), 1.0)

    if _is_conjunction(tag):
        # لا العاطفة joins single words; before a verb it negates (لا يكذبُ) or forbids (لا تكذبْ)
        verb = tags[i + 1] if i + 1 < len(tags) and tags[i + 1].get("pos") == "verb" else None
        if verb and strip_diacritics(tag["word"]) == "لا":
            forbids = verb.get("mood") == "j" or verb["word"].endswith(SUKUN)
            return (_harf_entry(tag, "حرف", "لا ناهية" if forbids else "لا نافية"), 0.88)
        return (_harf_entry(tag, "حرف", "حرف عطف"), 0.88)

    if _is_jarr_particle(tag):
        state["after_jarr"] = True
        return (_harf_entry(tag, "حرف جر", "حرف جر"), 0.92)

    if _is_inna_sister(tag) and i == 0:
        state["after_inna"] = True
        return (_harf_entry(tag, "حرف", "حرف ناسخ"), 0.92)

    if pos in ("part", "det"):
        return (_harf_entry(tag, "حرف", "حرف"), 0.82)

    if pos == "pron":
        return _process_pronoun(tag, state, is_verbal)

    if pos == "verb":
        return _process_verb(tag, state)

    if pos in ("noun", "noun_prop", "adj", "adv", "abbrev", "unknown", ""):
        return _process_noun(tag, state, is_verbal, tags)

    return (_unknown_entry(tag), 0.30)


def _process_pronoun(tag: dict, state: dict, is_verbal: bool) -> tuple[dict, float]:
    """Process pronoun tag."""
    if state["after_jarr"]:
        state["after_jarr"] = False
        return (_pron_entry(tag, "مجرور", "مجرور ضمير", "harf"), 0.80)

    if is_verbal and not state["fail_done"]:
        state["fail_done"] = True
        return (_pron_entry(tag, "فاعل", "فاعل ضمير", "fail"), 0.75)

    return (_pron_entry(tag, "–", "ضمير", None), 0.60)


def _process_verb(tag: dict, state: dict) -> tuple[dict, float]:
    """Process verb tag; the first verb is the sentence's own, so it is surer."""
    first = not state["verb_done"]
    state["verb_done"] = True
    return (_verb_entry(tag), 0.88 if first else 0.65)


def _process_noun(tag: dict, state: dict, is_verbal: bool, tags: list[dict]) -> tuple[dict | None, float]:
    """Process noun/adjective/adverb tag."""
    pos = (tag.get("pos") or "").lower()

    if state["after_jarr"]:
        state["after_jarr"] = False
        return (_noun_entry(tag, "مجرور", "harf"), 0.88)

    if state["after_inna"] and not state["ism_inna_done"]:
        state["ism_inna_done"] = True
        state["after_inna"] = False
        return (_noun_entry(tag, "اسم إن", "mubtada"), 0.85)

    if state["ism_inna_done"] and not state["khabar_done"] and not is_verbal:
        state["khabar_done"] = True
        state["mubtada_done"] = True
        return (_noun_entry(tag, "خبر إن", "khabar"), 0.82)

    if state["ism_inna_done"] and state["khabar_done"] and not is_verbal:
        if pos == "adj":
            return (_noun_entry(tag, "خبر إن", "khabar", why="خبر إن ثانٍ"), 0.75)
        return (_noun_entry(tag, "–", None), 0.45)

    if is_verbal:
        return _process_noun_verbal(tag, state, tags, pos)

    return _process_noun_nominal(tag, state, pos)


def _process_noun_verbal(tag: dict, state: dict, tags: list[dict], pos: str) -> tuple[dict, float]:
    """Process noun in verbal sentence (jumlah fi'liyyah)."""
    if not state["fail_done"]:
        is_passive = any(t.get("voice") == "p" for t in tags if t.get("pos") == "verb")
        role = "نائب فاعل" if is_passive else "فاعل"
        state["fail_done"] = True
        return (_noun_entry(tag, role, "fail"), 0.80)

    if pos == "adj":
        return (_noun_entry(tag, "صفة", "sifah"), 0.72)

    return (_noun_entry(tag, "مفعول به", "mafool"), 0.75)


def _process_noun_nominal(tag: dict, state: dict, pos: str) -> tuple[dict, float]:
    """Process noun in nominal sentence (jumlah ismiyyah)."""
    if not state["mubtada_done"]:
        state["mubtada_done"] = True
        return (_noun_entry(tag, "مبتدأ", "mubtada"), 0.82)

    if not state["khabar_done"]:
        state["khabar_done"] = True
        return (_noun_entry(tag, "خبر", "khabar"), 0.78)

    if pos == "adj":
        return (_noun_entry(tag, "صفة", "sifah"), 0.68)

    return (_noun_entry(tag, "–", None), 0.45)
