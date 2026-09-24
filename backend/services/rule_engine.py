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
"""
from __future__ import annotations

import logging
from typing import Any

from backend.services.arabic_text import strip_diacritics as _bare

logger = logging.getLogger(__name__)

# Every entry below carries a `role_key` beside its Arabic role: the stable name
# the word grid colours by, the same idea as a tarkeeb node's `tone`. The names
# themselves are the contract's, `schemas.ROLE_KEYS`, and
# tests/test_rule_engine.py holds the two lists together.

# ── Word-sets (stored bare) ───────────────────────────────────────────────────

_HUROOF_JARR_BARE = {
    "من",   # من
    "إلى",  # إلى
    "حتى",  # حتى
    "في",   # في
    "عن",   # عن
    "على",  # على
    "عند",  # عند
    "مع",   # مع
    "بعد",  # بعد
    "قبل",  # قبل
    "خلف",  # خلف
    "أمام",  # أمام
    "تحت",  # تحت
    "فوق",  # فوق
    "بين",  # بين
    "حول",  # حول
    "منذ",  # منذ
    "مذ",   # مذ
    "رب",   # رب
    "خلا",  # خلا
    "عدا",  # عدا
    "حاشا",  # حاشا
    "ب",   # ب
    "ل",   # ل
    "ك",   # ك
}

_INNA_SISTERS_BARE = {
    "إن",   # إن
    "أن",   # أن
    "كأن",  # كأن
    "لكن",  # لكن
    "ليت",  # ليت
    "لعل",  # لعل
}

_CONJUNCTIONS_BARE = {
    "و",   # و
    "ف",   # ف
    "ثم",  # ثم
    "أو",  # أو
    "أم",  # أم
    "لا",  # لا
    "بل",  # بل
    "لكن",  # لكن
    "حتى",  # حتى
}

# CAMeL POS tags for inna/sisters (conj_sub = subordinating conjunction)
_INNA_POS = {"conj_sub", "part_focus"}

# CAMeL POS tags for prepositions
_JARR_POS = {"prep"}

# ── Case signs ────────────────────────────────────────────────────────────────

_SIGNS: dict[tuple[str, str], tuple[str, str]] = {
    # Arabic only, like every other sign here: the term stands alone on the
    # page and the glossary carries the English.
    ("n", "s"): ("raf'",  "ضمة"),
    ("a", "s"): ("nasb",  "فتحة"),
    ("g", "s"): ("jarr",  "كسرة"),
    ("n", "d"): ("raf'",  "الألف، مثنى"),
    ("a", "d"): ("nasb",  "الياء، مثنى"),
    ("g", "d"): ("jarr",  "الياء، مثنى"),
    ("n", "p"): ("raf'",  "ضمة"),
    ("a", "p"): ("nasb",  "فتحة"),
    ("g", "p"): ("jarr",  "كسرة"),
}

# ── Detection helpers ─────────────────────────────────────────────────────────

def _is_jarr_particle(tag: dict) -> bool:
    """True if the word is a preposition (harf jarr)."""
    pos = (tag.get("pos") or "").lower()
    if pos in _JARR_POS:
        return True
    return _bare(tag.get("word", "")) in _HUROOF_JARR_BARE


def _is_inna_sister(tag: dict) -> bool:
    """True if the word is إنّ or one of her sisters."""
    pos = (tag.get("pos") or "").lower()
    if pos in _INNA_POS:
        return True
    return _bare(tag.get("word", "")) in _INNA_SISTERS_BARE


def _is_conjunction(tag: dict) -> bool:
    pos = (tag.get("pos") or "").lower()
    if pos == "conj":
        return True
    return _bare(tag.get("word", "")) in _CONJUNCTIONS_BARE


# ── Entry-builder helpers ─────────────────────────────────────────────────────

def _common(tag: dict) -> dict:
    return {"word": tag["word"], "root": tag.get("root") or None}


def _harf_entry(tag: dict, role: str, reason_ar: str, key: str | None = "harf") -> dict:
    return {
        **_common(tag),
        "type": "harf",
        "role": role,
        "role_key": key,
        "case": "mabni",
        "sign": "مبني لا محل له من الإعراب",  # مبني لا محل له من الإعراب
        "reason": reason_ar,
        "notes": tag.get("features") or "",
        "source": "rule_engine",
    }


def _verb_entry(tag: dict, role: str, reason_ar: str, key: str | None = "fil") -> dict:
    asp = tag.get("aspect", "na") or "na"
    mod = tag.get("mood", "i") or "i"

    if asp == "p":
        # Past: mabni
        w = _bare(tag.get("word", ""))
        ending = (
            "السكون"
            if w.endswith(
                ("ت", "نا", "تم", "تن", "تما")  # ت  # نا  # تم  # تن
            )
            else "الفتح"
        )
        return {
            **_common(tag),
            "type": "fi'l",
            "role": role,
            "role_key": key,
            "case": "mabni",
            "sign": f"مبني على {ending}",
            "reason": f"فعل ماضٍ مبني على {ending}. {reason_ar}",
            "notes": tag.get("features") or "",
            "source": "rule_engine",
        }

    elif asp == "i":
        mood_map = {
            "i": ("raf'",  "الضمة"),   # الضمة
            "s": ("nasb",  "الفتحة"),  # الفتحة
            "j": ("jazm",  "السكون"),  # السكون
        }
        case_label, sign_ar = mood_map.get(mod, ("raf'", "الضمة"))
        mood_labels = {"i": "مرفوع", "s": "منصوب", "j": "مجزوم"}
        ml = mood_labels.get(mod, "مرفوع")
        return {
            **_common(tag),
            "type": "fi'l",
            "role": role,
            "role_key": key,
            "case": case_label,
            "sign": f"{sign_ar} الظاهرة",
            "reason": f"فعل مضارع {ml}. {reason_ar}",
            "notes": tag.get("features") or "",
            "source": "rule_engine",
        }

    elif asp == "c":
        return {
            **_common(tag),
            "type": "fi'l",
            "role": role,
            "role_key": key,
            "case": "mabni",
            "sign": "مبني على السكون",
            "reason": f"فعل أمر مبني على السكون. {reason_ar}",
            "notes": tag.get("features") or "",
            "source": "rule_engine",
        }

    return {
        **_common(tag),
        "type": "fi'l",
        "role": role,
        "role_key": key,
        "case": "mabni",
        "sign": "مبني",
        "reason": reason_ar,
        "notes": tag.get("features") or "",
        "source": "rule_engine",
    }


def _noun_entry(tag: dict, role: str, reason_ar: str, key: str | None = None,
                force_case: str | None = None) -> dict:
    cas = force_case or tag.get("case_raw", "u") or "u"
    num = tag.get("number", "s") or "s"

    # Sound masculine plural heuristic
    bare_w = _bare(tag.get("word", ""))
    smp_endings = (
        "ون",   # ون
        "ين",   # ين
    )
    is_smp = (num == "p" and tag.get("gender") == "m"
              and any(bare_w.endswith(e) for e in smp_endings))

    if is_smp:
        smp = {
            "n": ("raf'", "الواو، جمع مذكر سالم"),
            "a": ("nasb", "الياء، جمع مذكر سالم"),
            "g": ("jarr", "الياء، جمع مذكر سالم"),
        }
        case_label, sign_label = smp.get(cas, (None, None))
    else:
        case_label, sign_label = _SIGNS.get((cas, num if num in ("s", "d") else "s"), (None, None))

    if not case_label:
        case_label = tag.get("case")
        sign_label = None

    return {
        **_common(tag),
        "type": tag.get("type") or "ism",
        "role": role,
        "role_key": key,
        "case": case_label,
        "sign": sign_label,
        "reason": reason_ar,
        "notes": tag.get("features") or "",
        "source": "rule_engine",
    }


def _pron_entry(tag: dict, role: str, reason_ar: str, key: str | None = None) -> dict:
    return {
        **_common(tag),
        "type": "damir",
        "role": role,
        "role_key": key,
        "case": "mabni",
        "sign": "مبني",
        "reason": reason_ar,
        "notes": tag.get("features") or "",
        "source": "rule_engine",
    }


def _unknown_entry(tag: dict) -> dict:
    return {
        **_common(tag),
        "type": tag.get("type") or "ism",
        "role": "–",
        "role_key": None,
        "case": tag.get("case"),
        "sign": None,
        "reason": "يحتاج إلى مزيد من التحليل",
        "notes": tag.get("features") or "",
        "source": "rule_engine",
    }


# ── Main engine ───────────────────────────────────────────────────────────────

def with_engine_roots(words: list[dict[str, Any]], engine_words: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The AI's word dicts, each carrying the analyzer's root instead of its own.

    A root is the analyzer's finding, not a thing to ask a language model for:
    it wrote "ل-م-" for لم and dropped roots at random between two runs of the
    same sentence. Matched on the bare word so a stray harakah does not unpair
    them; a word the analyzer never saw keeps no root rather than a guessed one.
    """
    roots = {_bare(w.get("word", "")): w.get("root") for w in engine_words}
    return [{**w, "root": roots.get(_bare(w.get("word", "")))} for w in words]


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
    """Return the sentence type label. The one place these words are written:
    services/syntax names the same three from the parser's own reading."""
    if is_verbal:
        return "jumlah fi'liyyah (جملة فعلية)"
    if is_inna:
        return "jumlah ismiyyah · إنّ (جملة اسمية)"
    return "jumlah ismiyyah (جملة اسمية)"


