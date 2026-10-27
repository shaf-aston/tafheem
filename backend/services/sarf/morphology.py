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
from typing import Any, NamedTuple

from backend.services.text.arabic_text import HAS_PYARABIC, bare_letters, has_arabic, shown_root, strip_diacritics, words
from backend.services.sarf import noun_reader
from backend.services.sarf import verb_reader
from backend.services.nahw.book import book_map, book_words, elative_shape, is_built_word, is_mabni, is_one, participle_shape, sakt_off, six_noun_case
from backend.services.text.harakat import CAMEL_CASE, CASE_NAME, NO_ANALYSIS, TANWEEN, base_of, best_reading, has_tanween, nearest_reading, past_passive_shape, weak_last, moved_for_wasl, paused, stuck_letters, typed_case, unread, vowel_agreement, letters

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

# the kinds known by what they are, with no ال: a pronoun, a pointer, a name, a relative (Ibn Aqil V1 p86:
# وغيره معرفة كهم وذي وهند وابني والغلام والذي), though CAMeL files them indefinite
_KNOWN_KINDS = frozenset({"pron", "pron_dem", "pron_rel", "noun_prop"})


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


def has_no_root(pos: str) -> bool:
    """A harf, or a noun built like one (a pronoun, a demonstrative, a relative): no root to find.

    "حرفٌ وشِبْهُهُ من الصَّرْفِ بَرِي" (the Alfiyya, at التصريف): sarf, and so a root, is only for
    the declined noun and the conjugated verb. The Qur'an corpus agrees: of the words CAMeL
    reads first as one of these, it roots 0 to 14 in 100; nouns, verbs and adverbs, 80 to 99.
    CAMeL still files a root for many of them (إليه under و ل ي, إنه under أ و ن).
    """
    return _pos_type(pos) == "harf" or pos.startswith("pron") or pos == "verb_pseudo"


class Reading(NamedTuple):
    """One way a word can be read alone."""

    lemma: str
    root: str  # CAMeL's, a # kept for a weak radical it could not pin down; "" for none
    rooted: bool  # False for a word that has no root at all (has_no_root)


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


def root_in_arabic(root: str, lemma: str = "", word: str = "") -> str:
    """'ktb' → 'كتب', a root as every tab shows and searches it.

    The radicals used to be joined with hyphens, which read as three letters
    rather than a word: "ك-ت-ب" is not a word any index holds, so a root was
    unsearchable the moment it was shown.

    A # (typically an elided weak letter, ق#ل for قالوا) is settled by
    services/dictionary/roots.py against the roots the books really file, `lemma`
    choosing between two that fit; one no book files stays no root, never a
    guess dressed as an answer. Without a lemma it is not settled; `word`, the form
    read, overrules a lemma that is not its own. A root of
    two letters (لس for ليس) is the one a book files the lemma under, or none.
    """
    from backend.services.dictionary import roots  # it reads with this module

    pattern = root_pattern(root)
    if pattern and (lemma or len(pattern) < roots.FEWEST_RADICALS):
        pattern = roots.settle(pattern, lemma, word)
    return shown_root(pattern)


def reading_root(a: dict) -> str:
    """The root of one CAMeL reading as every tab shows it; "" for a word with none.

    CAMeL still files a root for لم, هو, الذي and their kind (has_no_root), and for a foreign
    name (م.#.س for موسى) the Qur'an tags with none. The lemma settles a # only for a word
    built from a root (ROOTED_POS).
    """
    from backend.services.dictionary import roots  # it reads with this module

    pos = a.get("pos") or ""
    if pos == "noun_prop" and roots.tagged_rootless(a.get("diac") or ""):
        return ""
    return "" if has_no_root(pos) else root_in_arabic(a.get("root") or "", (a.get("lex") or "") if pos in ROOTED_POS else "", a.get("diac") or "")


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
    # only the present verb takes a mood: the past and the command are built (Ibn Aqil V1 p35: وفعل أمر ومضي بنيا)
    if mod in _MOD_LABEL and a.get("pos") == "verb" and asp == "i":
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
    if stt == "d" or a.get("pos") in _KNOWN_KINDS:
        parts.append("definite (معرفة)")
    elif stt == "i":
        parts.append("indefinite (نكرة)")
    elif stt == "c":
        parts.append("construct (مضاف)")
    return ", ".join(parts)


