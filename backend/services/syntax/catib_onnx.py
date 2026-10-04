"""Torch-free CATiB dependency parser: whitespace-split words -> a head/rel link
for each word, over the light clitic split those links assume.

CAMeL Tools' BERT disambiguator picks one reading per word; its atbtok/catib6/ud
fields say whether the word is one token or several (CATiB splits off
conjunctions, prepositions and pronoun suffixes, but folds the determiner ال into
a feature). The split forms go to an ONNX biaffine parser (onnxruntime and numpy
only) for head/rel. onnxruntime must be imported before camel_tools (Windows DLL
load order). data/parser/clitic_feats.csv, the only record of a clitic's own
case/state, is adapted from CAMeL-Lab/camel_parser (MIT, Copyright 2023 NYU Abu Dhabi).
"""
from __future__ import annotations

import csv
import json
import logging
import threading
import time
from typing import NamedTuple

import onnxruntime as ort  # must precede camel_tools (see module docstring)

import numpy as np
from tokenizers import Tokenizer

from backend.services.arabic_text import bare_letters
from backend.config import data_path, get_settings
from backend.services.syntax import decode
from backend.services.syntax.mask import book_links, book_mask
from backend.services.harakat import best_reading, past_passive_shape, typed_case, weak_last, base_of

logger = logging.getLogger(__name__)


class _Parser(NamedTuple):
    cfg: dict
    rel_labels: list[str]
    clitic_table: list[dict[str, str]]
    bpe: Tokenizer
    enc_sess: object
    scorer_sess: object
    ar2bw: object
    disambiguator: object


# Built once by warm() (at startup, or else the first parse()) and published whole.
_parser: _Parser | None = None

# Loading takes seconds (the BERT disambiguator alone is ~8s on a fast machine),
# so a second request always arrives while the first is still loading. Without
# this lock it loaded everything a second time beside the first, and a third,
# finding the encoder set but the disambiguator not, crashed on None and
# quietly fell back to the rule engine. One loader; the rest wait for it.
_load_lock = threading.Lock()
# Why the load failed, or "" when it has not. A missing package or model does
# not fix itself, so a failed load is not paid for again on every request, and
# /api/health can say what went wrong instead of "ready".
_load_error = ""


def files_present() -> bool:
    d = data_path("catib_parser_dir")
    names = ("encoder.onnx", "scorer.onnx", "tokenizer.json", "labels.json",
              "config.json", "clitic_feats.csv")
    return all((d / n).exists() for n in names)


def state() -> str:
    """"ready", "loading", "not loaded" or "failed: <why>", for /api/health."""
    if _parser is not None:
        return "ready"
    if _load_error:
        return f"failed: {_load_error}"
    return "loading" if _load_lock.locked() else "not loaded"


def warm() -> None:
    """Load the ONNX sessions, tokenizer and BERT disambiguator once (a ~110MB
    int8 encoder plus CAMeL's BERT), at startup so the first sentence typed does
    not wait, or on the first parse() when warming is off.
    """
    global _parser, _load_error
    if _parser is not None:
        return
    with _load_lock:
        if _parser is not None:
            return
        if _load_error:
            raise RuntimeError(f"CATiB parser failed to load: {_load_error}")
        try:
            _parser = _load()
        except Exception as exc:
            _load_error = f"{type(exc).__name__}: {exc}"
            raise


def _load() -> _Parser:
    settings = get_settings()
    if not settings.catib_parser_enabled:
        raise RuntimeError("CATiB parser is disabled (catib_parser_enabled=False)")

    d = data_path("catib_parser_dir")
    if not files_present():
        raise RuntimeError(f"CATiB parser model files missing under {d}")

    started = time.perf_counter()
    with (d / "config.json").open(encoding="utf-8") as f:
        cfg = json.load(f)
    with (d / "labels.json").open(encoding="utf-8") as f:
        rel_labels = json.load(f)["itos"]
    with (d / "clitic_feats.csv").open(encoding="utf-8") as f:
        clitic_table = list(csv.DictReader(f))

    bpe = Tokenizer.from_file(str(d / "tokenizer.json"))
    enc_sess = ort.InferenceSession(str(d / "encoder.onnx"), providers=["CPUExecutionProvider"])
    scorer_sess = ort.InferenceSession(str(d / "scorer.onnx"), providers=["CPUExecutionProvider"])

    # Imported here, not at module top: camel_tools pulls in pandas/torch,
    # which must load after onnxruntime.
    from camel_tools.disambig.bert import BERTUnfactoredDisambiguator
    from camel_tools.utils.charmap import CharMapper

    disambiguator = BERTUnfactoredDisambiguator.pretrained(
        "msa", top=settings.catib_readings, use_gpu=False)
    ar2bw = CharMapper.builtin_mapper("ar2bw")
    logger.info("CATiB ONNX parser ready (%s) in %.1fs", d, time.perf_counter() - started)
    return _Parser(cfg, rel_labels, clitic_table, bpe, enc_sess, scorer_sess, ar2bw, disambiguator)