def _init_state(is_verbal: bool, is_inna: bool) -> dict[str, bool]:
    """Initialize analysis state flags."""
    return {
        "after_jarr": False,
        "after_inna": is_inna,
        "ism_inna_done": False,
        "fa3il_done": not is_verbal,
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
        return ({**_common(tag), "type": "punc", "role": "–", "role_key": None,
                 "case": None, "sign": None,
                 "reason": "–", "notes": "", "source": "rule_engine"}, 1.0)

    if _is_conjunction(tag):
        return (_harf_entry(tag, "harf 'atf (حرف عطف)", "حرف عطف مبني لا محل له من الإعراب"), 0.88)

    if _is_jarr_particle(tag):
        state["after_jarr"] = True
        return (_harf_entry(tag, "harf jarr (حرف جر)", "حرف جر مبني لا محل له من الإعراب"), 0.92)

    if _is_inna_sister(tag) and i == 0:
        state["after_inna"] = True
        return (_harf_entry(tag, "حرف إن وأخواتها (ناسخ)",
                           "حرف ناسخ مبني لا محل له من الإعراب، ينصب الاسم ويرفع الخبر"), 0.92)

    if pos in ("part", "det"):
        label = "أداة تعريف" if _bare(tag.get("word", "")) in ("ال", "الـ") else "حرف"
        return (_harf_entry(tag, label, "مبني لا محل له من الإعراب"), 0.82)

    if pos == "pron":
        return _process_pronoun(tag, state, is_verbal)

    if pos == "verb":
        return _process_verb(tag, state, is_verbal)

    if pos in ("noun", "noun_prop", "adj", "adv", "abbrev", "unknown", ""):
        return _process_noun(tag, state, is_verbal, tags)

    return (_unknown_entry(tag), 0.30)


def _process_pronoun(tag: dict, state: dict, is_verbal: bool) -> tuple[dict, float]:
    """Process pronoun tag."""
    if state["after_jarr"]:
        state["after_jarr"] = False
        return (_pron_entry(tag, "ضمير متصل في محل جر", "ضمير متصل مبني في محل جر", "harf"), 0.80)

    if is_verbal and not state["fa3il_done"]:
        state["fa3il_done"] = True
        return (_pron_entry(tag, "ضمير في محل رفع فاعل",
                           "ضمير مبني في محل رفع فاعل. القاعدة: الفاعل مرفوع", "fail"), 0.75)

    return (_pron_entry(tag, "ضمير (محله يُحدّس بالسياق)",
                       "ضمير مبني، محله من الإعراب يُحدّد بالسياق", None), 0.60)


def _process_verb(tag: dict, state: dict, is_verbal: bool) -> tuple[dict, float]:
    """Process verb tag."""
    if state["verb_done"]:
        return (_verb_entry(tag, "فعل (جملة فعلية فرعية)", "فعل في جملة فعلية"), 0.65)

    asp = tag.get("aspect", "na") or "na"
    roles = {
        "c": ("فعل أمر", "فعل أمر مبني على السكون"),
        "i": ("فعل مضارع", "فعل مضارع. القاعدة: الفعل المضارع معرب"),
        "p": ("فعل ماضٍ", "فعل ماضٍ. القاعدة: الفعل الماضي مبني"),
    }
    role, reason = roles.get(asp, ("فعل", "فعل"))

    state["verb_done"] = True

    return (_verb_entry(tag, role, reason), 0.88)


def _process_noun(tag: dict, state: dict, is_verbal: bool, tags: list[dict]) -> tuple[dict | None, float]:
    """Process noun/adjective/adverb tag."""
    pos = (tag.get("pos") or "").lower()

    if state["after_jarr"]:
        state["after_jarr"] = False
        return (_noun_entry(tag, "اسم مجرور",
                           "مجرور بحرف الجر السابق. القاعدة: الاسم بعد حرف الجر مجرور", "harf", force_case="g"), 0.88)

    if state["after_inna"] and not state["ism_inna_done"]:
        state["ism_inna_done"] = True
        state["after_inna"] = False
        return (_noun_entry(tag, "اسم إن (منصوب)",
                           "منصوب لأنه اسم إن. القاعدة: إن وأخواتها تنصب الاسم", "mubtada", force_case="a"), 0.85)

    if state["ism_inna_done"] and not state["khabar_done"] and not is_verbal:
        state["khabar_done"] = True
        state["mubtada_done"] = True
        return (_noun_entry(tag, "خبر إن (مرفوع)",
                           "مرفوع لأنه خبر إن. القاعدة: إن وأخواتها ترفع الخبر", "khabar", force_case="n"), 0.82)

    if state["ism_inna_done"] and state["khabar_done"] and not is_verbal:
        if pos == "adj":
            return (_noun_entry(tag, "خبر ثانٍ (مرفوع)",
                               "مرفوع لأنه خبر ثانٍ لإن. القاعدة: إن وأخواتها ترفع الخبر", "khabar", force_case="n"), 0.75)
        return (_noun_entry(tag, "اسم (يُحدّد بالسياق)", "يحتاج إلى تحليل سياقي أدق", None), 0.45)

    if is_verbal:
        return _process_noun_verbal(tag, state, tags, pos)

    return _process_noun_nominal(tag, state, pos)


def _process_noun_verbal(tag: dict, state: dict, tags: list[dict], pos: str) -> tuple[dict, float]:
    """Process noun in verbal sentence (jumlah fi'liyyah)."""
    if not state["fa3il_done"]:
        is_passive = any(t.get("voice") == "p" for t in tags if t.get("pos") == "verb")
        role = "نائب فاعل (مرفوع)" if is_passive else "فاعل (مرفوع)"
        reason = ("مرفوع لأنه نائب فاعل. القاعدة: نائب الفاعل مرفوع"
                 if is_passive else "مرفوع لأنه فاعل. القاعدة: الفاعل مرفوع بالضمة")
        state["fa3il_done"] = True
        return (_noun_entry(tag, role, reason, "fail", force_case="n"), 0.80)

    if pos == "adj":
        return (_noun_entry(tag, "نعت (صفة)", "نعت يتبع منعوته في الإعراب", "sifah"), 0.72)

    return (_noun_entry(tag, "مفعول به (منصوب)",
                       "منصوب لأنه مفعول به. القاعدة: المفعول به منصوب بالفتحة", "mafool", force_case="a"), 0.75)


def _process_noun_nominal(tag: dict, state: dict, pos: str) -> tuple[dict, float]:
    """Process noun in nominal sentence (jumlah ismiyyah)."""
    if not state["mubtada_done"]:
        state["mubtada_done"] = True
        return (_noun_entry(tag, "مبتدأ (مرفوع)",
                           "مرفوع لأنه مبتدأ. القاعدة: المبتدأ مرفوع بالضمة الظاهرة", "mubtada", force_case="n"), 0.82)

    if not state["khabar_done"]:
        state["khabar_done"] = True
        return (_noun_entry(tag, "خبر (مرفوع)",
                           "مرفوع لأنه خبر. القاعدة: الخبر مرفوع بالضمة الظاهرة", "khabar", force_case="n"), 0.78)

    if pos == "adj":
        return (_noun_entry(tag, "نعت (صفة)", "نعت يتبع منعوته في الإعراب", "sifah"), 0.68)

    return (_noun_entry(tag, "اسم (يُحدّد بالسياق)", "يحتاج إلى تحليل سياقي أدق", None), 0.45)
