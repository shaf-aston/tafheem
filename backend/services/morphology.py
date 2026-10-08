"""Arabic morphological analysis service.

Priority fallback chain (highest quality first):
  1. CAMeL Tools Analyzer, readings ranked by the MLE disambiguator, then
     the typed harakat choose among them (harakat.best_reading).
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
from typing import Any

from backend.services.arabic_text import HAS_PYARABIC, has_arabic, shown_root, strip_diacritics, words
from backend.services import verb_reader
from backend.services.nahw_book import is_one
from backend.services.harakat import CAMEL_CASE, CASE_NAME, TANWEEN, base_of, best_reading, weak_last, moved_for_wasl, paused, typed_case, unread, vowel_agreement, letters

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
        # choose among them (harakat.best_reading), which a single pick cannot allow.
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
    "adj":       "ism",   # an adjective is an ism; صفة is a role it may not hold (جَدِيدٌ as khabar)
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


# The tags whose # is settled to a root. A particle or pronoun CAMeL files with a
# # (إنّ as verb_pseudo, الذي, سوف) has no root a reader is looking for.
ROOTED_POS = {"verb", "noun", "noun_prop", "adj"}


def root_pattern(root: str) -> str:
    """CAMeL's root in Arabic letters, keeping its # for a radical it could not pin down; "" for none.

    'ktb' and 'ك-ت-ب' both give كتب. Particles carry the placeholder NTWS
    instead of a root; mapped letter by letter it came out as "NطWص", so a root
    is only Buckwalter-converted when it is wholly Buckwalter.
    """
    if not root or root in _NO_ROOT:
        return ""
    clean = root.replace("-", "").replace(".", "").strip()
    if not has_arabic(clean):
        if not _BUCKWALTER_RE.fullmatch(clean.replace(_UNKNOWN_RADICAL, "")):
            return ""
        clean = "".join(c if c == _UNKNOWN_RADICAL else _bw_to_ar(c) for c in clean)
    return clean


def root_in_arabic(root: str, lemma: str = "") -> str:
    """'ktb' → 'كتب', a root as every tab shows and searches it.

    The radicals used to be joined with hyphens, which read as three letters
    rather than a word: "ك-ت-ب" is not a word any index holds, so a root was
    unsearchable the moment it was shown.

    A # (typically an elided weak letter, ق#ل for قالوا) is settled by
    services/roots.py against the roots the books really file, `lemma`
    choosing between two that fit; one no book files stays no root, never a
    guess dressed as an answer. Without a lemma it is not settled.
    """
    pattern = root_pattern(root)
    if _UNKNOWN_RADICAL in pattern and lemma:
        from backend.services import roots  # it reads with this module

        pattern = roots.settle(pattern, lemma)
    return shown_root(pattern)


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


def _as_command(word: str, a: dict, before: str, after: str) -> dict:
    """CAMeL's word list has no اِجْلِسِي، ارْحَمُوا or قُمْ, so it offers a name or another
    tense; sarf's own table names the command (verb_reader), by the same rules the
    Sarf tab conjugates with. Only a verb or a noun is overruled: لَمْ and مِنْ have a
    command's shape too, and أَفْضَلُ is a comparative whatever sarf can build."""
    if (a.get("pos") or "").lower() not in ("verb", "noun", "noun_prop"):
        return a
    governed = any(is_one(before, family, "before_a_present_verb") for family in ("jazm", "nasb_mudari"))
    root = root_in_arabic(a.get("root") or "", a.get("lex") or "")  # a verb or a noun, so rooted
    # the kasra before hamzat al-wasl is the word's own (سَمِّ اللَّهَ) or a paused sukun (أَقِمِ الصَّلَاةَ)
    cell = verb_reader.command(word, governed, root) or verb_reader.command(paused(word, after), governed, root)
    if cell is None:
        return a
    return {**a, "pos": "verb", "asp": "c", "mod": "na", "vox": "a", "per": cell.person,
            "gen": cell.gender, "num": cell.number, "root": ".".join(cell.root),
            "lex": verb_reader.past(cell) or a.get("lex")}