# ─────────────────────────────────────────────────────────────────────────────
# CAMeL analysis -> clitic-split tokens (form, lemma, pos, ud, feats)
# ─────────────────────────────────────────────────────────────────────────────

# CATiB folds the ال determiner into a feature (prc0=Al_det) rather than a
# token, so only these clitic slots ever produce a separate token.
# A word the analyzer could not read at all: BERT's own prediction has no
# atbtok/catib6/ud (those come from the morphology DB, not the tagger), so it
# is reported as one unsplit token with a coarse guess at its CATiB tag.
_POS_TO_CATIB6 = {
    "verb": "VRB", "noun": "NOM", "noun_prop": "NOM", "noun_num": "NOM",
    "pron": "NOM", "adj": "NOM", "adj_comp": "NOM", "adv": "NOM",
    "prep": "PRT", "conj": "PRT", "conj_sub": "PRT", "part": "PRT",
    "part_neg": "PRT", "part_focus": "PRT", "det": "PRT", "interj": "PRT",
    "punc": "PNX", "digit": "NOM", "abbrev": "NOM",
}


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

    surface = _parser.ar2bw(dediac_ar(token.strip("+")))
    active = [f"{k}:{v}" for k, v in stem.items()
              if k.startswith(order) and v not in ("0", "na")]
    for deciding_feat in active:
        for row in _parser.clitic_table:
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


def _split_word(word: str, a: dict) -> list[dict]:
    """One CAMeL analysis dict -> a list of subtoken dicts (one per CATiB
    clitic/baseword), each with form/lemma/pos/pos_camel/ud/asp/vox/stt/cas/
    token_type. Mirrors camel_parser's get_main_features_df +
    add_remaining_features, trimmed to the feature set this app keeps.
    """
    from camel_tools.utils.dediac import dediac_ar

    def clean(text: str, fallback: str | None = None) -> str:
        d = dediac_ar(text)
        return d.replace("_", "").replace("ـ", "") or (d if fallback is None else fallback)

    def baseword(form: str, lex_default: str, pos: str, ud: str, **extra) -> dict:
        return {
            "form": form, "lemma": dediac_ar(a.get("lex", lex_default)),
            "pos": pos, "pos_camel": a.get("pos", ""), "ud": ud,
            "asp": a.get("asp", "na"), "vox": a.get("vox", "na"),
            "stt": a.get("stt", "na"), "cas": a.get("cas", "na"), "num": a.get("num", "na"),
            "weak_last": weak_last(a), "base": base_of(word, a.get("atbtok")), **extra, "token_type": "baseword",
        }

    if not a.get("catib6") or "atbtok" not in a:
        # The analyzer found nothing for this word; BERT's own tag is all
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
    pieces = a["atbtok"].split("_")
    if len(pieces) == 1 or ("+" not in a["catib6"] and not all(p.startswith("+") for p in pieces[1:])):
        toks, catib6s, uds = [a["atbtok"]], [a["catib6"]], [a["ud"]]
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
            out.append(baseword(form, tok, catib6, ud, pattern=a.get("pattern", "")))
        else:
            feats = _clitic_token_feats(tok, "prc" if tok.endswith("+") else "enc", a)
            out.append({
                "form": form, "lemma": form, "base": form.strip("+"),
                "pos": catib6, "pos_camel": feats["pos_camel"], "ud": ud,
                "asp": feats["asp"], "vox": feats["vox"],
                "stt": feats["stt"], "cas": feats["cas"],
                "token_type": feats["token_type"],
            })
    return out


