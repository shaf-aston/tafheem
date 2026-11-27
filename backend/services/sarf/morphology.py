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
from dataclasses import dataclass, field
from typing import Any, NamedTuple

from backend.config import get_settings
from backend.services.text.arabic_text import HAS_PYARABIC, bare_letters, hamzah_folded, has_arabic, shown_root, strip_diacritics, words
from backend.services.sarf import engine, expects, noun_reader
from backend.services.sarf import verb_reader
from backend.services.quran import corpus as quran_corpus
from backend.services.nahw.book import book_map, book_words, condition_of, elative_shape, is_built_word, is_mabni, is_one, kaffa_sister, declined_with_ma, participle_shape, sakt_off, six_noun_case
from backend.services.text.harakat import CAMEL_CASE, CASE_NAME, DAMMA, FATHA, NO_ANALYSIS, SHADDA, SUKUN, TANWEEN, base_of, best_reading, build_nun, has_tanween, nearest_reading, own_letters, past_passive_shape, weak_last, moved_for_wasl, no_vowels_typed, paused, stuck_letters, typed_case, unread, vowel_agreement, letters

logger = logging.getLogger(__name__)

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
    if engine.bw2ar is not None:
        try:
            return engine.bw2ar.map(bw)
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
    verb: bool = False  # read as a verb: its lemma is looked for among its root's verbs (roots.lemma_of)


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


def reading_lemma(word: str, a: dict, root: str | None = None) -> str:
    """The bare lemma of one reading, for the cards and the parser alike: a lemma the word does not carry
    is not its lemma (رأيت filed under راوند), so the Qur'an's for its root (roots.lemma_of)."""
    from backend.services.dictionary import roots  # it reads with this module
    pos = (a.get("pos") or "").lower()
    return roots.lemma_of(strip_diacritics(a.get("lex") or a.get("diac") or word), strip_diacritics(word),
                          reading_root(a) if root is None else root, pos == "verb")


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
    if a.get("pos") != "verb" and (verb_reader.called(before, after, after_read) or verb_reader.noun_marked(word, before, a.get("lex") or "", after)):
        return a  # يَا رَبِّ، رَبِّ اغْفِرْ لِي: a noun called, not رَبَّى's command; عَلَى مَالِ: a noun in jarr
    governed = any(is_one(before, family, "before_a_present_verb") for family in ("jazm", "nasb_mudari"))
    # a verb or a noun, so rooted; a reading the typed vowels contradict tells nothing of the word's root (كِلْ is no كُلْ)
    root = root_in_arabic(a.get("root") or "", a.get("lex") or "", word) \
        if vowel_agreement(word, a.get("diac") or "") is not None else ""
    # فَأَنْذِرْ: the letters CAMeL files as joined before (فَ+) are no part of the command; the table reads the verb's own
    # (base_of keeps the word whole where CAMeL's split does not fit the letters typed)
    front = sum(len(p) - 1 for p in strip_diacritics(a.get("atbtok") or "").split("_") if p.endswith("+"))
    own = own_letters(word, front, 0) if front and base_of(word, a.get("atbtok")) != strip_diacritics(word) else word
    # the kasra before hamzat al-wasl is the word's own (سَمِّ اللَّهَ) or a paused sukun (أَقِمِ الصَّلَاةَ)
    cell = verb_reader.command(own, governed, root, said=has_verb) or verb_reader.command(paused(own, after), governed, root, said=has_verb)
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

    lemma = reading_lemma(word, a, root_ar)
    guessed = NO_ANALYSIS in a.get("atbtok", "")

    cas = a.get("cas", "na") or "na"
    # A built word (a past verb, a pronoun) has no case: its last vowel is not one. Nor is a
    # noun's attached pronoun's (the fatha of أَخِيكَ is the kaf's), and on ياء المتكلم the case
    # is unseen (the fatha of سُلْطَانِيَ is the ya's own).
    unseen = is_mabni(pos, a.get("asp"), base_of(word, a.get("atbtok"))) or a.get("enc0") == "1s_poss"
    pronoun = stuck_letters([{"form": piece} for piece in (a.get("atbtok") or "").split("_")], word) if pos in NOUNISH else 0
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


def has_verb(verb: str, root: str) -> bool:
    """The dictionary's training text has this verb (يَقِفْ، وَقَفَ) of this root (وقف) as typed: every letter, its
    hamzah's seat too (أَكَلَ is not آكُلُ), a shadda as the letter it doubles (وَرِثَ is not وَرَّثَ), and every vowel
    both write. A present is listed with no mood ending (يَقِف), so a jussive is matched as its present."""
    return any(a.get("pos") == "verb" and a.get(_LIKELIHOOD, _NEVER_SEEN) > _NEVER_SEEN
               and _listed_root(a, root) and _spelled_as(verb, a.get("diac") or "")
               for a in _analyses(strip_diacritics(verb)))


def _listed_root(a: dict, root: str) -> bool:
    """The reading is of `root`, its hamzah on any seat (يَأْمُرُ's ءمر is أمر) and its weak letter either و or ي: the
    dictionary writes every weak letter # and never says which (بَاعَ and قَالَ alike: ب.#.ع، ق.#.ل), where reading_root
    writes it و (بَاعَ: بوع)."""
    return reading_root(a).replace("ي", "و") == hamzah_folded(root).replace("ي", "و")


def _spelled_as(typed: str, listed: str) -> bool:
    """`typed` is the word the dictionary lists: the same letters and shaddas, and no vowel either writes differently."""
    return strip_diacritics(listed) == strip_diacritics(typed) and listed.count(SHADDA) == typed.count(SHADDA) \
        and vowel_agreement(typed, listed) is not None


_WASL = str.maketrans("ٱ", "ا")  # the dictionary writes a past's hamzat al-wasl so (ٱِسْتَغْفَر)


def _analyses(word: str) -> list[dict]:
    """Every CAMeL reading of one word, the likeliest lemma first; [] when CAMeL is not there.

    The analyzer lists readings in no order of likelihood, so a first pick from its list
    took يترك for وَتَر rather than تَرَك and يكن for كَنّ rather than كان. Each reading
    carries how often its lemma, as that part of speech, occurs in CAMeL's training text
    (pos_lex_logprob); every pick below that falls back to "the first" now means the likeliest.
    """
    if engine.camel is None:
        return []
    try:
        analyses = engine.camel.analyze(word)
    except Exception as exc:
        logger.debug("CAMeL analyze error for '%s': %s", word, exc)
        return []
    return sorted(map(verb_reader.mended, analyses), key=lambda a: -a.get(_LIKELIHOOD, _NEVER_SEEN))


def is_listed_verb(word: str) -> bool:
    """The bare letters are a verb's own lemma in the dictionary (أَمْسَكَ، أَنْزَلَ، أَجْلَسَ), not only some
    other verb's form: أغفر is only غَفَرَ's أَغْفِرُ, for the dictionary knows no أَغْفَرَ."""
    bare = strip_diacritics(word)
    return any(a.get("pos") == "verb" and strip_diacritics(a.get("lex") or "") == bare for a in _analyses(bare))


def _analyze_word_camel_only(word: str) -> dict[str, Any] | None:
    """Word-level CAMeL Analyzer with diacritic-guided best-analysis selection."""
    if engine.camel is None:
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
    if engine.camel is None:
        return [Reading(_analyze_qalsadi(word)["lemma"], "", True)] if engine.qalsadi is not None else []
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
        reading = Reading(strip_diacritics(a.get("lex") or ""), root, rooted, pos == "verb")
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
        result = engine.qalsadi.lemmatize(word)  # type: ignore[union-attr]
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
    if engine.camel is not None:
        return "camel-tools"
    if engine.qalsadi is not None:
        return "qalsadi"
    return "pyarabic" if HAS_PYARABIC else "bare"


def analyze_word(word: str) -> dict[str, Any]:
    """Morphological analysis of a single Arabic word (no sentence context)."""
    word = word.strip()
    if not word or not has_arabic(word):
        return _analyze_bare(word)
    if engine.camel is not None:
        if result := _analyze_word_camel_only(word):
            return result
    return _analyze_qalsadi(word) if engine.qalsadi is not None else _analyze_bare(word)


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
    if _passive_shape_past_joined(word) and verbs:
        # the shape is a past verb's: اسْتُعْمِلَ, which CAMeL lacks, is its active اِسْتَعْمَلَ
        # with the voice read off the vowels, never أَسْتَعْمِلُ
        return next((r for r in verbs if r.get("asp") == "p"), verbs[0])
    # a reading spelled with the letters typed goes first, even one vowel off, before another word's
    # letters that say nothing either way (خُلُقُهُ is خُلْقُهُ, not خَلَقَة)
    same = [r for r in real if [bare_letters(c) for c, _ in letters(r.get("diac", ""))] == [bare_letters(c) for c, _ in letters(word)]]
    # with none agreeing, one spelled as typed (حِجَارَةٌ, which the dictionary has only as حَجّارَةٌ)
    return best_reading(word, same) or nearest_reading(word, same) or best_reading(word, real) or (same or readings)[0]


def _passive_shape_past_joined(word: str) -> bool:
    """فُعِلَ by its vowels, past a joined و or ف that carries its own fatha (فَسُحِبَ، فَأُتِيَ، وَقُتِلَ): that fatha
    is the particle's, so the shape is read on the letters after it."""
    marked = letters(word)
    return past_passive_shape(word) or len(marked) > 3 and marked[0][0] in "فو" and marked[0][1] == {_FATHA} \
        and past_passive_shape(own_letters(word, 1, 0))


def _ranked(tokens: list[str], disambiguator) -> list[list[dict]] | None:
    """Each word's CAMeL readings, best first, from the disambiguator (BERT) and, if it fails,
    the MLE; None when neither reads."""
    for reader in filter(None, (disambiguator, engine.mle)):
        try:
            return [[verb_reader.mended(scored.analysis) for scored in word.analyses] for word in reader.disambiguate(tokens)]
        except Exception as exc:
            logger.warning("CAMeL disambiguation failed: %s", exc)
    return None


def pick(tokens: list[str], disambiguator=None) -> list[dict[str, Any]]:
    """One raw CAMeL reading per word ({} where none is read), shared by the cards and
    the parser. Neighbours rank the readings (MLE, or the parser's BERT), the typed vowels choose:
    each word's WORD_OVERRIDES in order, then the SENTENCE_PASSES over the readings chosen."""
    if not tokens:  # only signs and numbers typed (۝ ٢٨ ۚ): no word, no reading
        return []
    if (all_ranked := _ranked(tokens, disambiguator)) is None:
        return [{} for _ in tokens]

    steps = []  # each word's vowels as evidence, and its ranked readings
    settled = set()  # the words read as a command after a joined ف or و
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
        word = _Word(tokens, i, token, evidence, ranked, after, disambiguator, _reading(evidence, ranked),
                     bool(steps) and _saying(_reading(*steps[-1])))
        for override in WORD_OVERRIDES:
            if found := override(word):
                word.ranked = [found]
                if override is _command_after_joining:
                    settled.add(i)
        steps.append((evidence, word.ranked))
    picked = _Picked(tokens, steps, [_reading(*step) for step in steps], paused, disambiguator, settled)
    for sentence_pass in SENTENCE_PASSES:
        sentence_pass(picked)
    return picked.out


