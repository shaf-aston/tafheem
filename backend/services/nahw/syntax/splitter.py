"""Model-free word splitting: typed words and their picked readings -> the clitic-split pieces
the CATiB parser links (catib_onnx.links).

CATiB splits off conjunctions, prepositions and pronoun suffixes, but folds the determiner ال
into a feature. data/parser/clitic_feats.csv, the only record of a clitic's own case/state, is
adapted from CAMeL-Lab/camel_parser (MIT, Copyright 2023 NYU Abu Dhabi). Nothing here runs a model.
"""
from __future__ import annotations

import csv
import functools
import logging

from backend.config import data_path
from backend.services.nahw.syntax.facts.word import typed_case_of
from backend.services.sarf.morphology import reading_lemma, reading_root
from backend.services.text.harakat import NO_ANALYSIS, base_of, stuck_letters, typed_case, weak_last

logger = logging.getLogger(__name__)


@functools.cache
def _clitic_table() -> list[dict[str, str]]:
    with (data_path("catib_parser_dir") / "clitic_feats.csv").open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


@functools.cache
def _ar2bw():
    # Imported here, not at module top: camel_tools pulls in pandas, which must load after onnxruntime.
    from camel_tools.utils.charmap import CharMapper

    return CharMapper.builtin_mapper("ar2bw")


# ─────────────────────────────────────────────────────────────────────────────
# CAMeL analysis -> clitic-split tokens (form, lemma, pos, ud, feats)
# ─────────────────────────────────────────────────────────────────────────────

# CATiB folds the ال determiner into a feature (prc0=Al_det) rather than a
# token, so only these clitic slots ever produce a separate token.
# A word the analyzer could not read at all: its pick has no
# atbtok/catib6/ud (those come from the morphology DB, not the tagger), so it
# is reported as one unsplit token with a coarse guess at its CATiB tag.
_POS_TO_CATIB6 = {
    "verb": "VRB", "noun": "NOM", "noun_prop": "NOM", "noun_num": "NOM",
    "pron": "NOM", "adj": "NOM", "adj_comp": "NOM", "adv": "NOM",
    "prep": "PRT", "conj": "PRT", "conj_sub": "PRT", "part": "PRT",
    "part_neg": "PRT", "part_focus": "PRT", "det": "PRT", "interj": "PRT",
    "punc": "PNX", "digit": "NOM", "abbrev": "NOM",
}

# CAMeL's part of speech -> the UD tag a word takes when CAMeL gives none of its own
_UD_OF = {"verb": "VERB", "noun_prop": "PROPN", "adj": "ADJ", "adj_comp": "ADJ"}


def _is_clitic(token: str) -> bool:
    return (token.startswith("+") or token.endswith("+")) and token.strip("+") != ""


def _clitic_token_feats(token: str, order: str, stem: dict) -> dict:
    """Look up token's own asp/vox/stt/cas/pos in clitic_feats.csv, keyed by
    the clitic's surface form and by whichever prcN/enc0 slot is active on
    the stem. UD is not looked up here: the stem analysis's own 'ud' field is
    already split per subtoken by the caller, clitics included, so this only
    supplies what the CSV alone records (a clitic's own case/state/pos).
    """
    from camel_tools.utils.dediac import dediac_ar

    surface = _ar2bw()(dediac_ar(token.strip("+")))
    active = [f"{k}:{v}" for k, v in stem.items()
              if k.startswith(order) and v not in ("0", "na")]
    for deciding_feat in active:
        for row in _clitic_table():
            if row["clitic"] == surface and row["deciding_feat"] == deciding_feat:
                return {
                    "pos_camel": row["pos"],
                    "asp": row["asp"], "vox": row["vox"], "stt": row["stt"], "cas": row["cas"],
                    "token_type": deciding_feat.split(":")[0],
                }
    logger.warning("no clitic_feats.csv row for %r (%s), using stem features", token, active)
    return {
        "pos_camel": stem.get("pos", ""),
        "asp": "na", "vox": "na", "stt": "na", "cas": "na", "token_type": order,
    }


# The letters of each attached pronoun by CAMeL's person (enc0 1p_dobj → نا): the one-person ي is
# ني on a verb (نون الوقاية) and ي on a noun or particle.
_PRONOUN_LETTERS = {"1s": ("ني", "ي"), "1p": ("نا",), "2ms": ("ك",), "2fs": ("ك",), "2d": ("كما",), "2mp": ("كم",),
                    "2fp": ("كن",), "3ms": ("ه",), "3fs": ("ها",), "3d": ("هما",), "3mp": ("هم",), "3fp": ("هن",)}


