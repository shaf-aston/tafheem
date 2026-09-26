"""Arabic morphological analysis service.

Priority fallback chain (highest quality first):
  1. CAMeL Tools Analyzer, word-level analysis with diacritic-guided
     disambiguation (see _pick_best_analysis); no cross-word context is used.
     (The MLE sentence disambiguator is deliberately NOT loaded, it is tuned
     for MSA and misreads classical/diacritised forms.)
  2. Qalsadi: lemmatisation + basic info
  3. PyArabic / bare harakat, case from diacritics only

One-time CAMeL setup (already done if you can see this running):
    pip install camel-tools
    camel_data -i morphology-db-msa-r13
    camel_data -i disambig-mle-calima-msa-r13
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

from backend.services.arabic_text import HAS_PYARABIC, has_arabic, shown_root, strip_diacritics, words

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. CAMeL Tools, analyzer + MLE disambiguator
# ─────────────────────────────────────────────────────────────────────────────
_CAMEL_AVAILABLE = False
_camel_analyzer = None
_camel_mle = None        # MLE disambiguator (sentence-level, more accurate)
_bw2ar = None

try:
    from camel_tools.morphology.database import MorphologyDB
    from camel_tools.morphology.analyzer import Analyzer
    from camel_tools.utils.charmap import CharMapper

    _db = MorphologyDB.builtin_db()
    _camel_analyzer = Analyzer(_db)  # v1.5+: no 'top' param; all analyses returned
    _bw2ar = CharMapper.builtin_mapper("bw2ar")
    _CAMEL_AVAILABLE = True
    logger.info("CAMeL Tools morphological analyzer ready")

    # Sentence-level disambiguation. Word-level selection cannot resolve
    # undiacritised homographs (ذهب = "gold" or "he went") because the evidence
    # that decides it lives in the neighbouring words, not the word itself.
    try:
        from camel_tools.disambig.mle import MLEDisambiguator
        # Every reading, ranked, not just the top one: the typed vowels then
        # choose among them (_heeding_vowels), which a single pick cannot allow.
        _camel_mle = MLEDisambiguator.pretrained(top=1_000_000)
        logger.info("CAMeL Tools MLE disambiguator ready")
    except Exception as _exc:
        logger.warning(
            "MLE disambiguator unavailable (%s), sentences fall back to "
            "word-level analysis", _exc
        )

except Exception as _exc:
    logger.warning("CAMeL Tools not available (%s), falling back to Qalsadi", _exc)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Qalsadi (only loaded when CAMeL is absent)
# ─────────────────────────────────────────────────────────────────────────────
_QALSADI_AVAILABLE = False
_lemmatizer = None

if not _CAMEL_AVAILABLE:
    try:
        import qalsadi.lemmatizer as _ql
        _lemmatizer = _ql.Lemmatizer()
        _QALSADI_AVAILABLE = True
        logger.info("Qalsadi lemmatizer ready")
    except Exception as _exc:
        logger.warning("Qalsadi not available (%s), using PyArabic/bare only", _exc)

# PyArabic is the third engine, and arabic_text is the module that looks for it.

# ─────────────────────────────────────────────────────────────────────────────
# Lookup tables
# ─────────────────────────────────────────────────────────────────────────────

# What the morphology database writes for a radical it cannot determine.
_UNKNOWN_RADICAL = "#"
# Root fields that mean "none": absent, and the particle placeholder NTWS.
_NO_ROOT = {"", "na", "NTWS"}

_BW_MAP: dict[str, str] = {
    "'": "ء", "|": "آ", ">": "أ", "&": "ؤ", "<": "إ", "}": "ئ",
    "A": "ا", "b": "ب", "p": "ة", "t": "ت", "v": "ث", "j": "ج",
    "H": "ح", "x": "خ", "d": "د", "*": "ذ", "r": "ر", "z": "ز",
    "s": "س", "$": "ش", "S": "ص", "D": "ض", "T": "ط", "Z": "ظ",
    "E": "ع", "g": "غ", "f": "ف", "q": "ق", "k": "ك", "l": "ل",
    "m": "م", "n": "ن", "h": "ه", "w": "و", "Y": "ى", "y": "ي",
}
# A root made only of letters the Buckwalter table knows how to convert.
_BUCKWALTER_RE = re.compile("[" + re.escape("".join(_BW_MAP)) + "]+")

_POS_TYPE: dict[str, str] = {
    "noun":      "ism",
    "noun_prop": "ism",   # CAMeL: proper nouns; still ism in Nahw
    "verb":      "fi'l",
    "adj":       "sifah",
    "prep":      "harf",
    "conj":      "harf",
    "conj_sub":  "harf",  # subordinating conjunction (إنّ / أنّ etc.)
    "pron":      "damir",
    "det":       "harf",
    "part":      "harf",
    "part_focus":"harf",
    "adv":       "zarf",
    "interj":    "harf",
    "abbrev":    "ism",
    "punc":      "punc",
    "digit":     "ism",
    "latin":     "other",
}


def _pos_type(pos: str) -> str:
    """Nahw word type for a CAMeL part of speech.

    CAMeL has a dozen particle tags (part_neg, part_verb, part_det, ...) and
    the table cannot list them all, so any unlisted part_/conj_/prep_ tag is
    a harf. Unlisted anything else is an ism, the safest default: لم was
    printed as a noun with a root because part_neg had no row here.
    """
    if pos in _POS_TYPE:
        return _POS_TYPE[pos]
    return "harf" if pos.startswith(("part", "conj", "prep", "interj")) else "ism"

_CAS_MAP: dict[str, str | None] = {
    "n": "raf'", "a": "nasb", "g": "jarr", "na": None, "u": None,
}

_ASP_LABEL: dict[str, str] = {
    "p": "perfect (ماضٍ)", "i": "imperfect (مضارع)", "c": "command (أمر)",
}

_MOD_LABEL: dict[str, str] = {
    "i": "indicative (مرفوع)", "s": "subjunctive (منصوب)", "j": "jussive (مجزوم)",
}


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _bw_to_ar(bw: str) -> str:
    if _bw2ar is not None:
        try:
            return _bw2ar.map(bw)
        except Exception:
            pass
    return "".join(_BW_MAP.get(c, c) for c in bw)


def _bw_root_to_arabic(root: str) -> str:
    """'ktb' → 'كتب'  (handles already-Arabic roots too).

    The radicals used to be joined with hyphens, which read as three letters
    rather than a word. It was decoration, never data: the same string is what
    the Define and In-the-Qur'an buttons search with, and "ك-ت-ب" is not a word
    any index holds, so a root was unsearchable the moment it was shown.

    The morphology database writes ``#`` for a radical it cannot pin down
    (typically an elided weak letter). Showing that to a reader is a guess
    dressed as an answer, so an incomplete root is reported as no root.

    Particles carry the placeholder ``NTWS`` instead of a root. Mapped letter
    by letter it came out as "NطWص" on the Nahw table, so a root is only
    Buckwalter-converted when it is wholly Buckwalter, and shown_root drops
    anything that still holds a code letter afterwards.
    """
    if not root or root in _NO_ROOT or _UNKNOWN_RADICAL in root:
        return ""
    clean = root.replace("-", "").replace(".", "").strip()
    if not has_arabic(clean) and _BUCKWALTER_RE.fullmatch(clean):
        clean = "".join(_bw_to_ar(c) for c in clean)
    return shown_root(clean)


# Single owner of diacritics stripping lives in services/arabic_text.py
_strip_diacritics = strip_diacritics


def _harakat_case(word: str) -> str | None:
    # The mark can sit either side of a shadda (رَبِّ, الجَوُّ), and a tanween
    # fath is usually written before a closing alef (حَقًّا), so both are set
    # aside before the last mark is read.
    end = word.replace("ّ", "")
    end = end.removesuffix("ا") if end.endswith("ًا") else end
    if end.endswith(("ٌ", "ُ")):
        return "raf'"
    if end.endswith(("ً", "َ")):
        return "nasb"
    return "jarr" if end.endswith(("ٍ", "ِ")) else None


def _build_features(a: dict) -> str:
    parts: list[str] = []
    asp = a.get("asp", "na") or "na"
    mod = a.get("mod", "na") or "na"
    vox = a.get("vox", "na") or "na"
    gen = a.get("gen", "na") or "na"
    num = a.get("num", "na") or "na"
    per = a.get("per", "na") or "na"
    stt = a.get("stt", "na") or "na"

    if asp in _ASP_LABEL:
        parts.append(_ASP_LABEL[asp])
    if mod in _MOD_LABEL and a.get("pos") == "verb":
        parts.append(_MOD_LABEL[mod])
    if vox == "p":
        parts.append("passive (مبني للمجهول)")
    if gen == "m":
        parts.append("masculine (مذكر)")
    elif gen == "f":
        parts.append("feminine (مؤنث)")
    if num == "s":
        parts.append("singular (مفرد)")
    elif num == "d":
        parts.append("dual (مثنى)")
    elif num == "p":
        parts.append("plural (جمع)")
    if per in ("1", "2", "3"):
        parts.append({"1": "1st person", "2": "2nd person", "3": "3rd person"}.get(per, f"person {per}"))
    if stt == "d":
        parts.append("definite (معرفة)")
    elif stt == "i":
        parts.append("indefinite (نكرة)")
    elif stt == "c":
        parts.append("construct (مضاف)")
    return ", ".join(parts)


def _analysis_dict_from_camel(word: str, a: dict) -> dict[str, Any]:
    """Convert a raw CAMeL analysis dict into our standard morphology dict."""
    pos = (a.get("pos") or "").lower()
    word_type = _pos_type(pos)
    # A harf has no root in nahw; CAMeL still files one for لم and its kind.
    root_ar = "" if word_type == "harf" else _bw_root_to_arabic(a.get("root") or "")

    lex = a.get("lex") or a.get("diac") or word
    lemma = _strip_diacritics(lex)

    cas = a.get("cas", "na") or "na"
    # A past or imperative verb is mabni: its last vowel is not a case.
    mabni = pos == "verb" and a.get("asp") in ("p", "c")
    case_str = _CAS_MAP.get(cas) or (None if mabni else _harakat_case(word))

    return {
        "word": word,
        "lemma": lemma,
        "root": root_ar,
        "pos": pos,
        "type": word_type,
        "case": case_str,
        "case_raw": cas,
        "gloss": a.get("gloss") or "",
        "gender": a.get("gen") or "na",
        "number": a.get("num") or "na",
        "person": a.get("per") or "na",
        "aspect": a.get("asp") or "na",
        "mood": a.get("mod") or "na",
        "voice": a.get("vox") or "na",
        "state": a.get("stt") or "na",
        "pattern": a.get("pattern") or "",
        "features": _build_features(a),
        "engine": "camel",
    }


_NOUN_POS = {"noun", "noun_prop", "adj", "abbrev"}
_PART_POS = {"prep", "conj_sub", "part_focus", "conj", "part", "det"}
_TANWIN = {"ٌ", "ً", "ٍ"}  # ٌ ً ٍ  dammatan/fathatan/kasratan
_FATHA = "َ"           # ـَ  Arabic Fathah


def _find_by_pos_preference(items: list[dict], preferences: tuple) -> dict | None:
    """Find first item matching any of the preferred POS values."""
    for pref in preferences:
        for item in items:
            if (item.get("pos") or "").lower() == pref:
                return item
    return None


def _pick_best_analysis(word: str, analyses: list[dict]) -> dict | None:
    """
    Diacritic-guided selection, far more accurate than MLE for Classical Arabic.

    Priority order (each step only runs if the previous produced ambiguity):

      1. Exact diac match  → ``diac`` field == input word (fully vowelled text)
      2. Tanwin bias       → word ends in tanwin (ٌ ً ٍ) → strongly prefer noun/adj
      3. Fatha bias        → word ends in fatha (ـَ): particles, then verb+perfect
      4. Normalized match  → strip diacritics, match form
      5. First analysis    → last resort (CAMeL default ranking)
    """
    if not analyses:
        return None

    if exact := [a for a in analyses if a.get("diac") == word]:
        return _handle_exact_match(word, exact)

    bare = _strip_diacritics(word)
    norm = [a for a in analyses if _strip_diacritics(a.get("diac", "")) == bare]

    if word and word[-1] in _TANWIN:
        if result := _handle_tanwin_bias(norm or analyses):
            return result

    if word.endswith(_FATHA):
        if result := _handle_fatha_bias(norm):
            return result

    if norm:
        return _find_by_pos_preference(
            norm, ("prep", "conj_sub", "part_focus", "conj", "noun_prop", "noun", "adj", "verb")
        ) or norm[0]

    return analyses[0] if analyses else None


def _handle_exact_match(word: str, exact: list[dict]) -> dict:
    """Handle exact diacritic match case."""
    if len(exact) == 1:
        return exact[0]

    if part := _find_by_pos_preference(
        exact, ("prep", "conj_sub", "part_focus", "conj", "part")
    ):
        return part

    if word.endswith(_FATHA):
        if verb := next(
            (
                a
                for a in exact
                if (a.get("pos") or "").lower() == "verb"
                and (a.get("asp") or "") == "p"
            ),
            None,
        ):
            return verb

    noun = _find_by_pos_preference(exact, ("noun_prop", "noun", "adj", "verb"))
    return noun or exact[0]


def _handle_tanwin_bias(items: list[dict]) -> dict | None:
    """Handle tanwin (nunation) bias, prefer nouns/adjectives."""
    nouns = [a for a in items if (a.get("pos") or "").lower() in _NOUN_POS]
    return nouns[0] if nouns else None


def _handle_fatha_bias(items: list[dict]) -> dict | None:
    """Handle fatha bias, prefer particles, then verb+perfect."""
    if parts := [
        a for a in items if (a.get("pos") or "").lower() in _PART_POS
    ]:
        return parts[0]

    verbs = [
        a
        for a in items
        if (a.get("pos") or "").lower() == "verb" and (a.get("asp") or "") == "p"
    ]
    return verbs[0] if verbs else None


# ─────────────────────────────────────────────────────────────────────────────
# Word-level analysis
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_word_camel_only(word: str) -> dict[str, Any] | None:
    """Word-level CAMeL Analyzer with diacritic-guided best-analysis selection."""
    if _camel_analyzer is None:
        return None
    try:
        analyses = _camel_analyzer.analyze(word)
    except Exception as exc:
        logger.debug("CAMeL analyze error for '%s': %s", word, exc)
        return None
    best = _pick_best_analysis(word, analyses)
    return None if best is None else _analysis_dict_from_camel(word, best)


def _analyze_qalsadi(word: str) -> dict[str, Any]:
    try:
        result = _lemmatizer.lemmatize(word)  # type: ignore[union-attr]
        lemma = str(result[0]) if isinstance(result, list) and result else str(result)
    except Exception as exc:
        logger.debug("qalsadi lemmatize failed for %r: %s", word, exc)
        lemma = _strip_diacritics(word)
    case_str = _harakat_case(word)
    return {
        "word": word, "lemma": lemma, "root": "", "pos": "unknown",
        "type": "ism", "case": case_str, "case_raw": "u", "gloss": "",
        "gender": "na", "number": "na", "person": "na", "aspect": "na",
        "mood": "na", "voice": "na", "state": "na", "pattern": "",
        "features": f"case={case_str}" if case_str else "",
        "engine": "qalsadi",
    }


def _analyze_bare(word: str) -> dict[str, Any]:
    case_str = _harakat_case(word)
    return {
        "word": word, "lemma": _strip_diacritics(word), "root": "", "pos": "unknown",
        "type": "ism", "case": case_str, "case_raw": "u", "gloss": "",
        "gender": "na", "number": "na", "person": "na", "aspect": "na",
        "mood": "na", "voice": "na", "state": "na", "pattern": "",
        "features": f"case={case_str}" if case_str else "",
        "engine": "bare",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_engine_name() -> str:
    if _CAMEL_AVAILABLE:
        return "camel-tools"
    if _QALSADI_AVAILABLE:
        return "qalsadi"
    return "pyarabic" if HAS_PYARABIC else "bare"


def analyze_word(word: str) -> dict[str, Any]:
    """Morphological analysis of a single Arabic word (no sentence context)."""
    word = word.strip()
    if not word or not has_arabic(word):
        return _analyze_bare(word)
    if _CAMEL_AVAILABLE:
        if result := _analyze_word_camel_only(word):
            return result
    return _analyze_qalsadi(word) if _QALSADI_AVAILABLE else _analyze_bare(word)


def _analyze_sentence_camel_mle(tokens: list[str]) -> list[dict[str, Any]] | None:
    """
    Sentence-level analysis: neighbouring words decide each word's reading.

    Evidence order per token: a fully-diacritised input matches exactly one
    analysis and settles it outright; otherwise the disambiguator's own ranking
    decides, so no fixed part-of-speech preference is imposed here.
    """
    if _camel_mle is None:
        return None
    try:
        disambiguated = _camel_mle.disambiguate(tokens)
    except Exception as exc:
        logger.debug("CAMeL MLE disambiguation failed: %s", exc)
        return None

    out: list[dict[str, Any]] = []
    for token, word_disambig in zip(tokens, disambiguated):
        ranked = [scored.analysis for scored in word_disambig.analyses]
        if not ranked:
            out.append(_analyze_bare(token))
            continue
        out.append(_analysis_dict_from_camel(token, _heeding_vowels(token, ranked)))
    return out


# The vowel a mark writes, so a fatha and a fathatan on the same letter still
# disagree (one is definite, one is not) while a missing mark agrees with anything.
_VOWEL = {"َ": "a", "ُ": "u", "ِ": "i", "ً": "an", "ٌ": "un", "ٍ": "in", "ْ": "o", "ّ": "~"}


def _marks_by_letter(text: str) -> list[set[str]]:
    letters: list[set[str]] = []
    for ch in text:
        if ch in _VOWEL:
            if letters:
                letters[-1].add(_VOWEL[ch])
        elif not unicodedata.combining(ch):
            letters.append(set())
    return letters


def _vowel_agreement(token: str, diac: str) -> int | None:
    """How many of the vowels typed on `token` this reading also has, or None
    when a typed vowel contradicts it (فَتَحَ against فَتْح).

    A letter the reading leaves bare agrees with whatever was typed on it; the
    two spellings disagreeing on how many letters there are (hamza seats, the
    dagger alef) says nothing either way, so it scores nothing.
    """
    typed, read = _marks_by_letter(token), _marks_by_letter(diac)
    if len(typed) != len(read):
        return 0
    agreed = 0
    for mine, theirs in zip(typed, read):
        if not mine or not theirs:
            continue
        if (mine - {"~"}) and (theirs - {"~"}) and (mine - {"~"}) != (theirs - {"~"}):
            return None
        agreed += len(mine & theirs)
    return agreed


def _heeding_vowels(token: str, ranked: list[dict]) -> dict:
    """The reading the typed vowels support best, in the disambiguator's order
    among equals. Vowels the reader wrote are evidence the statistics lack:
    ranked alone, فَتَحَ came back as the noun فَتْح."""
    scored = [(s, i) for i, a in enumerate(ranked) if (s := _vowel_agreement(token, a.get("diac", ""))) is not None]
    if not scored:
        return ranked[0]
    best = max(scored, key=lambda pair: (pair[0], -pair[1]))
    return ranked[best[1]]


def analyze_sentence(sentence: str) -> list[dict[str, Any]]:
    """
    Tokenise and morphologically analyse a sentence.

    Uses sentence context (MLE disambiguator) when available, falling back to
    independent word-level analysis when it is not.
    """
    tokens = words(sentence)
    if not tokens:
        return []

    if _CAMEL_AVAILABLE:
        if result := _analyze_sentence_camel_mle(tokens):
            return result
        return [analyze_word(t) for t in tokens]

    if _QALSADI_AVAILABLE:
        return [_analyze_qalsadi(t) for t in tokens]

    return [_analyze_bare(t) for t in tokens]


def tags_as_string(tags: list[dict]) -> str:
    """Compact one-line summary injected into LLM prompts."""
    parts: list[str] = []
    for t in tags:
        word = t.get("word", "")
        bits = [f"lemma={t.get('lemma', '')}"]
        if t.get("root"):
            bits.append(f"root={t['root']}")
        pos = t.get("pos", "")
        if pos and pos not in ("unknown", ""):
            bits.append(f"pos={pos}")
        if t.get("case"):
            bits.append(f"case={t['case']}")
        if feats := t.get("features", ""):
            bits.append(feats)
        parts.append(f"{word} ({', '.join(bits)})")
    return "; ".join(parts)


# Parts of speech that are not verbs, so have no conjugation table of their own.
NOUNISH = {"noun", "noun_prop", "adj", "abbrev", "noun_num", "noun_quant", "adj_comp"}


def clean_gloss(text: str) -> str:
    """Turn a tagger's gloss into English a reader can read.

    CAMeL writes one entry as `receive;greet;meet+he;it_<verb>`, alternatives
    separated by semicolons, an attached pronoun after a plus, a part-of-speech
    tag in angle brackets and underscores where spaces belong. None of that is
    English, and all of it was going straight onto the screen.
    """
    text = re.sub(r"<[^>]*>", " ", text).split("+")[0]
    senses = [s.replace("_", " ").strip() for s in text.split(";")]
    return ", ".join(dict.fromkeys(s for s in senses if s))