@dataclass(slots=True)
class _Word:
    """One word as pick reads it: the letters typed (`token`, the `i`th of `tokens`), its vowels as `evidence`,
    its readings best first (`ranked`, which an override replaces with its one reading), the word typed after it,
    and the reading its vowels chose before any override (`first`)."""
    tokens: list[str]
    i: int
    token: str
    evidence: str
    ranked: list[dict]
    after: str
    disambiguator: Any
    first: dict
    said_before: bool = False  # the word before is a verb of saying (قَالَ): what follows it opens a sentence of its own


@dataclass(slots=True)
class _Picked:
    """The sentence as pick has read it: the words typed (`tokens`), each word's (evidence, ranked) `steps`, and
    `out`, the reading chosen for each word, which a sentence pass changes in place; `paused`, each هاء السكت word as
    said joined, and the `disambiguator` that ranked the readings."""
    tokens: list[str]
    steps: list[tuple[str, list[dict]]]
    out: list[dict]
    paused: dict[int, str]
    disambiguator: Any
    settled: set[int] = field(default_factory=set)  # the words read as a command after a joined ف or و, which no pass reads as a past again


# ── Word overrides: each returns the one reading the word is, or None to leave it. In order; a later one ──
# ── that fires replaces an earlier one's reading.                                                     ──

def _name_adding_fewer(w: _Word) -> dict | None:
    """The name in nasb (_name_in_nasb), where it adds fewer letters to the writing than the reading chosen."""
    # زيدا typed bare fits the verb زَيَّدَا too, but that one adds a shadda the writing lacks and the name none
    # (الأصل عدم الزيادة), so the name in nasb is read where it adds fewer. A particle stays (الا is إِلَّا)
    agreeing, read = _agreeing(w.evidence, w.ranked), w.first
    if (not agreeing or read.get("pos") == "verb" and _added(read, w.token)) and (name := _name_in_nasb(w.token, w.disambiguator)) \
            and (not agreeing or _added(name, w.token) < _added(read, w.token)):
        return name
    return None


def _named_in_the_quran(w: _Word) -> dict | None:
    """A verb reading that is a name the Qur'an says (_quran_name)."""
    return w.first.get("pos") == "verb" and _quran_name(w.evidence, _widened(w.token, w.ranked)) or None


def _emphasis(w: _Word) -> dict | None:
    """The emphasis nun on a verb, or the لام of emphasis on a word."""
    return _emphasis_nun(w.evidence, w.ranked) or _emphasis_lam(w.evidence, w.disambiguator, _after_fronted_khabar(w.tokens[:w.i]))


def _oath(w: _Word) -> dict | None:
    """فَوَ / تَ / لَ of an oath."""
    return _fa_before_oath(w.evidence, w.ranked, w.disambiguator) or _oath_ta(w.evidence, w.ranked, w.disambiguator) \
        or _oath_lam(w.evidence)


def _ma_in_jarr(w: _Word) -> dict | None:
    """The asking مَا written with its حرف جر as one word: فِيمَ، عَمَّ، لِمَاذَا (_jarred_ma)."""
    return _jarred_ma(w.evidence)


def _ma_kaffa(w: _Word) -> dict | None:
    """An إنّ sister with مَا الكافة written onto it: إِنَّمَا، كَأَنَّمَا (_kaffa_ma)."""
    return _kaffa_ma(w.evidence, w.ranked)


def _name_made_dual_or_plural(w: _Word) -> dict | None:
    """أَقَائِمٌ الزَّيْدَانِ، جَاءَ الزَّيْدُونَ: a name with ال takes the dual and the sound plural as any noun does
    (an ال on a name says it is counted, made common), but the dictionary files these letters as a name of
    their own (زَيْدان) or not at all. Where the letters before the ending are a name it knows, the word is
    that name made dual or plural, its case from the ending; يْنِ is told from ِينَ by the vowels typed."""
    marked, first = letters(w.token), w.first
    if len(marked) < 6 or bare_letters(w.token)[:2] != "ال" or first.get("pos") != "noun_prop" or first.get("num") in ("d", "p"):
        return None
    (one, _one_marks), (nun, nun_marks), before = marked[-2], marked[-1], marked[-3][1]
    if nun != "ن":
        return None
    dual, plural = one == "ا" or one == "ي" and (FATHA in before or "\u0650" in nun_marks), \
        one == "و" or one == "ي" and ("\u0650" in before or FATHA in nun_marks)
    if dual == plural:
        return None
    stem = "".join(letter + "".join(marks - {FATHA, "\u0650", DAMMA}) for letter, marks in marked[2:-2])
    name = next((r for r in (_ranked([stem], w.disambiguator) or [[]])[0]
                 if r.get("pos") == "noun_prop" and r.get("num") == "s" and r.get("gen") == "m"), None)
    if not name:
        return None
    ending = {"ا": "َانِ", "و": "ُونَ"}.get(one) or ("َيْنِ" if dual else "ِينَ")
    number, case = ("d" if dual else "p"), ("n" if one in "او" else "a")
    spelled = "ال" + name["diac"] + ending
    return {**name, "num": number, "form_num": number, "cas": case, "stt": "d", "prc0": "Al_det",
            "diac": spelled, "atbtok": spelled}


def _ayy_ma(w: _Word) -> dict | None:
    """أيّ with ما الزائدة written onto it: أَيَّمَا (_declined_ma)."""
    return _declined_ma(w.evidence)


def _a_particle(w: _Word) -> dict | None:
    """إنّ's sister with "me" shortened, a particle that only comes before a noun, or a particle with a twin."""
    return _inna_short_me(w.evidence) or _noun_only_particle(w.evidence) or _twin_particle(w.evidence, w.i == 0)


def _hamza_seat(w: _Word) -> dict | None:
    """A hamza typed on a seat the dictionary spells otherwise, where no reading agrees."""
    return not _agreeing(w.evidence, w.ranked) and (_hamza_written_waw(w.evidence, w.disambiguator)
                                                    or _hamza_stem_seat(w.evidence, w.disambiguator)) or None


def _command_after_joining(w: _Word) -> dict | None:
    """فَأْتُوا، فَأْذَنُوا، وَأْمُرْ: after a joined ف or و the command's hamzat al-wasl drops and its first-letter hamza
    is said with a sukun, which no past or present of the word carries; the reading with the ف or و split off is the
    command (_as_command reads it off sarf's table), never فاتُوا, another root's past spelled with the same letters."""
    marked = letters(w.evidence)
    if len(marked) < 3 or marked[0][0] not in "فو" or marked[1][0] != "أ" or marked[1][1] != {SUKUN}:
        return None
    # وَأْدُ الْبَنَاتِ: a damma or tanween on the last letter is a noun's case, and a fatha a past verb's, which no command
    # ends on (its ending is a sukun, a dropped letter, or ـوا ـي ـا ـنَ)
    last, marks = marked[-1]
    if has_tanween(w.evidence) or DAMMA in marks or FATHA in marks and last != "ن":
        return None
    joined = [r for r in w.ranked if strip_diacritics(r.get("atbtok") or "").startswith(marked[0][0] + "+_")]
    commands = [(r, read) for r in joined if (read := _as_command(w.evidence, r, "", w.after)).get("asp") == "c"]
    # the command is Form I's (اِيذَنُوا), so the reading whose lemma is the root's own past (أَذِنَ), not آذَنَ
    # (أَذِنَ, not آذَنَ or أَذَّنَ: the lemma is the root's bare letters, its hamza unseated and no shaddah)
    plain = lambda r, read: "\u0651" not in (r.get("lex") or "") and strip_diacritics(r.get("lex") or "") == (read.get("root") or "").replace(".", "")  # noqa: E731
    if found := next((r for r, read in commands if plain(r, read)), None):
        return found
    # فَأْتِيَا، وَأْتُوا: no reading has the bare past (أَتَى is no root's letters, آتِي a noun), so sarf's table's,
    # tagged a verb with the ف or و split off, as the cards and the parser both read it
    table = verb_reader.reading_of(w.evidence, _seen_verb, None, has_verb) if commands else None
    if table and table.get("asp") == "c" and strip_diacritics(table.get("atbtok") or "").startswith(marked[0][0] + "+_"):
        return {"lex": base_of(w.evidence, table.get("atbtok")), **table, "diac": w.evidence}
    return commands[0][0] if commands else None


def _by_shape(w: _Word) -> dict | None:
    """The first of: a command's answer; where no reading agrees, sarf's verb table; the first word asked;
    where none agrees, sarf's noun shapes and a feminine sound plural."""
    disagreeing = lambda: not _agreeing(w.evidence, w.ranked)  # noqa: E731, asked only as each step is reached
    return (_answer_command(w.tokens[:w.i], w.token, w.evidence, w.ranked)
            or not _agreeing(w.evidence, w.ranked, undoubled=True) and _table_verb(w.token, w.evidence, w.ranked)
            or (w.i == 0 or w.said_before) and _asked_reading(w.evidence, w.ranked, w.after, w.disambiguator)
            # تَبَسُّمُكَ، أَدْوَمُهَا: a masdar or an elative the dictionary lacks, by sarf's shapes, its pronoun split off;
            # one with a joining و or ف on it (وَإِقَامِ الصَّلَاةِ) is that noun with the particle put back
            or disagreeing() and (noun_reader.reading_of(w.evidence) or next(
                filter(None, (_joined_noun(w.evidence, letter, "CONJ", prc2=f"{name}_conj") for letter, name in _JOINING)), None))
            or disagreeing() and _sound_fem_plural(w.evidence, w.disambiguator)
            or None)


WORD_OVERRIDES = (_name_adding_fewer, _named_in_the_quran, _emphasis, _oath, _ma_in_jarr, _ma_kaffa, _ayy_ma, _a_particle,
                  _hamza_seat, _by_shape, _name_made_dual_or_plural, _command_after_joining)


# ── Sentence passes: each reads the readings the words chose and changes the ones the sentence says ──
# ── are another; in order, after every word's overrides.                                            ──