def pronoun_cut_off(a: dict) -> dict:
    """أَيّكُم، يَفُوتُنا: the dictionary files a few words with their attached pronoun (enc0) left unsplit;
    the pronoun is cut off the end by its own letters, as every other word's is (كِتاب_+كُم، يَزُور_+نِي),
    so it stands in the sentence as the word's مضاف إليه or object."""
    from camel_tools.utils.dediac import dediac_ar

    atbtok, enc = a.get("atbtok") or "", str(a.get("enc0", ""))
    if "_" in atbtok or not enc.endswith(("_poss", "_dobj", "_pron")):
        return a
    letters = dediac_ar(atbtok)
    starts = [i for i, ch in enumerate(atbtok) if dediac_ar(ch)]  # where each letter, not a mark, stands
    # نون الوقاية comes before the ي of a verb or particle, never of a noun's own (دِينِي: دين_+ي)
    for pronoun in ("ي",) if enc == "1s_poss" else _PRONOUN_LETTERS.get(enc.split("_")[0], ()):
        if letters.endswith(pronoun) and len(letters) > len(pronoun):
            cut = starts[len(letters) - len(pronoun)]
            return {**a, "atbtok": f"{atbtok[:cut]}_+{atbtok[cut:]}"}
    return a


def _as_written(pronoun: str, word: str) -> str:
    """عِنْدِي، مَعِي: the tokenisation files the one-person pronoun as +ني where the word writes only ي;
    the pronoun is the letters the word ends with, so its card and its column say «ي»."""
    from camel_tools.utils.dediac import dediac_ar

    letters, written = pronoun.strip("+"), dediac_ar(word)
    while letters and not written.endswith(letters):
        letters = letters[1:]
    return f"+{letters}" if letters else pronoun