def _as_command(word: str, a: dict, before: str, after: str, after_read: str = "") -> dict:
    """CAMeL's word list has no اِجْلِسِي، ارْحَمُوا or قُمْ, so it offers a name or another
    tense; sarf's own table names the command (verb_reader), by the same rules the
    Sarf tab conjugates with. Only a verb or a noun is overruled: لَمْ and مِنْ have a
    command's shape too, and أَفْضَلُ is a comparative whatever sarf can build."""
    if (a.get("pos") or "").lower() not in ("verb", "noun", "noun_prop") or is_built_word(a.get("lex") or ""):
        return a  # مُنْذُ أَمْسِ: a built time word is never the command its letters spell
    if a.get("pos") != "verb" and verb_reader.called(before, after, after_read):
        return a  # يَا رَبِّ، رَبِّ اغْفِرْ لِي: a noun called, not رَبَّى's command
    governed = any(is_one(before, family, "before_a_present_verb") for family in ("jazm", "nasb_mudari"))
    root = root_in_arabic(a.get("root") or "", a.get("lex") or "", word)  # a verb or a noun, so rooted
    # the kasra before hamzat al-wasl is the word's own (سَمِّ اللَّهَ) or a paused sukun (أَقِمِ الصَّلَاةَ)
    cell = verb_reader.command(word, governed, root) or verb_reader.command(paused(word, after), governed, root)
    if cell is None:
        return a
    return {**a, "pos": "verb", "asp": "c", "mod": "na", "vox": "a", "per": cell.person,
            "gen": cell.gender, "num": cell.number, "root": ".".join(cell.root),
            "lex": verb_reader.past(cell) or a.get("lex")}