def _wider_list(p: _Picked) -> None:
    """A word whose chosen reading is a vowel off the typed ones is read again from its whole list."""
    tokens, steps, out = p.tokens, p.steps, p.out
    for i, (evidence, ranked) in enumerate(steps):
        # وَجَدَ: the context ranker keeps its top readings only, and may keep none but ones that
        # double a letter the reader left single (وَجَدّ); then the word's whole list is read too
        if not ((found := vowel_agreement(evidence, out[i].get("diac", ""))) and found[1]):
            continue
        wider = _widened(tokens[i], ranked)
        better = best_reading(evidence, wider)
        if better and (vowel_agreement(evidence, better.get("diac", "")) or found)[1] < found[1]:
            out[i], steps[i] = better, (evidence, wider)


def _past_verb_doer(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # ضُرِبْتُ، أُعْطِيتُ: a past verb's ending names its doer (تُ أنا، تَ أنت، تْ هي), and sarf's table reads it off
    # the typed vowels; a reading of another doer, agreeing only where the dictionary leaves the ending bare
    # or not at all (it lacks most passives), is not the word: the one of that doer is, or the doer is the table's.
    # One the typed vowels contradict is no evidence for the verb either (كُسِيتُ is كَسَا's passive, not كَسِيَ)
    for i, (evidence, ranked) in enumerate(steps):
        if i not in p.settled and out[i].get("pos") == "verb" and out[i].get("asp") == "p" and (said := verb_reader.reading_of(evidence, _seen_verb)) \
                and said.get("asp") == "p":
            keys = (*DOER, "lex") if vowel_agreement(evidence, out[i].get("diac", "")) is None else DOER
            if not _same(out[i], said, keys):
                out[i] = next((r for r in _widened(tokens[i], ranked) if r.get("asp") == "p" and _same(r, said, keys)),
                              {**out[i], **{key: said[key] for key in keys if key in said}})


def _my_before_a_genitive(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # a noun already joined to "my" takes no second mudaf ilayh: before a genitive noun
    # أَبِي is the six nouns' jarr (أَبِي الطَّبِيبِ), not "my father"; so before a name that
    # shows no case at all (أَبِي مُوسَى), which a jarr fits as well as any
    for i in range(len(out) - 1):
        after = out[i + 1]
        if out[i].get("enc0") == "1s_poss" and after.get("pos", "").startswith("noun") \
                and (after.get("cas") == "g" or after.get("pos") == "noun_prop" and typed_case(tokens[i + 1]) is None):
            word, ranked = steps[i]
            # a plural's dropped ن needs a jarr seen after it: before a caseless name (صَدِيقِي سَامِر) it stays "my"
            out[i] = best_reading(word, [r for r in ranked if r.get("enc0") != "1s_poss"
                                         and six_noun_case(base_of(word, r.get("atbtok")), r.get("lex") or "")]) \
                or (after.get("cas") == "g" and _construct_plural(word, ranked, out[i])) or out[i]


def _verb_after_its_governor(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # صِلْ مَنْ قَطَعَكَ، هَلْ نَضَجَ التِّينُ: a word after a governor that wants a verb (expects.json: لم، لن، هل،
    # a relative whose صلة is a sentence ...) which the typed vowels read as well as a verb (قَطَعَكَ the verb, or
    # the noun "your pieces") is that verb. A relative opening the sentence may be a question instead (مَنْ أَبُوكَ).
    # A word that itself wants the verb after it (ما لَمْ تَسْتَطِعْ: لم puts its verb in jazm) is that particle, which
    # the relative's sentence begins with, never the verb its letters also spell
    for i in range(1, len(out)):
        if out[i].get("pos") != "verb" and expects.verb_after(tokens, out, i) and not (
                i + 1 < len(out) and expects.verb_after(tokens, out, i + 1)):
            word, ranked = steps[i]
            here = vowel_agreement(word, out[i].get("diac", ""))
            verb = best_reading(word, [r for r in _widened(tokens[i], ranked) if r.get("pos") == "verb"]) \
                or (unread(ranked) and no_vowels_typed([word]) and _table_verb(word, word, [], bare=True) or None)
            said = vowel_agreement(word, verb.get("diac", "")) if verb else None
            # the verb reads the typed vowels at least as well, or the reading kept contradicts them (ظُلْمُكَ for ظَلَمَكَ);
            # a name the dictionary files, typed with vowels (هَلْ سَامِر مَوْجُود), stays a name while it fits them: its own vowels are only
            # partly marked, so a verb that marks more of them is not a better fit
            name = out[i].get("pos") == "noun_prop" and not no_vowels_typed([word])
            # nor one that puts on a shadda the vowelled word lacks while the reading kept puts on none (أَبُوهُ is
            # "his father", not أَبُّوهُ): the writing shows every letter (الأصل عدم الزيادة)
            added = verb and not no_vowels_typed([word]) and _added(verb, word) > max(_added(out[i], word), 0)
            if said is not None and not added and (here is None or not name and said >= here):
                out[i] = verb


def _first_word_past(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # أَكْرَمَ مُصْطَفَى يَحْيَى: nothing before the sentence's first word puts it in nasb, so a typed fatha
    # the past verb reads as well as a noun's nasb (the elative أَكْرَمَ, here before a name showing no case) is that verb;
    # with a pronoun on it the case is the vowel before the pronoun (خَلَقَكُمْ: not the noun خَلَق "worn" in nasb)
    pronoun = "".join(part[1:] for part in strip_diacritics(out[0].get("atbtok") or "").split("_") if part.startswith("+")) if out else ""
    if out and out[0].get("cas") == "a" and typed_case(tokens[0], len(pronoun)) == "a":
        word, ranked = steps[0]
        verb = best_reading(word, [r for r in _widened(tokens[0], ranked) if r.get("pos") == "verb" and r.get("asp") == "p"])
        if verb and best_reading(word, [verb, out[0]]) is verb:
            out[0] = verb


def _elative_khabar(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # الْعِلْمُ أَنْفَعُ مِنَ الْمَالِ: after a noun opening the sentence in raf', a word that is either
    # أَفْعَلُ "I do" or the elative is that noun's khabar, and a verb khabar needs a pronoun back to
    # its مبتدأ (رابط جملة الخبر, Ibn Aqil on the Alfiyya); "I" with nothing on it has none
    if len(out) > 1 and out[0].get("pos", "").startswith("noun") and typed_case(tokens[0]) == "u" \
            and out[1].get("pos") == "verb" and out[1].get("per") == "1" and out[1].get("enc0") in ("0", "na", None) \
            and (elative := noun_reader.reading_of(steps[1][0])):
        out[1] = elative


def _joined_onto_an_elative(p: _Picked) -> None:
    steps, out = p.steps, p.out
    # وَالْآخِرَةُ خَيْرٌ وَأَبْقَى: a word joined by و onto an elative, which the typed vowels read as that
    # elative as well as a verb ("and I remain"), is the elative: a verb is joined onto a noun only when the
    # noun is like a verb, as the active participle is (Ibn Aqil on the Alfiyya V3 p244), and an elative is not
    for i in range(1, len(out)):
        if out[i].get("pos") == "verb" and out[i - 1].get("pos") in NOUNISH \
                and elative_shape(out[i - 1].get("pattern", ""), out[i - 1].get("lex", "")):
            word = steps[i][0]  # the only shape of sarf's nouns a verb spells too is أَفْعَل, the elative's
            if (noun := _joined_noun(word, "و", "CONJ", prc2="wa_conj")) and best_reading(word, [noun]):
                out[i] = noun


def _construct_needs_what_follows(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # مَنْ جَدَّ وَجَدَ: a مضاف needs its مضاف إليه straight after it, so a bare construct noun
    # before a و, a preposition or nothing is not the word typed (here the verb جَدَّ)
    # لَا رَيْبَ فِيهِ: after لا النافية للجنس the noun's missing tanween is لا's building on fatha
    # (closed_words la_jins, Tasheel 3.7.3 p69), not a مضاف waiting for its مضاف إليه
    for i, reading in enumerate(out):
        after_la = i > 0 and is_one(bare_letters(out[i - 1].get("diac", "")), "la_jins")
        if _bare_construct(reading) and not after_la and not _takes_mudaf_ilayh(*((out[i + 1], tokens[i + 1]) if i + 1 < len(out) else ({}, ""))):
            word, ranked = steps[i]
            pool = _widened(tokens[i], ranked)
            if reading.get("prc3") == "Aa_ques" and (split := _asked_split(word)):  # أَذَهَبَ زَيْدٌ: not "the gold of"
                pool += [_joined_onto(split[0], r, "INTERROG_PART", prc3="Aa_ques") for r in _rest_readings(split[1])]
            # the word's whole list too (أَكْبَرُ's own indefinite reading may be ranked out), never a guessed name
            out[i] = best_reading(word, [r for r in pool
                                         if not _bare_construct(r) and r.get("pos") != "noun_prop"]) or reading


def _elative_before_min(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # أَوْعَى لَهُ مِنْهُ، أَعْظَمَ فِي نَفْسِي مِنْ صِدْقِي: the elative is followed by, or by what it governs and then, the مِنْ-phrase (Tashil V1 p132), so a word with the
    # elative's shape, read as a verb, straight before a preposition and a مِنْ within the next three words with no verb
    # before it, is that elative; a doer (أَنْعَمَ اللَّهُ عَلَيَّ مِنْ نِعْمَةٍ) or an object straight after it keeps the verb, and so does
    # a verb after لم، لن، سوف (لَمْ أَفْهَمْ مِنْهُ شَيْئًا), where no noun stands (expects.json `only`), and a word typed with a fatha
    # first or after a ما, نافية، موصولة، كافة alike (أَصْبَحَ مِنْ عِبَادِي مُؤْمِنٌ، مَا أَصْبَحَ مِنْهُمْ أَحَدٌ): a noun there has no
    # عامل before it to set it in nasb, so the fatha is the past verb's. The dual pronoun هُمَا، كُمَا is no ما: a verb with it
    # takes the noun as its object (أَعْطَيْتُهُمَا أَكْثَرَ مِنْ حَقِّهِمَا)
    for i in range(len(out) - 1):
        if out[i].get("pos") == "verb" and out[i + 1].get("pos") == "prep" and _min_phrase_follows(out[i + 1:i + 4]) \
                and not (i and expects.only_verb(tokens, out, i)) \
                and not (typed_case(tokens[i]) == "a" and (not i or bare_letters(tokens[i - 1]).endswith("ما")
                                                       and not (out[i - 1].get("enc0") or "").startswith(("2d", "3d")))) \
                and (elative := _elative_reading(tokens[i], steps[i])):
            out[i] = elative


def _speaker_present(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # إِنِّي أَعْلَمُ مَا لَا تَعْلَمُونَ (2:30): the elative never takes an object (Ashmuni V2 p312: لا ينصب المفعول به), so a word of
    # its shape, said by the speaker (إِنِّي، أَنَا before it) with a relative or a word typed in nasb straight after it, is the
    # speaker's present verb "I know" and that word its object; with a preposition after it (أَعْلَمُ بِمَا) it stays the elative
    for i in range(1, len(out) - 1):
        if out[i].get("pos") in NOUNISH and elative_shape(out[i].get("pattern", ""), out[i].get("lex", "")) \
                and out[i].get("enc0") in ("0", "na", None) and _speaker(tokens[i - 1]) \
                and all(out[i + 1].get(prc, "0") in ("0", "na") for prc in ("prc1", "prc2", "prc3")) \
                and (out[i + 1].get("pos") == "pron_rel" or typed_case(tokens[i + 1]) == "a" and out[i + 1].get("pos", "").startswith("noun")) \
                and (verb := best_reading(tokens[i], [r for r in _widened(tokens[i], steps[i][1])
                                                      if r.get("pos") == "verb" and r.get("asp") == "i" and r.get("per") == "1"])):
            out[i] = verb


def _nasb_needs_its_verb(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
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
            verb = best_reading(tokens[i], [
                r for r in _widened(tokens[i], steps[i][1]) if r.get("pos") == "verb" and "ّ" not in r.get("diac", "")])
            if verb:
                out[i] = verb
                break


def _two_words_a_sentence(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # أكل الطعام: a sentence tells a full thought, built of two nouns or a verb and a noun (Ibn Aqil V1 p14:
    # الكلام ... اللفظ المفيد فائدة يحسن السكوت عليها ... ولا يتركب الكلام إلا من اسمين ... أو من فعل واسم).
    # A مضاف typed bare with nothing but its مضاف إليه after it tells none, so where it reads as a past verb
    # adding no letter, that verb with its hidden doer is the sentence. Typed vowels still choose (أَكْلُ الطَّعَامِ)
    if len(out) == 2 and _bare_construct(out[0]) and out[1].get("cas") == "g":
        verb = best_reading(tokens[0], [r for r in _widened(tokens[0], steps[0][1])
                                        if r.get("pos") == "verb" and r.get("asp") == "p" and "ّ" not in r.get("diac", "")])
        if verb:
            out[0] = verb


def _verb_shaped_name_alone(p: _Picked) -> None:
    tokens, steps, out = p.tokens, p.steps, p.out
    # قال إبراهيم لأبيه آزر: typed bare, a word the Qur'an says alone only as a name is that name where the
    # dictionary reads a verb and no noun comes next to be its doer or what it is done to (the sentence ends,
    # or a new one opens: آزر أنا ذاهب); a noun next keeps the verb (آزر الجيش الشعب). Only a verb's shape is
    # foreign to a name: a noun read so stays (في قلبي حنين: longing, not the battle)
    for i, reading in enumerate(out):
        if reading.get("pos") == "verb" and not any(r.get("pos") in NOUNISH for r in out[i + 1:i + 2]) \
                and (name := _quran_name(tokens[i], _widened(tokens[i], steps[i][1]), bare=True)):
            out[i] = name


def _present_after_its_particle(p: _Picked) -> None:
    """A past verb after a particle that wants a present (أَنْ، لَنْ، لَمْ) is that present; so is one of
    تَفَاعَلَ or تَفَعَّلَ written with one of its two تاءات."""
    tokens, steps, out, disambiguator = p.tokens, p.steps, p.out, p.disambiguator
    for i in range(len(out)):
        before = out[i - 1] if i else {}
        if i and (wants := _wants_present(before, out[i])) and (present := _present_reading(tokens[i], steps[i][1])) \
                and (wants == "nasb" or reading_root(present) == reading_root(out[i])):
            out[i] = present
        elif _one_taa_written(before, out[i], tokens[i], i > 0 and (expects.verb_after(tokens, out, i) == "nasb" or _merged_nasb(tokens[i - 1]))) \
                and not _la_before_a_past(out, i) and (present := _both_taas(out[i], tokens[i], disambiguator)):
            out[i] = present


def _said_joined(p: _Picked) -> None:
    """A word with هاء السكت carries the word as said joined (مَالِيَهْ → مَالِيَ)."""
    out, paused = p.out, p.paused
    for i, said in paused.items():
        out[i] = {**out[i], "said": said}


def _rivals(p: _Picked) -> None:
    """A word the typed letters leave open carries its rival reading (iraab._rivalled reads it)."""
    steps, out = p.steps, p.out
    for i, (evidence, ranked) in enumerate(steps):
        if rival := _rival(evidence, out[i], ranked):
            out[i] = {**out[i], "rival": rival}


SENTENCE_PASSES = (_wider_list, _past_verb_doer, _my_before_a_genitive, _verb_after_its_governor, _first_word_past,
                   _elative_khabar, _joined_onto_an_elative, _construct_needs_what_follows, _elative_before_min,
                   _speaker_present, _nasb_needs_its_verb, _two_words_a_sentence, _verb_shaped_name_alone,
                   _present_after_its_particle, _said_joined, _rivals)


def _wants_present(before: dict, reading: dict) -> str | None:
    """The mood a particle straight before a past verb reading wants a present in: "nasb" after أَنْ، لَنْ، كَيْ ...;
    "jazm" after لَمْ, which never comes before a past (لَمْ أُكْرِمْ زَيْدًا: أُكْرِمْ is أُفْعِلُ's jazm, not the passive past),
    so pick takes the present only of the same verb, its root the past's: letters no present of that verb spells are
    the past after لِمَ ("why", لِ + مَا), spelled as لَمْ is (لِمَ تَرَكَ الصَّلَاةَ, typed bare too). لَمَّا comes before a past
    too, as "when" (لَمَّا جَاءَ), so a past after it stays; the particle is told by its lemma."""
    if reading.get("pos") != "verb" or reading.get("asp") != "p":
        return None
    if is_one(strip_diacritics(before.get("diac", "")), "nasb_mudari", "before_a_present_verb"):
        return "nasb"
    jazm = strip_diacritics(before.get("lex", ""))
    return "jazm" if is_one(jazm, "jazm", "before_a_present_verb") \
        and jazm not in book_words("ghair_amila_other", "conditional_particles") else None


def _present_reading(token: str, ranked: list[dict]) -> dict | None:
    """أَنْ أَقْرَأَ: the final fatha is the present verb's nasb as well as the past verb أَقْرَأَ's (form IV,
    "he made read"), and a past verb is never what a nasb particle works on. The present reading the typed
    vowels do not contradict is the word; None where no such reading exists (أَنْ جَاءَ)."""
    return best_reading(token, [r for r in _widened(token, ranked) if r.get("pos") == "verb" and r.get("asp") == "i"])


def _one_taa_written(before: dict, reading: dict, token: str, nasbed: bool = False) -> bool:
    """لَا تَحَاسَدُوا، وَلَا تَوَلَّوْا (8:20): a present verb of تَفَاعَلَ or تَفَعَّلَ opens with two تاءات, and
    one may go (Alfiyya, باب الإدغام: وَمَا بِتَاءَيْنِ ابْتُدِي قَدْ يُقْتَصَرْ فِيهِ عَلَى تَا; page unchecked), so
    تَتَحَاسَدُوا is written as the past تَحَاسَدُوا. After a particle that puts one present verb in jazm (لَا، لَمْ),
    a past of those forms whose ending is a dropped نون's (وا، ا) or the women's نون, stilled before it (تَحَاسَدْنَ),
    is that present (the Quranic Treebank: حَرْفُ نَهْيٍ before تَوَلَّوْا 8:20 and تَجَسَّسُوا 49:12). A particle that
    opens a condition, which a past follows too (مَا تَحَاسَدُوا، لَمَّا تَزَوَّجَا), and أَنْ leave it, as does a past
    whose ending no present shares (فَلَا صَدَّقَ 75:31، تَبَيَّنَ). So after لَنْ، كَيْ and the others no word but a
    present follows (`nasbed`: expects.json nasb; لَنْ تَحَاسَدُوا), and under a kasra لام on the word itself, which
    only a present stands after (لِتَعَارَفُوا 49:13, Quranic Treebank: لام التعليل), where the dictionary reads the
    لَ of a past verb against the typed kasra."""
    lemma = strip_diacritics(before.get("lex") or "")
    lam = token.startswith("لِ") and reading.get("prc1", "0") != "0"
    takes_a_past = book_words("jazm", "conditional_particles") | book_words("jazm", "conditional_nouns") \
        | book_words("ghair_amila_other", "conditional_particles")
    marked = letters(token)
    ending = bare_letters(token).endswith(("وا", "ا")) or (
        bare_letters(token).endswith("ن") and len(marked) > 1 and SUKUN in marked[-2][1])
    # تَنَزَّلُ الْمَلَائِكَةُ (97:4): a damma typed on the last letter is a present's raf'; no past ends on one
    # (its ت keeps the fatha: تُحَدِّثُ is فَعَّلَ's own present); only the bare past of one man, which ends on a fatha,
    # not one carrying a pronoun or تُ whose damma is theirs (تَنَزَّلَهُ، تَعَلَّمْتُ)
    bare_past = (reading.get("per"), reading.get("num"), reading.get("gen")) == ("3", "s", "m") \
        and reading.get("enc0", "0") in ("0", "", None)
    raised = bare_past and len(marked) > 1 and "\u064e" in marked[0][1] and "\u064f" in marked[-1][1] and not has_tanween(token)
    return reading.get("pos") == "verb" and reading.get("asp") == "p" \
        and (raised or (lam or nasbed or lemma in book_words("jazm") - takes_a_past) and ending) \
        and str(reading.get("pattern") or "")[len("لَ") if lam else 0:].startswith("تَ")


def _merged_nasb(token: str) -> bool:
    """أَلَّا تَنَازَعُوا: أنْ with its nun merged into لا (data: nasb_mudari `merges`), the shadda on its lam telling it
    from أَلَا that opens speech, puts the present after it in nasb as لَنْ does."""
    return SHADDA in token and strip_diacritics(token) in book_map("nasb_mudari", "merges")


def _la_before_a_past(out: list[dict], i: int) -> bool:
    """فَلَا صَدَّقَ وَلَا صَلَّى (75:31): a لا said again over past verbs denies each, so the one after it is a
    past too (فَلَا تَابُوا وَلَا تَذَكَّرُوا), not a present that lost a ت (_one_taa_written)."""
    return any(out[j].get("pos") == "verb" and out[j].get("asp") == "p" and strip_diacritics(out[j - 1].get("lex") or "") == "لا"
               for j in range(1, i - 1))


def _both_taas(past: dict, token: str, disambiguator=None) -> dict | None:
    """The present verb of a past written with one of its two تاءات (_one_taa_written). Both forms have the
    past's own letters and vowels (تَحَاسَدُوا), so the reading keeps them and takes the present's grammar: the
    present's spelling with the ت it lost taken out again. A kasra لام on the word stays before the ت (لِتَعَارَفُوا)."""
    at = len("لِ") if token.startswith("لِ") else 0
    ranked = (_ranked([token[:at] + "ت" + token[at:]], disambiguator) or [[]])[0]
    found = next((r for r in ranked if r.get("pos") == "verb" and r.get("asp") == "i" and r.get("lex") == past.get("lex")), None)
    return found and {**found, **{key: found[key].replace("تَتَ", "تَ", 1) for key in ("diac", "atbtok", "pattern") if key in found}}


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
    one with another vowel on that alif or before it is no nasb (مُحَمَّدُا). The reading is the one the
    typed vowels fit (وَعَمْرًا is no عُمَر); a name whose letter is written only out of nasb (farqa_waw:
    عَمْرو) is read with it back."""
    marked = letters(typed)
    if len(marked) < 3 or marked[-1][0] != "ا" or (marked[-1][1] | marked[-2][1]) - {"ً"}:
        return None
    stem = "".join(letter + "".join(marks - {"ً"}) for letter, marks in marked[:-1])
    def read(spelled: str) -> list[dict]:
        return [r for r in (_ranked([spelled], disambiguator) or [[]])[0] if NO_ANALYSIS not in r.get("atbtok", "")]
    farqa = book_map("farqa_waw", "letter")
    readings = read(stem) + [{**r, "diac": r["diac"].removesuffix(farqa), "atbtok": r["atbtok"].removesuffix(farqa)}
                             for name in book_words("farqa_waw") if bare_letters(stem).endswith(name.removesuffix(farqa))
                             for r in read(stem + farqa)]
    known = best_reading(stem, readings) or (readings[0] if readings else None)
    # the alif goes on the word's own split, so a وَ before the name stays its own piece (جِئْتُ وَزَيْدًا)
    return known and {**known, "cas": "a", "diac": known["diac"] + "ًا", "atbtok": known["atbtok"] + "ًا"}


def _quran_name(typed: str, readings: list[dict], bare: bool = False) -> dict | None:
    """كَانَ اسْمُ أَبِيهِ آزَرَ: a foreign name may wear a verb's shape (Sharh al-Tasrih V2 p708: أعجمي على
    وزن فاعل كآزر), and the dictionary, lacking the name, reads the verb. Where the Qur'an's hand-tagged
    corpus says these letters alone only as a proper noun (quran.corpus.name_of) and the dictionary has
    no name spelled so, the word is that name, by the vowels the reader typed: one typed bare says
    nothing either way, and stays the dictionary's unless `bare` (pick's reading by what comes after)."""
    spelled = bare_letters(typed)
    if not quran_corpus.is_loaded() or any(r.get("pos") == "noun_prop" and bare_letters(r.get("diac", "")) == spelled for r in readings):
        return None
    if not ((lemma := quran_corpus.name_of(typed)) and (found := vowel_agreement(typed, lemma)) and (found[0] or bare)):
        return None
    case = {vowel: camel for camel, vowel in CAMEL_CASE.items()}.get(typed_case(typed) or "", "na")
    return {"pos": "noun_prop", "diac": typed, "lex": lemma, "atbtok": typed, "catib6": "PROP", "ud": "PROPN",
            "bw": f"{typed}/NOUN_PROP", "pattern": "", "enc0": "0", "stt": "i", "cas": case, "num": "s", "gen": "m",
            "asp": "na", "vox": "na", "per": "na", "mod": "na", "prc0": "0", "prc1": "0", "prc2": "0", "prc3": "0", "source": "quran"}


def _saying(reading: dict) -> bool:
    """A verb of saying (closed_words saying_verbs): قَالَ، فَقَالُوا. What is said after it is a sentence of its own
    (Tasheel 1.2), so a question hamza may open it (قَالَ أَتَقُولُونَ)."""
    return reading.get("pos") == "verb" and is_one(strip_diacritics(reading.get("lex", "")), "saying_verbs")


def _asked_split(typed: str) -> tuple[str, str] | None:
    """The question hamza written onto the front of a word (its fatha with it, or with no vowel typed on the word at
    all), and the rest of the word."""
    marked = letters(typed)
    hamza = next((w for w in book_words("istifham") if len(w) == 1), None)
    if not (hamza and len(marked) > 2 and marked[0][0] == hamza and ("َ" in marked[0][1] or no_vowels_typed([typed]))):
        return None
    asked = typed[:len(marked[0][0]) + len("".join(marked[0][1]))]
    return asked, typed[len(asked):]


def _table_verb(typed: str, evidence: str, ranked: list[dict], bare: bool = False) -> dict | None:
    """يَسْتَعْتِبُوا، تَسْتَحِ: no reading the dictionary has is the word typed, so the table's is. One of
    the table's own tense is only spelled otherwise: the dictionary's stays. A command alone is left to
    repair.typed (verb_reader.command), which cuts nothing off; one with a letter joined on (فَاعْزِمُوا) or its
    object pronoun written on (اِهْدِنَا) is split here. A word typed with no vowel (`bare`), which the dictionary has
    no reading of, is read off the table too, where its root is one the books file (dictionary.roots.spelling)."""
    from backend.services.dictionary import roots  # it reads with this module
    # الْفُلْكَ: a word the dictionary reads only as a noun with the article (فَلَك) is that noun with its vowels unknown;
    # ال is a sign of the noun (Ibn Aqil, علامات الاسم: أل; page unchecked), not the front of a command it has no record of
    if (had := [r for r in ranked if NO_ANALYSIS not in r.get("atbtok", "")]) and all(r.get("bw", "").startswith("ال/DET+") for r in had):
        return None
    if (sarf := verb_reader.reading_of(typed, _seen_verb, roots.spelling if bare else None, has_verb)) and (sarf.get("asp") != "c" or "+" in sarf.get("atbtok", "")) \
            and all(r.get("asp") != sarf.get("asp") or _other_bab(sarf, r, evidence) or _voice_against(sarf, r, evidence)
                    for r in ranked if NO_ANALYSIS not in r.get("atbtok", "")):
        return {"lex": base_of(evidence, sarf.get("atbtok")), **sarf, "diac": evidence}  # its past, else the verb's own letters


def _answer_command(before: list[str], typed: str, evidence: str, ranked: list[dict]) -> dict | None:
    """فَاعْزِمُوا typed bare (فاعزموا): the answer to a condition that is a command takes the ف (Ibn Aqil V4 p37: إن جاء
    زيد فاضربه), so a word with a ف on its front that the dictionary has no reading of, after a word that opens a
    condition, is that ف and a command of a root the books file, read off sarf's table."""
    def opens(word: str) -> bool:
        spelled = strip_diacritics(word)
        return bool(condition_of(spelled) or spelled[:1] in "وف" and condition_of(spelled[1:]))

    if (typed[:1] == "ف" and unread(ranked) and no_vowels_typed([typed]) and any(opens(word) for word in before)
            and (table := _table_verb(typed, evidence, ranked, bare=True)) and table.get("asp") == "c"):
        return table


def _asked_reading(typed: str, ranked: list[dict], after: str, disambiguator=None) -> dict | None:
    """أَذَاهِبٌ زَيْدٌ: the question hamza (closed_words istifham, a one-letter word) opens the
    sentence before a full clause, written onto its first word; the dictionary lacks it on a
    noun, so the rest of the word is read and the hamza put back as its proclitic, as CAMeL
    writes a وَ (وَ+_ذاهِب). Read so where no reading of the whole word fits its vowels, or where
    the rest is a حرف جر and the next word is typed in jarr (أَفِي اللَّهِ شَكٌّ: no verb or name puts
    the noun after it in jarr, so أَفِي is not "I fulfil"), or where the rest is a jazm particle typed
    with its sukun (أَلَمْ نَشْرَحْ: not the verb أَلَمَّ). A rest the dictionary has no reading of that holds
    its vowels is read off sarf's table (أَيَعْجِزُ: the dictionary has يَعْجَزُ, not يَعْجِزُ)."""
    if not (split := _asked_split(typed)):
        return None
    asked, rest = split
    bare_rest = strip_diacritics(rest)
    asks_onto = (bare_rest in book_words("jarr") and typed_case(after) == "i") \
        or (bare_rest in book_words("jazm") and rest.endswith("ْ")) \
        or (bare_rest[:1] in "فو" and bare_rest[1:] in ("لا", "لم")  # أَفَلَا تَعْقِلُونَ، أَوَلَمْ يَرَوْا: not the verb أَفَلَا;
            and "ْ" not in letters(rest)[0][1])  # a joining و/ف is never silent: أَوْلَمَ (he gave a feast) is one verb
    bare = no_vowels_typed([typed])
    if _agreeing(typed, ranked) and not asks_onto and not (bare and unread(ranked)):
        return None
    ranked = _rest_readings(rest, disambiguator)
    if not _agreeing(rest, ranked) or bare and unread(ranked):
        table = _table_verb(rest, rest, [], bare)  # none of its readings holds the vowels typed, so none competes
        return _joined_onto(asked, {**verb_reader.pieces([], letters(rest)), **table}, "INTERROG_PART", prc3="Aa_ques") if table else None
    return _joined_onto(asked, _reading(rest, ranked), "INTERROG_PART", prc3="Aa_ques")


def _after_fronted_khabar(before: list[str]) -> bool:
    """إِنَّ فِي ذَلِكَ لَعِبْرَةً: the words before are إنّ (or a sister), a جار, and its majrur (up to three words), so the
    word now is the ism that waits behind its khabar."""
    spelled = [strip_diacritics(w) for w in before]
    inna = next((j for j in range(len(spelled) - 2, -1, -1) if is_one(spelled[j], "inna")), None)
    return inna is not None and spelled[inna + 1] in book_words("jarr") and 2 <= len(spelled) - inna <= 5


def _emphasis_lam(typed: str, disambiguator=None, fronted_khabar: bool = False) -> dict | None:
    """وَإِنَّكَ لَعَلَى خُلُقٍ عَظِيمٍ: after إنّ the لام of emphasis comes onto its khabar, a jar-majroor
    or ظرف too (closed_words `khabar_lam`). The dictionary never writes a لام onto a حرف جر or ظرف, so
    it reads لِ+عَلِيّ or a verb; but a جار takes no جار after it, so the word is that لام on the
    particle, after إنّ or not (وَاللَّهِ لَعَلَى الْحَقِّ أَنْتَ: the لام of the oath's answer). Not with a
    typed kasra (لِمَنْ: the جار on مَن who), nor where a verb reads the letters too (إِنَّ اللَّهَ لَعَنَ
    الْكَافِرِينَ، لمن bare as لُمْنَ). A لام typed with a fatha onto any other word that no reading of the
    whole word fits (لَأَنْتُمْ أَشَدُّ رَهْبَةً: the dictionary has only لِ+ a verb) is that لام too: the
    jarr لام takes a fatha only before a pronoun joined on (لَكَ), which the dictionary reads whole
    (closed_words ghair_amila_other `_fatha_lam`). Typed bare, the لام of ابتداء comes onto the ism of إنّ that waits
    behind a fronted khabar (إِنَّ مِنَ الْبَيَانِ لَسِحْرًا; Alfiyya: وتصحب الواسط معمول الخبر والفصل واسما حل قبله الخبر,
    page unchecked), unless the whole word is a noun the dictionary has (لسحرا is no verb: no ism is one)."""
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
    elif [r for r in whole if r.get("pos") != "verb" and not unread([r])] if fronted_khabar and no_vowels_typed([typed]) else whole:
        return None
    ranked = _rest_readings(rest, disambiguator)
    # لَصَادِقُونَ: a noun the dictionary lacks is read by sarf's shapes, as pick reads it standing alone
    found = _reading(rest, ranked) if _agreeing(rest, ranked) else noun_reader.reading_of(rest)
    return _joined_onto(said, found, "EMPHATIC_PART", prc1="la_emph") if found else None


def _fa_before_oath(typed: str, ranked: list[dict], disambiguator=None) -> dict | None:
    """فَوَاللَّهِ إِنِّي لَأُعْطِي، فَوَالَّذِي نَفْسِي بِيَدِهِ: a فاء written before the oath's واو (closed_words jarr
    `oath_only`; Ibn Aqil vol 4 p42, bab al-qasam: the oath's answer follows it, the فاء only ties it to what came
    before). The dictionary reads the two letters and the sworn-by as one guessed name ("والله") under the فاء; the
    word is the فاء put back on what the rest reads as when it stands alone (وَاللَّهِ: وَ + الله)."""
    marked = letters(typed)
    if not (len(marked) > 1 and marked[0][0] == "ف" and not marked[0][1] - {"َ"} and is_one(marked[1][0], "jarr", "oath_only")
            and _reading(typed, ranked).get("pos") == "noun_prop"):
        return None
    said = typed[:len(marked[0][0]) + len("".join(marked[0][1]))]
    rest = _rest_readings(typed[len(said):], disambiguator)
    return _joined_onto(said, _reading(typed[len(said):], rest), "CONJ", prc2="fa_conj")         if rest and str(rest[0].get("prc2", "")).startswith("wa_") else None


def _emphasis_nun(typed: str, ranked: list[dict]) -> dict | None:
    """لَأَكِيدَنَّ، لَنُخْرِجَنَّكَ، لَيَقُولُنَّ: the doubled nun of emphasis, with a fatha, comes only onto a verb (Ibn Aqil
    V1 p23: ومما يميز الفعل نون أقبلن ... لنخرجنك يا شعيب). The dictionary has no verb with it, so it reads the word as one
    guessed name, ل and pronoun and all. The word is the present those letters spell with the nun gone and its raf' back
    (_RAF_UNDER_NUN), written as typed; a لام typed with a fatha before it is the لام of emphasis (that answers an oath:
    closed_words ghair_amila_other `_fatha_lam`), and a و or ف before that joins."""
    if _agreeing(typed, ranked):
        return None
    joined = next(((split, name) for letter, name in _JOINING if (split := _one_letter_off(typed, letter))), None)
    said, rest = joined[0] if joined else ("", typed)
    lam, verb = _one_letter_off(rest, "ل") or ("", rest)
    marked = letters(verb)
    if not marked or marked[0][0] not in "أنيت":  # a present opens on one of أنيت: لِيَكْتُبَنَّ is the لام of command's
        return None
    for after in range(4):  # the letters of a pronoun after the nun
        # before ني the nun of emphasis and the pronoun's nun are one doubled letter (harakat.build_nun): the pronoun is نِي
        merged = build_nun(verb, after) == "emphasis" and after == 2 and SHADDA in marked[-2][1]
        at = len(marked) - after - (0 if merged else 1)
        # اقْصِدَنْ، لَأَفْعَلَنْ: the light nun, its sukun its own, ends the word (Ibn Aqil V3 p306: للفعل توكيد بنونين
        # هما كنوني اذهبنّ واقصدنهما; page unchecked)
        light = marked[at][0] == "ن" and marked[at][1] == {SUKUN}
        if not light and (at < 2 or marked[at][0] != "ن" or SHADDA not in marked[at][1] or not (merged or "َ" in marked[at][1])):
            continue
        last, marks = marked[at - 1]
        if not (vowel := next((v for v in _RAF_UNDER_NUN if v in marks), None)):
            continue
        pronoun = "نِي" if merged else own_letters(verb, at + 1, 0)
        spelt = own_letters(verb, 0, len(marked) - at + 1) + last
        # تَرَوُنَّ، اخْشَيِنَّ: after a fatha the five verbs' و or ي stays, with its own vowel (تَرَوْنَ، تَخْشَيْنَ)
        kept = (spelt + SUKUN + "نَ" + pronoun,) if (last, vowel) in (("و", "ُ"), ("ي", "ِ")) and "َ" in marked[at - 2][1] else ()
        # the dictionary lacks most passives (يُسْجَنُ): its verb adding no shadda is kept, and the vowels read the voice
        ending, number = _RAF_UNDER_NUN[vowel]
        found = next((best for plain in (*kept, spelt + ending + pronoun, spelt + pronoun)
                      if (verbs := [r for r in _analyses(plain) if r.get("pos") == "verb" and r.get("asp") == "i"
                                    and number in (None, r.get("num"))
                                    and ("_+" in r.get("atbtok", "")) == bool(after)])
                      and (best := best_reading(plain, verbs) or nearest_reading(plain, verbs)
                           or min(verbs, key=lambda r: _added(r, plain)))), None)
        if not found:
            continue
        tail = found["atbtok"][found["atbtok"].index("_+"):] if after else ""
        # the merged ن is written once and opens the pronoun's نِي, so the verb's own letters stop before it
        reading = {**found, "diac": verb, "atbtok": own_letters(verb, 0, len(marked) - at - (0 if merged else 1)) + tail}
        reading = _joined_onto(lam, reading, "EMPHATIC_PART", prc1="la_emph") if lam else reading
        return _joined_onto(said, reading, "CONJ", prc2=f"{joined[1]}_conj") if joined else reading
    return None


# The raf' a present loses to the nun of emphasis, by the vowel left on the letter before it, and whose verb that is:
# one verb's damma (يَقُولَنَّ is يَقُولُ, built on the fatha), or the five verbs' و or ي with their nun, gone so that two sukuns
# and three nuns do not meet: the men's (يَقُولُنَّ is يَقُولُونَ) or the one woman's (تَقُولِنَّ is تَقُولِينَ: the women's keep
# their nun and take انِّ after it; Alfiyya, نونا التوكيد: واشكله قبل مضمر لين بما جانس,
# page unchecked), unless a fatha before keeps them (تَرَوُنَّ). A weak last letter shows no damma (أَقْضِيَنَّ is أَقْضِي),
# so the letters alone are read too.
_RAF_UNDER_NUN = {"َ": ("ُ", None), "ُ": ("ُونَ", "p"), "ِ": ("ِينَ", "s")}


def _one_letter_off(typed: str, letter: str) -> tuple[str, str] | None:
    """The word's first letter with its marks, and the rest, where that letter is `letter` with a fatha or none."""
    marked = letters(typed)
    if not (len(marked) > 1 and marked[0][0] == letter and not marked[0][1] - {"َ"}):
        return None
    said = typed[:len(marked[0][0]) + len("".join(marked[0][1]))]
    return said, typed[len(said):]


def _oath_ta(typed: str, ranked: list[dict], disambiguator=None) -> dict | None:
    """تَاللَّهِ لَأَكِيدَنَّ أَصْنَامَكُمْ: the ت of an oath (closed_words jarr `oath_only`) swears by الله alone and is written
    onto it (`ta_swears_by`). The dictionary has no reading of the two but a guessed name; the word is the ت put back on
    what the name reads as alone, as CAMeL writes the و of وَاللَّهِ."""
    if not (split := _one_letter_off(typed, "ت")) or bare_letters(split[1]) not in book_words("jarr", "ta_swears_by") \
            or _agreeing(typed, ranked):
        return None
    said, rest = split
    found = _rest_readings(rest, disambiguator)
    return _joined_onto(said, _reading(rest, found), "PREP", prc1="ta_prep") if _agreeing(rest, found) else None


def _oath_lam(typed: str) -> dict | None:
    """لَئِنْ شَكَرْتُمْ، وَلَئِنْ سَأَلْتَهُمْ: the لام that announces an oath onto إنْ of a condition (closed_words
    ghair_amila_other `oath_lam`), a و or ف joining it on. A hamza opening a word is written in its middle once a
    letter is joined on, on the seat its kasra asks (ئ). The dictionary reads لَ+إِنَّ, which the لام never comes onto,
    so the word is the لام on the dictionary's إِنْ, spelled on the typed seat."""
    joined = next(((split, name) for letter, name in _JOINING if (split := _one_letter_off(typed, letter))), None)
    said, rest = joined[0] if joined else ("", typed)
    lam = book_map("ghair_amila_other", "oath_lam")
    if not ((split := _one_letter_off(rest, lam["lam"])) and split[1].startswith("ئ")
            and (particle := strip_diacritics("إ" + split[1][1:])) in lam["onto"]):
        return None
    particle = next((r for r in _analyses(particle) if r.get("pos") == "conj_sub" and SHADDA not in r.get("atbtok", "")
                     and strip_diacritics(r.get("atbtok", "")) == particle), None)
    if not particle:
        return None
    seated = {**particle, "diac": _reseated(particle["diac"], 0, "ئ"), "atbtok": _reseated(particle["atbtok"], 0, "ئ")}
    found = _joined_onto(split[0], seated, "EMPHATIC_PART", prc1="la_emph")
    return _joined_onto(said, found, "CONJ", prc2=f"{joined[1]}_conj") if joined else found


def _jarred_ma(typed: str) -> dict | None:
    """فِيمَ، عَمَّ، إِلَامَ، لِمَاذَا: the ما that asks, jarred, is written with its حرف جر as one word (closed_words
    istifham `jarred_ma`). CAMeL splits some (فِيمَ) and files the rest as another word (عَمَّ a verb, إِلَامَ "pains",
    لِمَ unsplit), so the two are read here, as CAMeL writes بِمَ (a one-letter حرف جر before) and فِيمَ (a word, ما after)."""
    bare = strip_diacritics(typed)
    if not (pair := book_map("istifham", "jarred_ma").get(bare)) or (mark := book_map("istifham", "jarred_ma_marked").get(bare)) and mark not in typed:
        return None
    jar, ma, *proclitic = pair
    shared = {"diac": typed, "prc2": "0", "prc3": "0", "per": "na", "asp": "na", "vox": "na", "mod": "na", "num": "na", "gen": "na",
              "catib6": "PRT+NOM", "ud": "ADP+PRON", "root": "م.#", "bw": f"{jar}/PREP+{ma}/INTERROG_PART",
              "gloss": book_map("istifham", "jarred_ma_gloss").get(bare, "")}
    if proclitic:
        return {**shared, "lex": strip_diacritics(ma), "pos": "pron_interrog", "atbtok": f"{jar}+_{ma}", "prc0": "0", "prc1": proclitic[0],
                "enc0": "0", "stt": "i", "cas": "u"}
    return {**shared, "lex": jar, "pos": "prep", "atbtok": f"{jar}_+{ma}", "prc0": "na", "prc1": "0", "enc0": "ma_interrog", "stt": "na", "cas": "na"}


def _kaffa_ma(typed: str, ranked: list[dict]) -> dict | None:
    """إِنَّمَا، أَنَّمَا، كَأَنَّمَا، لَكِنَّمَا، لَيْتَمَا، لَعَلَّمَا: an إنّ sister with ما الكافة written onto it (closed_words
    inna `kaffa`), a و or ف joining it on. The dictionary splits only إِنَّمَا (إِنَّ_+ما); it reads أَنَّمَا as إِنَّمَا, keeps
    كَأَنَّمَا whole, reads لَعَلَّمَا and لَيْتَمَا as لَ or لِ on a verb, and has no لَكِنَّمَا. So the sister's own reading
    gets the ما put after it, as the dictionary writes إِنَّمَا; typed vowels must fit the sister (لِيَتِمَّا stays a verb)."""
    if any("_+ما" in r.get("atbtok", "") and best_reading(typed, [r]) for r in ranked[:1]):
        return None  # the dictionary's own إِنَّ_+ما, read as typed
    joined = next(((split, name) for letter, name in _JOINING if (split := _one_letter_off(typed, letter))
                   and kaffa_sister(split[1])), None)
    said, rest = joined[0] if joined else ("", typed)
    if not (sister := kaffa_sister(rest)):
        return None
    cut = rest.rindex("م")  # the ما's own letters, its fatha with them
    # the heavy sister only (لَيْتَ is written without a shadda): never the light أَنْ، إِنْ، لٰكِنْ
    own = [r for r in _analyses(sister) if r.get("catib6") == "PRT" and strip_diacritics(r.get("diac", "")) == sister
           and (r.get("pos") == "verb_pseudo" or SHADDA in r.get("diac", ""))]
    found = next((r for r in own if vowel_agreement(rest[:cut], r["diac"]) is not None), None)
    if not found:
        return None
    reading = {**found, "diac": found["diac"] + "ما", "lex": found["diac"] + "ما", "pos": "verb_pseudo", "atbtok": f"{found['diac']}_+ما",
               "bw": f"{found['diac']}/PSEUDO_VERB+ما/REL_PRON", "catib6": "PRT+NOM", "ud": "CCONJ+PRON", "enc0": "mA_rel",
               "prc0": "na", "prc1": "0", "prc2": "0"}
    return _joined_onto(said, reading, "CONJ", prc2=f"{joined[1]}_conj") if joined else reading


def _declined_ma(typed: str) -> dict | None:
    """أَيَّمَا: أيّ, the condition word that is declined (closed_words `conditional_inflected`), with ما الزائدة written
    onto it. The dictionary keeps أَيُّمَا whole as an adverb, so أيّ's own reading as a relative-and-condition noun gets
    the ما put after it, split off as إِنَّمَا's is; typed vowels must fit أيّ."""
    joined = next(((split, name) for letter, name in _JOINING if (split := _one_letter_off(typed, letter))
                   and declined_with_ma(strip_diacritics(split[1]))), None)
    said, rest = joined[0] if joined else ("", typed)
    if not (stem := declined_with_ma(strip_diacritics(rest))):
        return None
    cut = rest.rindex("م")  # the ما's own letters, its fatha with them
    found = next((r for r in _analyses(stem) if r.get("pos") == "pron_rel" and vowel_agreement(rest[:cut], r["diac"]) is not None), None)
    if not found:
        return None
    reading = {**found, "diac": found["diac"] + "ما", "atbtok": f"{found['diac']}_+ما", "bw": f"{found['diac']}/REL_PRON+ما/PART",
               "catib6": "NOM+PRT", "ud": "PRON+PART", "enc0": "mA_rel"}
    return _joined_onto(said, reading, "CONJ", prc2=f"{joined[1]}_conj") if joined else reading


def _rest_readings(rest: str, disambiguator=None) -> list[dict]:
    """The readings of what is left once a one-letter particle is off: the word itself, not an
    abbreviation spelled like it (فِي)."""
    return [r for r in (_ranked([rest], disambiguator) or [[]])[0] if r.get("pos") != "abbrev"]


def _construct_plural(typed: str, ranked: list[dict], kept: dict) -> dict | None:
    """مَرَرْتُ بِرَافِعِي رَايَاتِهِمْ: before its مضاف إليه the word is no "my" but a sound plural or a dual, its ن
    dropped for the إضافة: the dictionary's own such reading where the typed vowels allow one (مُعَلِّمِي الْمَدْرَسَةِ),
    else sarf's (noun_reader.construct_of), a one-letter preposition or joining letter the kept reading has put back."""
    own = best_reading(typed, [r for r in ranked if r.get("enc0") in (None, "", "0") and r.get("stt") == "c"
                               and r.get("num") in ("p", "d") and r.get("pos", "").startswith(("noun", "adj"))])
    if own:
        return own
    front = next((key for key in ("prc1", "prc2") if str(kept.get(key, "0")) not in ("0", "na")), None)
    if not front:
        return noun_reader.construct_of(typed)
    marked = letters(typed)
    said = typed[:len(marked[0][0]) + len("".join(marked[0][1]))]
    found = noun_reader.construct_of(typed[len(said):])
    return _joined_onto(said, found, "PREP" if kept[front].endswith("_prep") else "CONJ", **{front: kept[front]}) if found else None


def _sound_fem_plural(typed: str, disambiguator) -> dict | None:
    """الْجَارَاتُ، مُسْرِعَاتٍ: a sound feminine plural the dictionary lacks is its singular with the ة made ات
    (Alfiyya, باب المعرب والمبني: وما بتا وألف قد جمعا), so it is read as that singular is, by the dictionary
    or else sarf's shapes, in the plural's number with its own typed ending: a damma its raf', a kasra its
    jarr or nasb (يكسر في الجر وفي النصب معا)."""
    marked = letters(typed)
    if len(marked) < 5 or [letter for letter, _ in marked[-2:]] != ["ا", "ت"]:
        return None
    ending = "".join(sorted(marked[-1][1]))
    singular = "".join(letter + "".join(sorted(marks)) for letter, marks in marked[:-2]) + "ة" + ending
    ranked = (_ranked([singular], disambiguator) or [[]])[0]
    found = best_reading(singular, [r for r in ranked if NO_ANALYSIS not in r.get("atbtok", "") and r.get("pos") in ("noun", "adj")
                                    and r.get("gen") == "f" and r.get("num") == "s"]) or noun_reader.reading_of(singular)
    if not found:
        return None
    case = "n" if marked[-1][1] & {"ُ", "ٌ"} else "g" if marked[-1][1] & {"ِ", "ٍ"} else "u"
    return {**found, "diac": typed, "atbtok": typed, "num": "p", "gen": "f", "cas": case,
            "pattern": (found.get("pattern") or "").replace("ة", "ات"), "gloss": (found.get("gloss") or "").replace("sg.", "pl.")}


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


def _inna_short_me(typed: str) -> dict | None:
    """لَعَلِّي، لَيْتِي: a sister of إنّ takes "me" as ـنِي or a bare ـي (Alfiyya, نون الوقاية: وليتني فشا وليتي ندرا ومع لعل اعكس),
    and the dictionary may hold only the ـنِي one; the bare ـي is that sister and its ism, never a name or verb."""
    bare = bare_letters(typed)
    # a written ي: لَعَلَى is لَ + عَلَى, its ى no pronoun
    if not (strip_diacritics(typed).endswith("ي") and is_one(bare[:-1], "inna")) or any(
            r.get("pos") == "verb_pseudo" for r in _analyses(bare)):
        return None
    full = next((r for r in _analyses(bare[:-1] + "ني") if r.get("pos") == "verb_pseudo"), None)
    if not full:
        return None
    stem = re.sub("[ً-ِْ]$", "", full["stem"])  # its last vowel gives way to the ي's kasra
    reading = {**full, "diac": stem + "ِي", "atbtok": full["stem"] + "_+ي", "bw": re.sub(r"\+نِي/", "+ي/", full["bw"]),
               "pattern": full["pattern"].removesuffix("نِي") + "ي"}
    return reading if best_reading(typed, [reading]) else None


def _particle_reading(particle: str) -> dict | None:
    """The dictionary's particle reading of a bare particle, or its twin's respelled where it has none
    (ghair_amila_other `read_as`: لوما read as لولا)."""
    twin = book_map("ghair_amila_other", "read_as").get(particle)
    own = next((r for r in _analyses(twin["twin"] if twin else particle) if r.get("catib6") == "PRT"), None)
    if not (own and twin):
        return own
    return {key: value.replace(twin["twin_diac"], twin["diac"]) if isinstance(value, str) else value
            for key, value in own.items()}


def _twin_particle(typed: str, opens: bool) -> dict | None:
    """لَوْمَا تَأْتِينَا: a particle the dictionary reads only as a noun (لَوْم) is its twin's reading, where it
    opens its sentence (لها صدر الكلام) and its typed marks fit that reading; لَوْمًا with tanween is the noun."""
    if not opens or has_tanween(typed) or bare_letters(typed) not in book_map("ghair_amila_other", "read_as"):
        return None
    reading = _particle_reading(bare_letters(typed))
    return reading if reading and best_reading(typed, [reading]) else None


def _noun_only_particle(typed: str) -> dict | None:
    """لَوْلَاكَ، لَوْلَاهُ، لَوْلَايَ: لولا and لوما (حرف امتناع لوجود) open only on a noun (condition `before`), so a
    pronoun written on one is that noun, its مبتدأ (Ibn Aqil, الابتداء: لولاي ولولاك ولولاه); never لَ + the verb وَلَّى."""
    bare, marked = bare_letters(typed), letters(typed)
    for particle in book_words("ghair_amila_other", "conditional_particles"):
        said = bare[len(particle):]
        own = (condition_of(particle) or {}).get("before") == "noun" and bare.startswith(particle) \
            and said in book_words("damir_muttasil", "on_nouns") \
            and _particle_reading(particle)
        if not own:
            continue
        pronoun = "".join(letter + "".join(sorted(marks)) for letter, marks in marked[len(particle):])
        reading = {**own, "diac": own["diac"] + pronoun, "atbtok": f"{own['atbtok']}_+{pronoun}", "catib6": "PRT+NOM",
                   "ud": f"{own['ud']}+PRON", "enc0": f"{noun_reader.pronoun_name(said, marked[-1][1])}_pron",
                   "bw": f"{own['bw']}+{pronoun}/PRON"}
        return reading if best_reading(typed, [reading]) else None
    return None


_SEATED_ON_WAW = re.compile("(?<=ُ)و(?=[ً-ِ])")


def _hamza_written_waw(typed: str, disambiguator=None) -> dict | None:
    """كُفُوًا، هُزُوًا: the Qur'an's hand writes a hamza seated on و after a damma as a bare و
    (كُفُؤًا), so a voweled و after a damma that no reading fits is read as that ؤ, spelled as typed."""
    seated = _SEATED_ON_WAW.sub("ؤ", typed)
    if seated == typed:
        return None
    found = best_reading(seated, (_ranked([seated], disambiguator) or [[]])[0])
    return found and {**found, "diac": found["diac"].replace("ؤ", "و"), "atbtok": found["atbtok"].replace("ؤ", "و")}


def _hamza_stem_seat(typed: str, disambiguator=None) -> dict | None:
    """يَقْرَؤُهُ: a hamza the vowels around it seat on و or ي (its damma after a fatha), the dictionary may write on the
    stem's alif only (يقرأه); no reading fitting, the word is read on the alif and spelled on the typed seat.
    The I-verb أَفْعَلُ is none: the elative has its letters and vowels (يَؤُمُّ الْقَوْمَ أَقْرَؤُهُمْ), so the
    seat cannot tell the two apart and the word is left to the noun's reading."""
    for at, (letter, _) in enumerate(letters(typed)):
        if letter not in "ؤئ":
            continue
        on_alif = "".join("أ" + "".join(marks) if i == at else c + "".join(marks) for i, (c, marks) in enumerate(letters(typed)))
        seated = [r for r in (_ranked([on_alif], disambiguator) or [[]])[0] if r.get("per") != "1"
                 and NO_ANALYSIS not in r.get("atbtok", "") and [c for c, _ in letters(r.get("diac", ""))][at:at + 1] == ["أ"]]
        if found := best_reading(on_alif, seated):
            return {**found, "diac": _reseated(found["diac"], at, letter), "atbtok": _reseated(found["atbtok"], at, letter)}
    return None


def _reseated(spelled: str, at: int, seat: str) -> str:
    """The word with its `at`-th letter (its marks and CAMeL's _ + not counted) put on `seat`."""
    seen = -1
    for i, c in enumerate(spelled):
        seen += c.isalpha()
        if seen == at:
            return spelled[:i] + seat + spelled[i + 1:]
    return spelled


def _added(reading: dict, typed: str) -> int:
    """The shaddas a reading puts on that the typed word lacks: letters the writing does not show."""
    return reading.get("diac", "").count("ّ") - typed.count("ّ")


DOER = ("per", "gen", "num")
# the one-letter joining particles, and CAMeL's name for each (prc2)
_JOINING = (("و", "wa"), ("ف", "fa"))


def _same(reading: dict, said: dict, keys: tuple[str, ...]) -> bool:
    """The reading has what sarf's table said of these (its person, gender, number, verb), where both said one;
    a verb by its letters, the two spelling its last vowel otherwise (ضَرَب، ضَرَبَ). A reading that leaves one
    unsaid does not contradict it (the dictionary's أَلَسْتُ is ليس, its number left "-")."""
    return all(bare_letters(reading.get(key) or "") == bare_letters(said[key]) for key in keys
               if "-" not in (said.get(key, "-"), reading.get(key, "-")))


def _other_bab(sarf: dict, listed: dict, typed: str) -> bool:
    """كَبُرَ against the dictionary's كَبَرَ: an active past the typed vowels contradict is another باب of the root, a
    verb of its own (فَعَلَ، فَعِلَ، فَعُلَ: the middle vowel of the past is the verb's, Shadha al-Arf; page unchecked),
    so it does not stand for the past the table reads. A shadda on a letter typed with a sukun (بَيَّنَا against بَيْنَا) is the
    same verb with its shadda left off, not another باب."""
    listed_diac = listed.get("diac", "")
    if [bare_letters(c) for c, _ in letters(typed)] != [bare_letters(c) for c, _ in letters(listed_diac)]:
        return False  # other letters (a hamza seat, a dropped letter): the vowels do not line up to compare
    return sarf.get("asp") == listed.get("asp") == "p" and sarf.get("vox") == listed.get("vox") == "a" \
        and not _adds_shadda(typed, listed_diac) and vowel_agreement(typed, listed_diac) is None


def _voice_against(sarf: dict, listed: dict, typed: str) -> bool:
    """أَغَارُ against the dictionary's passive أُغَارُ: a passive the typed vowels are against is not the word typed, so it
    does not stand for the active the table reads (غَارَ يَغَارُ، I am jealous). Only that way round: a passive typed
    (خُلِقَ) keeps the dictionary's active, which the voice is read from later."""
    return sarf.get("vox") == "a" and listed.get("vox") == "p" and vowel_agreement(typed, listed.get("diac", "")) is None


def _agreeing(typed: str, ranked: list[dict], undoubled: bool = False) -> bool:
    """Some real reading (not the no-analysis guess), spelled with the typed letters (الحاقّة is no
    إلحاقه), has no vowel against the typed ones. `undoubled`: nor doubles a letter typed with a vowel and no
    shadda, so كَبُرَ, which the dictionary has only as كَبَرَ, is not the كَ + بُرّ its letters also spell."""
    spelled = [bare_letters(c) for c, _ in letters(typed)]
    same = [r for r in ranked if NO_ANALYSIS not in r.get("atbtok", "")
            and [bare_letters(c) for c, _ in letters(r.get("diac", ""))] == spelled]
    if undoubled:
        same = [r for r in same if not _doubles_a_voweled_letter(typed, r.get("diac", ""))]
    return best_reading(typed, same) is not None


def _adds_shadda(typed: str, reading: str) -> bool:
    """The reading doubles a letter the reader typed bare or with a sukun: its shadda was just left off."""
    return any(SHADDA in read and SHADDA not in said and not said & {"\u064e", "\u064f", "\u0650"}
               for (_, said), (_, read) in zip(letters(typed), letters(reading)))

def _doubles_a_voweled_letter(typed: str, reading: str) -> bool:
    """The reading doubles a letter the reader typed with a vowel and no shadda: a vowel written shows the letter
    was looked at, so its shadda was not just left off."""
    return any(SHADDA in read and SHADDA not in said and said & {"\u064e", "\u064f", "\u0650"}
               for (_, said), (_, read) in zip(letters(typed), letters(reading)))


def _kind(reading: dict) -> str | None:
    """verb, noun or particle: the kinds a word's two readings can differ in."""
    pos = reading.get("pos", "")
    return ("verb" if pos == "verb" else "noun" if pos in NOUNISH - {"abbrev"} or pos.startswith("pron")
            else "particle" if pos.startswith(("part", "prep", "conj")) else None)


def _other_voice(typed: str, read: dict) -> str | None:
    """The voice sarf's table also gives the verb's letters as typed (كتب: كَتَبَ and كُتِبَ), its joined letters
    and pronoun cut off; None where the table has only the voice read, or the verb takes no object (ذهب)."""
    if is_one(read.get("lex", ""), "intransitive_verbs"):
        return None
    marked, bare = letters(typed), base_of(typed, read.get("atbtok"))
    at = "".join(c for c, _ in marked).find(bare)
    other = "p" if read["vox"] == "a" else "a"
    return other if at >= 0 and other in verb_reader.voices(marked[at:at + len(bare)], read["asp"]) else None


def _rival(typed: str, read: dict, ranked: list[dict]) -> dict | None:
    """The other reading the typed letters leave open, the one a second reading swaps in: the verb's other
    voice (كتب bare is كَتَبَ or كُتِبَ), else a close-ranked reading of another kind (verb, noun, particle)
    spelled with the letters typed. A word with a vowel typed on it speaks for itself (سِرْتُ, فُتِحَ kept as
    فَتَحَ): only a bare word has a rival."""
    if not no_vowels_typed([typed]):
        return None
    if read.get("pos") == "verb" and read.get("vox") in ("a", "p") and read.get("asp") in ("p", "i") \
            and (other := _other_voice(typed, read)):
        return {**read, "vox": other}
    kind = _kind(read)
    return next((r for r in ranked[:get_settings().rival_ranks]
                 if kind and _kind(r) not in (None, kind) and NO_ANALYSIS not in r.get("atbtok", "") and _agreeing(typed, [r])), None)


def _widened(token: str, ranked: list[dict]) -> list[dict]:
    """The context ranker's readings, then the word's whole list, never one CAMeL could not analyse."""
    return [r for r in ranked + (_ranked([token], None) or [[]])[0] if NO_ANALYSIS not in r.get("atbtok", "")]


def _min_phrase_follows(after: list[dict]) -> bool:
    """A مِنْ among these words, with no verb before it: the elative's مفضول (Tashil V1 p132)."""
    for reading in after:
        if reading.get("pos") == "verb":
            return False
        if reading.get("pos") == "prep" and reading.get("lex") == "مِن":
            return True
    return False


def _speaker(typed: str) -> bool:
    """أَنَا, or a sister of إنّ with "me" on it (إِنِّي، إِنَّنِي، لَعَلِّي), a joining وَ or فَ on it or not (وَإِنِّي): the one
    speaking stands before what follows."""
    bare = strip_diacritics(typed)  # its hamza kept: the book lists إنّ with it
    if bare[:1] in "وف" and len(bare) > 3:
        bare = bare[1:]
    return bare in ("أنا", "انا") or any(bare.endswith(me) and is_one(bare[:-len(me)], "inna") for me in ("ني", "ي"))


def _elative_reading(token: str, step: tuple) -> dict | None:
    """The word as the elative noun: sarf's shape أَفْعَل, or the dictionary's own reading with the
    elative's pattern (the doubled أَحَبّ، أَدَقّ, which sarf's shapes lack), the typed vowels choosing."""
    word, ranked = step
    return noun_reader.reading_of(word) or best_reading(word, [
        r for r in _widened(token, ranked) if r.get("pos") in NOUNISH and elative_shape(r.get("pattern", ""), r.get("lex", ""))])


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

    if engine.camel is not None:
        picks = picks or pick(tokens)
        tokens = as_said(tokens, picks)
        before = ["", *map(strip_diacritics, tokens[:-1])]
        return [_analysis_dict_from_camel(t, a, b, n, r.get("asp", "")) if a else analyze_word(t)
                for t, a, b, n, r in zip(tokens, picks, before, [*tokens[1:], ""], [*picks[1:], {}], strict=True)]

    if engine.qalsadi is not None:
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