def split_word(word: str, a: dict) -> list[dict]:
    """One CAMeL analysis dict -> a list of subtoken dicts (one per CATiB
    clitic/baseword), each with form/lemma/pos/pos_camel/ud/asp/vox/stt/cas/
    token_type. Mirrors camel_parser's get_main_features_df +
    add_remaining_features, trimmed to the feature set this app keeps.
    """
    from camel_tools.utils.dediac import dediac_ar

    root = reading_root(a)

    def clean(text: str, fallback: str | None = None) -> str:
        d = dediac_ar(text)
        return d.replace("_", "").replace("ـ", "") or (d if fallback is None else fallback)

    def baseword(form: str, lex_default: str, pos: str, ud: str, **extra) -> dict:
        return {
            "form": form, "lemma": reading_lemma(word, a, root) if "lex" in a else dediac_ar(lex_default),
            "pos": pos, "pos_camel": a.get("pos", ""), "ud": ud,
            "asp": a.get("asp", "na"), "vox": a.get("vox", "na"),
            "stt": a.get("stt", "na"), "cas": a.get("cas", "na"), "num": a.get("num", "na"),
            "per": a.get("per", "na"), "gen": a.get("gen", "na"),
            "root": root,
            "diac": a.get("diac", ""),
            "weak_last": weak_last(a), "base": base_of(word, a.get("atbtok")), **extra, "token_type": "baseword",
        }

    if "+" not in (a.get("catib6") or "") and (cut := pronoun_cut_off(a)) is not a:
        # أَيّكُم: an entry with no tags of its own, its pronoun still a word: the word's coarse tag, then a noun's;
        # يَفُوتُنا: tagged as one verb, the verb keeps its tags and the pronoun is a noun
        coarse = a.get("catib6") or _POS_TO_CATIB6.get(a.get("pos", ""), "NOM")
        a = {**cut, "catib6": f"{coarse}+NOM", "ud": f"{a.get('ud', coarse) if a.get('catib6') else coarse}+PRON"}
    if not a.get("catib6") or "atbtok" not in a:
        # The analyzer found nothing for this word; its pick's own tag is all
        # there is, so it is reported as a single unsplit token.
        catib6 = _POS_TO_CATIB6.get(a.get("pos", ""), "NOM")
        base = baseword(clean(word, word), word, catib6, catib6)
        if not str(a.get("prc1", "")).endswith("_prep"):
            return [base]
        # لِلّٰهِ: the analyser knows the word opens with a preposition but files it unsplit;
        # the preposition is its first letter, and the noun is its lemma (الله)
        letter = base["form"][:1]
        return [{"form": f"{letter}+", "lemma": f"{letter}+", "base": letter, "pos": "PRT", "pos_camel": "prep", "ud": "ADP",
                 "asp": "na", "vox": "na", "stt": "na", "cas": "na", "token_type": "prc1"},
                {**base, "form": base["lemma"], "base": base["form"][1:], "cas": "g"}]

    # the pieces are the tokenisation's, not the tags': ثُلْثَ_+هُ is tagged NOM alone, and
    # left whole its pronoun is lost to the sentence (the بدل's pronoun back to its noun).
    # Only a trailing pronoun is split untagged: it is a noun as the padding below makes it.
    # a word the analyser could not read keeps its tags, but its text is the word, not the NOAN mark
    pieces = [base_of(word, a["atbtok"]) if p == NO_ANALYSIS else p for p in a["atbtok"].split("_")]
    if len(pieces) == 1:
        toks, catib6s, uds = pieces, [a["catib6"]], [a["ud"]]
    elif "+" not in a["catib6"] and not all(p.startswith("+") for p in pieces[1:]):
        # فَلَيْسَتِ، بِأَرْبَعَةِ: one tag for a word with a word joined in front, and it is the
        # front word's; each piece takes its own kind: the joined word a particle, a pronoun
        # a noun, the word itself the dictionary's part of speech
        toks = pieces
        catib6s = ["PRT" if p.endswith("+") else "NOM" if p.startswith("+") else _POS_TO_CATIB6.get(a.get("pos", ""), "NOM")
                   for p in pieces]
        uds = [a["ud"] if p.endswith("+") else "PRON" if p.startswith("+") else _UD_OF.get(a.get("pos", ""), "NOUN")
               for p in pieces]
    else:
        toks = pieces
        catib6s = a["catib6"].split("+")
        uds = a["ud"].split("+")
        # A rare tokenization/tagging length mismatch: repeat the last known
        # tag rather than dropping a token CATiB6 does not have one for.
        while len(catib6s) < len(toks):
            catib6s.append(catib6s[-1] if catib6s else "NOM")
        while len(uds) < len(toks):
            uds.append(uds[-1] if uds else "X")

    out: list[dict] = []
    for tok, catib6, ud in zip(toks, catib6s, uds):
        form = clean(tok)
        if not _is_clitic(tok):
            # pattern: the analyser's own word-shape, e.g. 1ا2ِ3 for فاعل: how a participle is told from a noun
            # guessed: the dictionary had no reading of the word, so its "name" is only a guess (أَفْشُوا)
            out.append({**baseword(form, tok, catib6, ud, pattern=a.get("pattern", "")),
                        "guessed": NO_ANALYSIS in a.get("atbtok", "")})
        else:
            feats = _clitic_token_feats(tok, "prc" if tok.endswith("+") else "enc", a)
            out.append({
                "form": form, "lemma": form, "base": form.strip("+"), "written": _as_written(form, word) if tok.startswith("+") else form,
                "pos": catib6, "pos_camel": feats["pos_camel"], "ud": ud,
                "asp": feats["asp"], "vox": feats["vox"],
                "stt": feats["stt"], "cas": feats["cas"],
                "token_type": feats["token_type"],
            })
    return out


def pieces(words: list[str], picks: list[dict]) -> list[dict]:
    """Each typed word split by its pick into the pieces the parser links, in order; each piece
    carries the case typed on its word (word_case) and the tag of the word it is written on (on)."""
    subtokens: list[dict] = []
    for word, pick in zip(words, picks, strict=True):
        split = split_word(word, pick)
        # the vowel of an attached pronoun is the pronoun's: عِلْمَهُ is in nasb, not raf'
        stuck_on = stuck_letters(split, word)
        # the typed word rides on its one base piece from the start, so the book's masks and links read its case through
        # the one view (facts.typed_case_of: the six nouns, a written nasb alif, a منقوص, the hundreds) as every later step does
        bases = [t for t in split if t.get("token_type") == "baseword"]
        if len(bases) == 1:
            bases[0].update(typed=word, stuck_on=stuck_on)
        word_case = typed_case_of(bases[0]) if len(bases) == 1 else typed_case(word, stuck_on)
        # وَأَنْ: a letter written on a particle is no جار, so each piece keeps the tag of the word it is written on, and
        # the case typed on that word (وَخُلُقُهُ: a و on a word in raf' joins, facts.is_preposition)
        on = bases[0]["pos"] if bases else None
        subtokens.extend({**t, "word_case": word_case, "on": on} for t in split)
    return subtokens


def shown(tok: dict) -> dict:
    """A piece as the sentence writes it, the tokenisation's spelling kept only for the parser."""
    written = tok.get("written")
    rest = {key: value for key, value in tok.items() if key != "written"}
    return {**rest, "form": written, "lemma": written, "base": written.strip("+")} if written and written != tok["form"] else rest