def _reading(word: str, readings: list[dict]) -> dict:
    """The best reading of a word that does not contradict its typed vowels.

    The disambiguator reads bare letters, so its favourite may be a word the
    reader plainly did not write. The vowels typed are the reader's own evidence
    and win: the reading sharing most of them is used (harakat.best_reading). The
    analyser's guessed proper noun has no vowels to disagree with, so it never
    wins that way. When no real reading agrees the favourite is kept, since the
    naming layer still reads the vowels itself (a passive بُعْثِرَ).
    """
    if not readings:
        return {"pos": "", "lex": word}
    real = [r for r in readings if "NOAN" not in r.get("atbtok", "")]
    verbs = [r for r in readings
             if r.get("pos") == "verb" and bare_letters(r.get("diac", "")) == bare_letters(word)]
    if past_passive_shape(word) and verbs:
        return verbs[0]
    return best_reading(word, real) or readings[0]


# ─────────────────────────────────────────────────────────────────────────────
# ONNX biaffine parser: subtoken forms -> heads + rel labels
# (decoding lives in decode.py)
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize_and_pack(forms: list[str]) -> tuple[np.ndarray, np.ndarray, list[tuple[int, int]]]:
    bos, fix_len = _parser.cfg["bos_index"], _parser.cfg["fix_len"]
    groups = [[bos]]
    for w in forms:
        ids = _parser.bpe.encode(w, add_special_tokens=False).ids[:fix_len]
        groups.append(ids if ids else [bos])

    flat: list[int] = []
    spans: list[tuple[int, int]] = []
    for g in groups:
        spans.append((len(flat), len(flat) + len(g)))
        flat.extend(g)

    return np.array([flat], dtype=np.int64), np.ones((1, len(flat)), dtype=np.int64), spans


def _pool_words(mixed_hidden: np.ndarray, spans: list[tuple[int, int]]) -> tuple[np.ndarray, np.ndarray]:
    _, _, hidden = mixed_hidden.shape
    out = np.zeros((1, len(spans), hidden), dtype=np.float32)
    for j, (s, e) in enumerate(spans):
        out[0, j] = mixed_hidden[0, s:e].mean(axis=0)
    return out, np.ones((1, len(spans)), dtype=bool)


def _decode(s_arc: np.ndarray, s_rel: np.ndarray, toks: list[dict]) -> tuple[list[int], list[str]]:
    """Heads and labels, best first among the links the book allows (mask.py)."""
    n_words = len(toks)
    L = n_words + 1
    rel_labels = _parser.rel_labels
    rel_ok = book_mask(toks, rel_labels)
    heads = decode.heads(s_arc[:L, :L])
    rels = [rel_labels[int(np.argmax(np.where(rel_ok[i + 1, heads[i]], s_rel[i + 1, heads[i]], -np.inf)))]
            for i in range(n_words)]
    return book_links(toks, heads, rels)


def _parse_forms(toks: list[dict]) -> tuple[list[int], list[str]]:
    ids, mask, spans = _tokenize_and_pack([t["form"] for t in toks])
    (mixed,) = _parser.enc_sess.run(None, {"input_ids": ids, "attention_mask": mask})
    word_embed, wmask = _pool_words(mixed, spans)
    s_arc, s_rel = _parser.scorer_sess.run(
        None, {"word_embed": word_embed.astype(np.float32), "mask": wmask})
    return _decode(s_arc[0], s_rel[0], toks)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def parse(words: list[str]) -> list[dict]:
    """Dependency-parse one sentence's already-split words.

    words: the sentence split on whitespace/punctuation (not on clitics --
    that split happens inside this function).

    Returns one dict per output token (a clitic may add tokens beyond
    len(words)), each with: id (1-based), form, lemma, pos (CATiB6 tag),
    pos_camel (CAMeL's own finer tag), ud, vox, asp, stt, cas, token_type,
    head (1-based, 0 = sentence root), rel (CATiB dependency label).
    """
    if not words:
        return []

    warm()

    disambiguated = _parser.disambiguator.disambiguate(words)
    subtokens: list[dict] = []
    for word, dw in zip(words, disambiguated):
        readings = [scored.analysis for scored in dw.analyses]
        pieces = _split_word(word, _reading(word, readings))
        # the vowel of an attached pronoun is the pronoun's: عِلْمَهُ is in nasb, not raf'
        stuck_on = sum(len(bare_letters(t["form"].strip("+"))) for t in pieces if t["form"].startswith("+"))
        subtokens.extend({**t, "case": typed_case(word, stuck_on)} for t in pieces)

    heads, rels = _parse_forms(subtokens)

    return [
        {"id": i + 1, **tok, "head": heads[i], "rel": rels[i]}
        for i, tok in enumerate(subtokens)
    ]