def _analysis_dict_from_camel(word: str, a: dict, before: str = "", after: str = "") -> dict[str, Any]:
    """Convert a raw CAMeL analysis dict into our standard morphology dict; `before` is
    the bare word typed before it, which can make a command shape a present verb, and
    `after` the word typed after it, whose hamzat al-wasl can turn a sukun to kasra."""
    a = _as_command(word, a, before, after)
    pos = (a.get("pos") or "").lower()
    word_type = _pos_type(pos)
    # A harf has no root in nahw; CAMeL still files one for لم and its kind.
    root_ar = "" if word_type == "harf" else root_in_arabic(a.get("root") or "", (a.get("lex") or "") if pos in ROOTED_POS else "")

    lex = a.get("lex") or a.get("diac") or word
    lemma = strip_diacritics(lex)

    cas = a.get("cas", "na") or "na"
    # A past or imperative verb is mabni: its last vowel is not a case.
    mabni = pos == "verb" and a.get("asp") in ("p", "c")
    case_str = CASE_NAME.get(CAMEL_CASE.get(cas)) or (None if mabni else CASE_NAME.get(typed_case(word)))

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
        # the root's last letter is و or ي (عصا, قاضي): the root string above is empty for those
        "weak_last": weak_last(a),
        # the word without the letters joined to it (وَ+لا، سَ+يَكْتُبُ، أَخُو+كَ), by CAMeL's own split
        "base": base_of(word, a.get("atbtok")),
        # an attached pronoun: 1s_poss is ya al-mutakallim, which hides the case (كِتَابِي);
        # CAMeL writes "0" for none
        "enclitic": "" if a.get("enc0") in (None, "0") else a["enc0"],
        "features": _build_features(a),
        "engine": "camel",
    }


_NOUN_POS = {"noun", "noun_prop", "adj", "abbrev"}
_PART_POS = {"prep", "conj_sub", "part_focus", "conj", "part", "det"}
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

    bare = strip_diacritics(word)
    norm = [a for a in analyses if strip_diacritics(a.get("diac", "")) == bare]

    if word and word[-1] in TANWEEN:
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


def readings(word: str) -> list[tuple[str, str]]:
    """Every way `word` can be read alone, as (lemma, root) pairs, likeliest first.

    For looking a word up rather than parsing it, so nothing is chosen away: a
    dictionary shows فَرّ (flee) and فَرْو (fur) for فروا and lets the reader see
    which. The root keeps CAMeL's # for a weak radical it could not pin down
    (ق#ل for قالوا): services/roots.py settles it, knowing which roots are real. A harf has no root. Without CAMeL, the lemma alone.
    """
    word = word.strip()
    if not word or not has_arabic(word):
        return []
    if _camel_analyzer is None:
        return [(_analyze_qalsadi(word)["lemma"], "")] if _QALSADI_AVAILABLE else []
    try:
        analyses = _camel_analyzer.analyze(word)
    except Exception as exc:
        logger.debug("CAMeL analyze error for '%s': %s", word, exc)
        return []
    # The typed vowels choose first, as they do for a sentence; the readings they allow come
    # next, then the rest by how many typed marks they share: CAMeL has no command فِرُّوا,
    # and the shadda typed on its ر is what puts فَرّ (flee) before فَرْو (fur).
    best = best_reading(word, analyses) or _pick_best_analysis(word, analyses)
    typed = letters(word)

    def shared(a: dict) -> int:
        return sum(len(mine & theirs) for (_, mine), (_, theirs) in zip(typed, letters(a.get("diac", ""))))

    if not any(marks for _, marks in typed):
        ranked = analyses
    else:
        ranked = sorted(analyses, key=lambda a: (vowel_agreement(word, a.get("diac", "")) is None, -shared(a)))
        best = best if best is not None and vowel_agreement(word, best.get("diac", "")) is not None else None
    out: list[tuple[str, str]] = []
    for a in ([best] if best else []) + ranked:
        pos = (a.get("pos") or "").lower()
        root = "" if _pos_type(pos) == "harf" else root_pattern(a.get("root") or "")
        if _UNKNOWN_RADICAL in root and pos not in ROOTED_POS:
            root = ""
        reading = (strip_diacritics(a.get("lex") or ""), root)
        if reading[0] and reading not in out:
            out.append(reading)
    return out