def _analysis_dict_from_camel(word: str, a: dict, before: str = "", after: str = "", after_read: str = "") -> dict[str, Any]:
    """Convert a raw CAMeL analysis dict into our standard morphology dict; `before` is
    the bare word typed before it, which can make a command shape a present verb, and
    `after` the word typed after it, whose hamzat al-wasl can turn a sukun to kasra, read as `after_read` (its tense)."""
    a = _as_command(word, a, before, after, after_read)
    pos = (a.get("pos") or "").lower()
    word_type = _pos_type(pos)
    root_ar = reading_root(a)

    lex = a.get("lex") or a.get("diac") or word
    lemma = strip_diacritics(lex)
    guessed = NO_ANALYSIS in a.get("atbtok", "")

    cas = a.get("cas", "na") or "na"
    # A built word (a past verb, a pronoun) has no case: its last vowel is not one. Nor is a
    # noun's attached pronoun's (the fatha of أَخِيكَ is the kaf's), and on ياء المتكلم the case
    # is unseen (the fatha of سُلْطَانِيَ is the ya's own).
    unseen = is_mabni(pos, a.get("asp"), base_of(word, a.get("atbtok"))) or a.get("enc0") == "1s_poss"
    pronoun = stuck_letters({"form": piece} for piece in (a.get("atbtok") or "").split("_")) if pos in NOUNISH else 0
    case_str = CASE_NAME.get(CAMEL_CASE.get(cas)) or (None if unseen else CASE_NAME.get(typed_case(word, pronoun)))

    return {
        "word": word,
        "lemma": lemma,
        "root": root_ar,
        "pos": pos,
        "type": word_type,
        "case": case_str,
        "case_raw": cas,
        # a word CAMeL could not read has its mark for that as the gloss, which is no English
        "gloss": "" if guessed else a.get("gloss") or "",
        "stemgloss": "" if guessed else a.get("stemgloss") or "",  # the word's own piece of the gloss
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

    if word.endswith(_FATHA) and (verb := _perfect_verb(exact)):
        return verb

    noun = _find_by_pos_preference(exact, ("noun_prop", "noun", "adj", "verb"))
    return noun or exact[0]


def _perfect_verb(items: list[dict]) -> dict | None:
    return next((a for a in items if (a.get("pos") or "").lower() == "verb" and (a.get("asp") or "") == "p"), None)


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

    return _perfect_verb(items)


# How often a reading's lemma, as its part of speech, occurs in CAMeL's training text (log10);
# a reading without the figure ranks last.
_LIKELIHOOD = "pos_lex_logprob"
_NEVER_SEEN = -99.0


# ─────────────────────────────────────────────────────────────────────────────
# Word-level analysis
# ─────────────────────────────────────────────────────────────────────────────

def _seen_verb(past: str) -> bool:
    """The dictionary's training text uses this verb, given by its past (هَدَى, not هَدَنَ), as the dictionary
    spells it: every letter, its hamza too (هَدَا is not هَدَأ), and every vowel both write (ضَرِبَ is not ضَرَبَ)."""
    return any(a.get("pos") == "verb" and a.get(_LIKELIHOOD, _NEVER_SEEN) > _NEVER_SEEN
               and strip_diacritics(a["lex"]).translate(_WASL) == strip_diacritics(past)
               and vowel_agreement(past, a["lex"]) is not None for a in _analyses(past))


_WASL = str.maketrans("ٱ", "ا")  # the dictionary writes a past's hamzat al-wasl so (ٱِسْتَغْفَر)


def _analyses(word: str) -> list[dict]:
    """Every CAMeL reading of one word, the likeliest lemma first; [] when CAMeL is not there.

    The analyzer lists readings in no order of likelihood, so a first pick from its list
    took يترك for وَتَر rather than تَرَك and يكن for كَنّ rather than كان. Each reading
    carries how often its lemma, as that part of speech, occurs in CAMeL's training text
    (pos_lex_logprob); every pick below that falls back to "the first" now means the likeliest.
    """
    if _camel_analyzer is None:
        return []
    try:
        analyses = _camel_analyzer.analyze(word)
    except Exception as exc:
        logger.debug("CAMeL analyze error for '%s': %s", word, exc)
        return []
    return sorted(analyses, key=lambda a: -a.get(_LIKELIHOOD, _NEVER_SEEN))


def _analyze_word_camel_only(word: str) -> dict[str, Any] | None:
    """Word-level CAMeL Analyzer with diacritic-guided best-analysis selection."""
    if _camel_analyzer is None:
        return None
    best = _pick_best_analysis(word, _analyses(word))
    return None if best is None else _analysis_dict_from_camel(word, best)


def readings(word: str) -> list[Reading]:
    """Every way `word` can be read alone, likeliest first.

    For looking a word up rather than parsing it, so nothing is chosen away: a
    dictionary shows فَرّ (flee) and فَرْو (fur) for فروا and lets the reader see
    which. The root keeps CAMeL's # for a weak radical it could not pin down
    (ق#ل for قالوا): services/dictionary/roots.py settles it, knowing which roots are real. A harf has no root. Without CAMeL, the lemma alone.
    """
    word = word.strip()
    if not word or not has_arabic(word):
        return []
    if _camel_analyzer is None:
        return [Reading(_analyze_qalsadi(word)["lemma"], "", True)] if _QALSADI_AVAILABLE else []
    analyses = _analyses(word)
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
    out: list[Reading] = []
    for a in ([best] if best else []) + ranked:
        pos = (a.get("pos") or "").lower()
        rooted = not has_no_root(pos)
        root = root_pattern(a.get("root") or "") if rooted else ""
        if _UNKNOWN_RADICAL in root and pos not in ROOTED_POS:
            root = ""
        reading = Reading(strip_diacritics(a.get("lex") or ""), root, rooted)
        if reading.lemma and reading not in out:
            out.append(reading)
    return out


def glosses_of(word: str) -> list[str]:
    """CAMeL's gloss for every analysis of one word; [] when CAMeL is not there."""
    return [a.get("gloss") or "" for a in _analyses(word)]


def gloss_as(reading: dict, pos: str | None) -> str:
    """The reading's gloss with the word itself read as the class `pos`, its joined letters'
    English kept: the grammar's job for a word CAMeL lists under more than one (فَإِنَّ is
    "so indeed", the condition's فَإِنْ "so if"). A reading CAMeL has of that class spelled with
    the word's own letters gives the sense, the likeliest first; with none the gloss stands."""
    gloss = reading.get("gloss") or _lemma_gloss(reading)
    if not pos or reading.get("pos") == pos:
        return gloss
    written = strip_diacritics(reading.get("base") or reading.get("word") or "")
    other = next((a for a in _analyses(written)
                  if a.get("pos") == pos and strip_diacritics(a.get("diac") or "") == written), None)
    if other is None:
        return gloss
    stem = reading.get("stemgloss")
    return "+".join(other.get("stemgloss") or piece if piece == stem else piece for piece in gloss.split("+"))


def _lemma_gloss(reading: dict) -> str:
    """A verb only sarf's table read (verb_reader) has no gloss of its own: it means what the
    dictionary's reading of its lemma, in its class, means (آتِنَا is آتَى's: give, not أَتَى's come); "" for none."""
    lemma = reading.get("lemma") or ""
    return next((a["stemgloss"] for a in _analyses(lemma) if a.get("pos") == reading.get("pos")
                 and strip_diacritics(a.get("lex") or "") == lemma), "")


def has_comparative(word: str) -> bool:
    """CAMeL lists a bare noun with the same letters (أجمل: أَجْمَل, more beautiful); a verb
    with no such twin (أنزل, أظن) gives no comparative. False when CAMeL is not there."""
    bare = strip_diacritics(word)
    return any(a["pos"] in NOUNISH and strip_diacritics(a["lex"]) == bare
               and all(a.get(c, "0") in ("0", "na") for c in ("prc0", "prc1", "prc2", "enc0"))
               for a in _analyses(bare))


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


def _reading(word: str, readings: list[dict]) -> dict:
    """The best reading of a word that does not contradict its typed vowels.

    The disambiguator reads bare letters, so its favourite may not be the word
    written. The typed vowels win: the reading sharing most of them is used
    (harakat.best_reading), never the guessed proper noun. When no real reading
    agrees the favourite is kept; naming still reads the vowels (a passive بُعْثِرَ).
    """
    if not readings:
        return {}
    real = [r for r in readings if NO_ANALYSIS not in r.get("atbtok", "")]
    verbs = [r for r in readings
             if r.get("pos") == "verb" and bare_letters(r.get("diac", "")) == bare_letters(word)]
    if past_passive_shape(word) and verbs:
        # the shape is a past verb's: اسْتُعْمِلَ, which CAMeL lacks, is its active اِسْتَعْمَلَ
        # with the voice read off the vowels, never أَسْتَعْمِلُ
        return next((r for r in verbs if r.get("asp") == "p"), verbs[0])
    # a reading spelled with the letters typed goes first, even one vowel off, before another word's
    # letters that say nothing either way (خُلُقُهُ is خُلْقُهُ, not خَلَقَة)
    same = [r for r in real if [bare_letters(c) for c, _ in letters(r.get("diac", ""))] == [bare_letters(c) for c, _ in letters(word)]]
    return best_reading(word, same) or nearest_reading(word, same) or best_reading(word, real) or readings[0]


def _ranked(tokens: list[str], disambiguator) -> list[list[dict]] | None:
    """Each word's CAMeL readings, best first, from the disambiguator (BERT) and, if it fails,
    the MLE; None when neither reads."""
    for engine in filter(None, (disambiguator, _camel_mle)):
        try:
            return [[scored.analysis for scored in word.analyses] for word in engine.disambiguate(tokens)]
        except Exception as exc:
            logger.warning("CAMeL disambiguation failed: %s", exc)
    return None


def pick(tokens: list[str], disambiguator=None) -> list[dict[str, Any]]:
    """One raw CAMeL reading per word ({} where none is read), shared by the cards and
    the parser. Neighbours rank the readings (MLE, or the parser's BERT), the typed vowels choose."""
    if (all_ranked := _ranked(tokens, disambiguator)) is None:
        return [{} for _ in tokens]

    steps = []  # each word's vowels as evidence, and its ranked readings
    paused = {}  # a هاء السكت's word: the word as said joined (مَالِيَهْ → مَالِيَ)
    for i, (token, ranked, after) in enumerate(zip(tokens, all_ranked, [*tokens[1:], ""], strict=True)):
        # a kasra that may be a moved sukun is no evidence for the reading
        evidence = token[:-1] if moved_for_wasl(token, after) else token
        if said := _without_sakt(tokens, i, disambiguator):
            evidence, ranked = said
            paused[i] = evidence
        if unread(ranked) and (twin := verb_reader.known_as(token)) and (twin_ranked := _ranked([twin], disambiguator)):
            # a verb the dictionary lacks but sarf's table has (فَلْيَسْتَعْفِفْ): it reads the table's spelling of it
            ranked, evidence = twin_ranked[0], twin
        # زيدا typed bare fits the verb زَيَّدَا too, but that one adds a shadda the writing lacks and the name none
        # (الأصل عدم الزيادة), so the name in nasb is read where it adds fewer. A particle stays (الا is إِلَّا)
        agreeing, read = _agreeing(evidence, ranked), _reading(evidence, ranked)
        if (not agreeing or read.get("pos") == "verb" and _added(read, token)) and (name := _name_in_nasb(token, disambiguator)) \
                and (not agreeing or _added(name, token) < _added(read, token)):
            ranked = [name]
        if lam := _emphasis_lam(evidence, disambiguator):
            ranked = [lam]
        if not _agreeing(evidence, ranked) and (sarf := verb_reader.reading_of(token, _seen_verb)) \
                and (sarf.get("asp") != "c" or "enc0" in sarf) \
                and all(r.get("asp") != sarf.get("asp") for r in ranked if NO_ANALYSIS not in r.get("atbtok", "")):
            # يَسْتَعْتِبُوا، تَسْتَحِ: no reading the dictionary has is the word typed, so the table's is. One of
            # the table's own tense is only spelled otherwise: the dictionary's stays. A command alone is left to
            # repair.typed (verb_reader.command); one with its object pronoun written on (اِهْدِنَا) is split here
            ranked = [{"lex": base_of(evidence, sarf.get("atbtok")), **sarf, "diac": evidence}]  # its past, else the verb's own letters
        elif not steps and (asked := _asked_reading(evidence, ranked, after, disambiguator)):
            ranked = [asked]
        elif not _agreeing(evidence, ranked) and (noun := noun_reader.reading_of(evidence)):
            # تَبَسُّمُكَ، أَدْوَمُهَا: a masdar or an elative the dictionary lacks, by sarf's shapes, its pronoun split off
            ranked = [noun]
        steps.append((evidence, ranked))
    out = [_reading(*step) for step in steps]
    for i, (evidence, ranked) in enumerate(steps):
        # وَجَدَ: the context ranker keeps its top readings only, and may keep none but ones that
        # double a letter the reader left single (وَجَدّ); then the word's whole list is read too
        if not ((found := vowel_agreement(evidence, out[i].get("diac", ""))) and found[1]):
            continue
        wider = _widened(tokens[i], ranked)
        better = best_reading(evidence, wider)
        if better and (vowel_agreement(evidence, better.get("diac", "")) or found)[1] < found[1]:
            out[i], steps[i] = better, (evidence, wider)
    # ضُرِبْتُ، أُعْطِيتُ: a past verb's ending names its doer (تُ أنا، تَ أنت، تْ هي), and sarf's table reads it off
    # the typed vowels; a reading of another doer, agreeing only where the dictionary leaves the ending bare
    # or not at all (it lacks most passives), is not the word: the one of that doer is, or the doer is the table's.
    # One the typed vowels contradict is no evidence for the verb either (كُسِيتُ is كَسَا's passive, not كَسِيَ)
    for i, (evidence, ranked) in enumerate(steps):
        if out[i].get("pos") == "verb" and out[i].get("asp") == "p" and (said := verb_reader.reading_of(evidence, _seen_verb)) \
                and said.get("asp") == "p":
            keys = (*DOER, "lex") if vowel_agreement(evidence, out[i].get("diac", "")) is None else DOER
            if not _same(out[i], said, keys):
                out[i] = next((r for r in _widened(tokens[i], ranked) if r.get("asp") == "p" and _same(r, said, keys)),
                              {**out[i], **{key: said[key] for key in keys if key in said}})
    # a noun already joined to "my" takes no second mudaf ilayh: before a genitive noun
    # أَبِي is the six nouns' jarr (أَبِي الطَّبِيبِ), not "my father"; so before a name that
    # shows no case at all (أَبِي مُوسَى), which a jarr fits as well as any
    for i in range(len(out) - 1):
        after = out[i + 1]
        if out[i].get("enc0") == "1s_poss" and after.get("pos", "").startswith("noun") \
                and (after.get("cas") == "g" or after.get("pos") == "noun_prop" and typed_case(tokens[i + 1]) is None):
            word, ranked = steps[i]
            out[i] = best_reading(word, [r for r in ranked if r.get("enc0") != "1s_poss"
                                         and six_noun_case(base_of(word, r.get("atbtok")), r.get("lex") or "")]) or out[i]
    # صِلْ مَنْ قَطَعَكَ: a relative's صلة is a sentence, so a word after it that the typed vowels read
    # as well as a verb (قَطَعَكَ the verb, or the noun "your pieces") is that verb. Opening the sentence
    # مَنْ، ما may be a question or a negation instead (مَنْ أَبُوكَ، مَا أَنْتَ), so only one after a word.
    # The relative may be written onto a preposition (عَمَّنْ ظَلَمَكَ: عن + من), its own tag then the enclitic's
    for i in range(2, len(out)):
        relative = out[i - 1].get("pos") == "pron_rel" or str(out[i - 1].get("enc0", "")).endswith("_rel")
        if relative and out[i].get("pos") != "verb":
            word, ranked = steps[i]
            here = vowel_agreement(word, out[i].get("diac", ""))
            verb = best_reading(word, [r for r in _widened(tokens[i], ranked) if r.get("pos") == "verb"])
            said = vowel_agreement(word, verb.get("diac", "")) if verb else None
            # the verb reads the typed vowels at least as well, or the reading kept contradicts them (ظُلْمُكَ for ظَلَمَكَ)
            if said is not None and (here is None or said >= here):
                out[i] = verb
    # أَكْرَمَ مُصْطَفَى يَحْيَى: nothing before the sentence's first word puts it in nasb, so a typed fatha
    # the past verb reads as well as a noun's nasb (the elative أَكْرَمَ, here before a name showing no case) is that verb
    if out and out[0].get("cas") == "a" and typed_case(tokens[0]) == "a":
        word, ranked = steps[0]
        verb = best_reading(word, [r for r in _widened(tokens[0], ranked) if r.get("pos") == "verb" and r.get("asp") == "p"])
        if verb and best_reading(word, [verb, out[0]]) is verb:
            out[0] = verb
    # الْعِلْمُ أَنْفَعُ مِنَ الْمَالِ: after a noun opening the sentence in raf', a word that is either
    # أَفْعَلُ "I do" or the elative is that noun's khabar, and a verb khabar needs a pronoun back to
    # its مبتدأ (رابط جملة الخبر, Ibn Aqil on the Alfiyya); "I" with nothing on it has none
    if len(out) > 1 and out[0].get("pos", "").startswith("noun") and typed_case(tokens[0]) == "u" \
            and out[1].get("pos") == "verb" and out[1].get("per") == "1" and out[1].get("enc0") in ("0", "na", None) \
            and (elative := noun_reader.reading_of(steps[1][0])):
        out[1] = elative
    # وَالْآخِرَةُ خَيْرٌ وَأَبْقَى: a word joined by و onto an elative, which the typed vowels read as that
    # elative as well as a verb ("and I remain"), is the elative: a verb is joined onto a noun only when the
    # noun is like a verb, as the active participle is (Ibn Aqil on the Alfiyya V3 p244), and an elative is not
    for i in range(1, len(out)):
        if out[i].get("pos") == "verb" and out[i - 1].get("pos") in NOUNISH \
                and elative_shape(out[i - 1].get("pattern", ""), out[i - 1].get("lex", "")):
            word = steps[i][0]  # the only shape of sarf's nouns a verb spells too is أَفْعَل, the elative's
            if (noun := _joined_noun(word, "و", "CONJ", prc2="wa_conj")) and best_reading(word, [noun]):
                out[i] = noun
    # مَنْ جَدَّ وَجَدَ: a مضاف needs its مضاف إليه straight after it, so a bare construct noun
    # before a و, a preposition or nothing is not the word typed (here the verb جَدَّ)
    # لَا رَيْبَ فِيهِ: after لا النافية للجنس the noun's missing tanween is لا's building on fatha
    # (closed_words la_jins, Tasheel 3.7.3 p69), not a مضاف waiting for its مضاف إليه
    for i, reading in enumerate(out):
        after_la = i > 0 and is_one(bare_letters(out[i - 1].get("diac", "")), "la_jins")
        if _bare_construct(reading) and not after_la and not _takes_mudaf_ilayh(*((out[i + 1], tokens[i + 1]) if i + 1 < len(out) else ({}, ""))):
            word, ranked = steps[i]
            # the word's whole list too (أَكْبَرُ's own indefinite reading may be ranked out), never a guessed name
            out[i] = best_reading(word, [r for r in _widened(tokens[i], ranked)
                                         if not _bare_construct(r) and r.get("pos") != "noun_prop"]) or reading
    # نصر زيد بكرا، زيد نصر بكرا: every منصوب has its عامل (Ibn Aqil on the Alfiyya, المفعول به).
    # A noun read in nasb (بكرا's alif of tanween is written, typed vowels or none), in a line of
    # nouns alone, has none but a verb before it, or is that verb when the fatha is typed (زَيْدٌ أَكْرَمَ
    # ضَيْفًا: the fatha a diptote's nasb would be is the past verb's; أَبُوهُ's و is raf', no fatha
    # to give the verb): the first word that reads as a past verb adding
    # no letter the writing lacks (زَيَّدَ's shadda: الأصل عدم الزيادة). Typed vowels still choose, and a
    # typed tanween is a sign of the noun (Ibn Aqil V1 p15: بالجر والتنوين): زَيْدٌ فَاهِمٌ الدَّرْسَ, never فَأَهِم.
    # A pronoun is a noun too (هُوَ أَكْرَمَ ضَيْفًا: المضمر من أقسام الاسم, Ibn Aqil on the Alfiyya);
    # the word after a مضاف is مجرور (وَالثَّانِيَ اجْرُرْ): هَذَا كِتَابُ أَحْمَدَ's fatha is a diptote's jarr.
    # A participle with its tanween before it is its عامل already (Ibn Aqil V3 p106: كفعله اسم فاعل في العمل …
    # هذا ضارب زيدا الآن أو غدا): أَنَا ضَارِبٌ زَيْدًا has no verb in it
    nasb = next((i for i, r in enumerate(out) if i and r.get("cas") == "a" and not _bare_construct(out[i - 1])), None)
    if nasb and all(r.get("pos") in NOUNISH or r.get("pos", "").startswith("pron") for r in out) \
            and not any(has_tanween(word) and participle_shape(r.get("pattern", "")) for word, r in zip(tokens[:nasb], out)):
        for i in range(nasb + (typed_case(tokens[nasb]) == "a")):
            verb = not has_tanween(tokens[i]) and best_reading(tokens[i], [
                r for r in _widened(tokens[i], steps[i][1]) if r.get("pos") == "verb" and "ّ" not in r.get("diac", "")])
            if verb:
                out[i] = verb
                break
    for i, said in paused.items():
        out[i] = {**out[i], "said": said}
    return out


def as_said(tokens: list[str], picks: list[dict]) -> list[str]:
    """The words as said joined to the next, which the parser and the cards read: a هاء السكت's
    word without it (pick reads مَالِيَهْ as مَالِيَ), every other word as typed."""
    return [picked.get("said") or token for token, picked in zip(tokens, picks, strict=True)]


def _without_sakt(tokens: list[str], i: int, disambiguator=None) -> tuple[str, list[dict]] | None:
    """مَالِيَهْ، هِيَهْ: a word with a هاء السكت's shape is read as said joined to the next, without
    it (Mufassal: إذا أدرجت قلت مالي), when what is left is built on its vowel (closed_words
    haa_sakt): a pronoun, a question or pointing word (لِمَ، عَلَامَ), or a word with ياء المتكلم."""
    if not (rest := sakt_off(tokens[i])):
        return None
    ranked = (_ranked([*tokens[:i], rest, *tokens[i + 1:]], disambiguator) or [[]] * len(tokens))[i]
    found = _reading(rest, ranked)
    built = is_mabni(found.get("pos", "")) or str(found.get("enc0", "")).startswith("1s")
    return (rest, ranked) if built and _agreeing(rest, ranked) else None


def _name_in_nasb(typed: str, disambiguator=None) -> dict | None:
    """رَأَيْتُ زَيْدًا: CAMeL files a name without the alif its nasb tanween is written on, so a word
    none of its readings fits (زَيَّدَا is two vowels off), ending in that alif, is the word its letters
    before it spell, in nasb. One whose stem it does not know at all stays unread (مُسْرِعًا), and
    one with another vowel on that alif or before it is no nasb (مُحَمَّدُا)."""
    marked = letters(typed)
    if len(marked) < 3 or marked[-1][0] != "ا" or (marked[-1][1] | marked[-2][1]) - {"ً"}:
        return None
    stem = "".join(letter + "".join(marks - {"ً"}) for letter, marks in marked[:-1])
    ranked = (_ranked([stem], disambiguator) or [[]])[0]
    known = next((r for r in ranked if NO_ANALYSIS not in r.get("atbtok", "")), None)
    return known and {**known, "cas": "a", "diac": known["diac"] + "ًا", "atbtok": known["diac"] + "ًا"}


def _asked_reading(typed: str, ranked: list[dict], after: str, disambiguator=None) -> dict | None:
    """أَذَاهِبٌ زَيْدٌ: the question hamza (closed_words istifham, a one-letter word) opens the
    sentence before a full clause, written onto its first word; the dictionary lacks it on a
    noun, so the rest of the word is read and the hamza put back as its proclitic, as CAMeL
    writes a وَ (وَ+_ذاهِب). Read so where no reading of the whole word fits its vowels, or where
    the rest is a حرف جر and the next word is typed in jarr (أَفِي اللَّهِ شَكٌّ: no verb or name puts
    the noun after it in jarr, so أَفِي is not "I fulfil")."""
    marked = letters(typed)
    hamza = next((w for w in book_words("istifham") if len(w) == 1), None)
    if not (hamza and len(marked) > 2 and marked[0][0] == hamza and "َ" in marked[0][1]):
        return None
    asked = typed[:len(marked[0][0]) + len("".join(marked[0][1]))]
    rest = typed[len(asked):]
    if _agreeing(typed, ranked) and not (strip_diacritics(rest) in book_words("jarr") and typed_case(after) == "i"):
        return None
    ranked = _rest_readings(rest, disambiguator)
    if not _agreeing(rest, ranked):
        return None
    return _joined_onto(asked, _reading(rest, ranked), "INTERROG_PART", prc3="Aa_ques")


def _emphasis_lam(typed: str, disambiguator=None) -> dict | None:
    """وَإِنَّكَ لَعَلَى خُلُقٍ عَظِيمٍ: after إنّ the لام of emphasis comes onto its khabar, a jar-majroor
    or ظرف too (closed_words `khabar_lam`). The dictionary never writes a لام onto a حرف جر or ظرف, so
    it reads لِ+عَلِيّ or a verb; but a جار takes no جار after it, so the word is that لام on the
    particle, after إنّ or not (وَاللَّهِ لَعَلَى الْحَقِّ أَنْتَ: the لام of the oath's answer). Not with a
    typed kasra (لِمَنْ: the جار on مَن who), nor where a verb reads the letters too (إِنَّ اللَّهَ لَعَنَ
    الْكَافِرِينَ، لمن bare as لُمْنَ). A لام typed with a fatha onto any other word that no reading of the
    whole word fits (لَأَنْتُمْ أَشَدُّ رَهْبَةً: the dictionary has only لِ+ a verb) is that لام too: the
    jarr لام takes a fatha only before a pronoun joined on (لَكَ), which the dictionary reads whole
    (closed_words ghair_amila_other `_fatha_lam`)."""
    lam = book_map("ghair_amila_other", "khabar_lam")
    marked = letters(typed)
    if not (marked and marked[0][0] == lam["lam"] and not marked[0][1] - {"َ"}):
        return None
    said = typed[:len(marked[0][0]) + len("".join(marked[0][1]))]
    rest = typed[len(said):]
    whole = [r for r in (_ranked([typed], None) or [[]])[0] if _agreeing(typed, [r])]
    if any(strip_diacritics(rest) in book_words(family) for family in lam["onto"]):
        if any(r.get("pos") == "verb" for r in whole):
            return None
    elif whole:
        return None
    ranked = _rest_readings(rest, disambiguator)
    return _joined_onto(said, _reading(rest, ranked), "EMPHATIC_PART", prc1="la_emph") if _agreeing(rest, ranked) else None


def _rest_readings(rest: str, disambiguator=None) -> list[dict]:
    """The readings of what is left once a one-letter particle is off: the word itself, not an
    abbreviation spelled like it (فِي)."""
    return [r for r in (_ranked([rest], disambiguator) or [[]])[0] if r.get("pos") != "abbrev"]


def _joined_noun(typed: str, letter: str, tag: str, **proclitic) -> dict | None:
    """وَأَدْوَمُ: the noun sarf's shapes read once a one-letter particle is off (noun_reader takes ال,
    a ة and a pronoun, not a particle before them), the particle put back."""
    marked = letters(typed)
    if not (marked and marked[0][0] == letter):
        return None
    said = typed[:len(marked[0][0]) + len("".join(marked[0][1]))]
    noun = noun_reader.reading_of(typed[len(said):])
    return _joined_onto(said, noun, tag, **proclitic) if noun else None


def _joined_onto(said: str, found: dict, tag: str, **proclitic) -> dict:
    """A reading with a one-letter particle put back in front of it, as CAMeL writes a وَ (وَ+_ذاهِب)."""
    return {**found, "diac": said + found.get("diac", ""), "atbtok": f"{said}+_" + found.get("atbtok", ""),
            "catib6": "PRT+" + found.get("catib6", ""), "ud": "PART+" + found.get("ud", ""),
            "bw": f"{said}/{tag}+" + found.get("bw", ""), "pattern": said + found.get("pattern", ""), **proclitic}


def _added(reading: dict, typed: str) -> int:
    """The shaddas a reading puts on that the typed word lacks: letters the writing does not show."""
    return reading.get("diac", "").count("ّ") - typed.count("ّ")


DOER = ("per", "gen", "num")


def _same(reading: dict, said: dict, keys: tuple[str, ...]) -> bool:
    """The reading has what sarf's table said of these (its person, gender, number, verb), where both said one;
    a verb by its letters, the two spelling its last vowel otherwise (ضَرَب، ضَرَبَ). A reading that leaves one
    unsaid does not contradict it (the dictionary's أَلَسْتُ is ليس, its number left "-")."""
    return all(bare_letters(reading.get(key) or "") == bare_letters(said[key]) for key in keys
               if "-" not in (said.get(key, "-"), reading.get(key, "-")))


def _agreeing(typed: str, ranked: list[dict]) -> bool:
    """Some real reading (not the no-analysis guess), spelled with the typed letters (الحاقّة is no
    إلحاقه), has no vowel against the typed ones."""
    spelled = [bare_letters(c) for c, _ in letters(typed)]
    return best_reading(typed, [r for r in ranked if NO_ANALYSIS not in r.get("atbtok", "")
                                and [bare_letters(c) for c, _ in letters(r.get("diac", ""))] == spelled]) is not None


def _widened(token: str, ranked: list[dict]) -> list[dict]:
    """The context ranker's readings, then the word's whole list, never one CAMeL could not analyse."""
    return [r for r in ranked + (_ranked([token], None) or [[]])[0] if NO_ANALYSIS not in r.get("atbtok", "")]


def _bare_construct(reading: dict) -> bool:
    """A noun read as a مضاف with no pronoun on it."""
    return reading.get("pos") in ("noun", "adj") and reading.get("stt") == "c" and reading.get("enc0") in ("0", "na", None)


def _takes_mudaf_ilayh(after: dict, typed: str = "") -> bool:
    """The next word can be a مضاف إليه: a noun or pronoun with no و, ف or preposition on it,
    not typed with a damma. A مضاف إليه is مجرور (Alfiyya: وَالثَّانِيَ اجْرُرْ), and no جرّ is a
    damma (a diptote's is a fatha), so بَرَدَ before الْجَوُّ is the verb, not "the hail of"."""
    return typed_case(typed) != "u" and after.get("pos", "").startswith(("noun", "adj", "pron", "abbrev", "digit")) and all(
        after.get(prc, "0") in ("0", "na") for prc in ("prc1", "prc2", "prc3"))


def analyze_sentence(sentence: str, picks: list[dict] | None = None) -> list[dict[str, Any]]:
    """Tokenise and analyse a sentence from `picks` (see `pick`; read here by MLE when
    absent), falling back to word-level analysis when CAMeL gives none."""
    tokens = words(sentence)
    if not tokens:
        return []

    if _CAMEL_AVAILABLE:
        picks = picks or pick(tokens)
        tokens = as_said(tokens, picks)
        before = ["", *map(strip_diacritics, tokens[:-1])]
        return [_analysis_dict_from_camel(t, a, b, n, r.get("asp", "")) if a else analyze_word(t)
                for t, a, b, n, r in zip(tokens, picks, before, [*tokens[1:], ""], [*picks[1:], {}], strict=True)]

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