def glosses_of(word: str) -> list[str]:
    """CAMeL's gloss for every analysis of one word; [] when CAMeL is not there."""
    if _camel_analyzer is None:
        return []
    try:
        return [a.get("gloss") or "" for a in _camel_analyzer.analyze(word)]
    except Exception as exc:
        logger.debug("CAMeL analyze error for '%s': %s", word, exc)
        return []


def has_comparative(word: str) -> bool:
    """CAMeL lists a bare noun with the same letters (أجمل: أَجْمَل, more beautiful); a verb
    with no such twin (أنزل, أظن) gives no comparative. False when CAMeL is not there."""
    if _camel_analyzer is None:
        return False
    bare = strip_diacritics(word)
    try:
        return any(a["pos"] in NOUNISH and strip_diacritics(a["lex"]) == bare
                   and all(a.get(c, "0") in ("0", "na") for c in ("prc0", "prc1", "prc2", "enc0"))
                   for a in _camel_analyzer.analyze(bare))
    except Exception as exc:
        logger.debug("CAMeL analyze error for '%s': %s", word, exc)
        return False


def _analyze_qalsadi(word: str) -> dict[str, Any]:
    try:
        result = _lemmatizer.lemmatize(word)  # type: ignore[union-attr]
        lemma = str(result[0]) if isinstance(result, list) and result else str(result)
    except Exception as exc:
        logger.debug("qalsadi lemmatize failed for %r: %s", word, exc)
        lemma = strip_diacritics(word)
    return _unanalysed(word, lemma, "qalsadi")


def _analyze_bare(word: str) -> dict[str, Any]:
    return _unanalysed(word, strip_diacritics(word), "bare")


def _unanalysed(word: str, lemma: str, engine: str) -> dict[str, Any]:
    """A word no analyser placed: only its lemma and the case its harakat show."""
    case_str = CASE_NAME.get(typed_case(word))
    return {
        "word": word, "lemma": lemma, "root": "", "pos": "unknown",
        "type": "ism", "case": case_str, "case_raw": "u", "gloss": "",
        "gender": "na", "number": "na", "person": "na", "aspect": "na",
        "mood": "na", "voice": "na", "state": "na", "pattern": "",
        "weak_last": False, "enclitic": "", "base": strip_diacritics(word),
        "features": f"case={case_str}" if case_str else "",
        "engine": engine,
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
    for i, (token, word_disambig) in enumerate(zip(tokens, disambiguated)):
        ranked = [scored.analysis for scored in word_disambig.analyses]
        if not ranked:
            out.append(_analyze_bare(token))
            continue
        before = strip_diacritics(tokens[i - 1]) if i else ""
        after = tokens[i + 1] if i + 1 < len(tokens) else ""
        # a kasra that may be a moved sukun is no evidence for the reading
        evidence = token[:-1] if moved_for_wasl(token, after) else token
        if unread(ranked) and (twin := verb_reader.known_as(token)):
            # a verb the dictionary lacks but sarf's table has: it reads the table's spelling of it
            ranked, evidence = [scored.analysis for scored in _camel_mle.disambiguate([twin])[0].analyses], twin
        out.append(_analysis_dict_from_camel(token, best_reading(evidence, ranked) or ranked[0], before, after))
    return out


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
