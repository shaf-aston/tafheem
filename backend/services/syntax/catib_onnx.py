"""Torch-free CATiB dependency parser: whitespace-split words -> a head/rel
link for each word plus the light clitic split those links assume.

Pipeline: CAMeL Tools' BERT disambiguator (camel_tools.disambig.bert) picks
one morphological reading per word -- this pulls in torch itself, but that
import happens inside camel_tools, never in this file. Each reading's own
'atbtok'/'catib6'/'ud' fields say whether it is one token or several (CATiB
splits off conjunctions, prepositions and pronoun suffixes as their own
tokens, but folds the determiner ال into a feature instead of a token). Those
split forms are fed to an ONNX biaffine parser (BERT encoder + arc/label
scorer, exported from CAMeLBERT-CATiB-biaffine) for head/rel -- onnxruntime
and numpy only, no torch.

Proven first as a spike (see the project's camel_parser_trial scratchpad,
onnx_spike/parse_onnx.py + decode.py): this module ports that pipeline,
unchanged in shape, into the app.

Windows import-order bug (hit while building the spike, see its
build_fresh_conll.py): onnxruntime must be imported before pandas/camel_tools
or the pyd segfaults on load. onnxruntime is imported first below for that
reason, even though this file uses no pandas.

Origin note: data/parser/clitic_feats.csv and the lookup in
_clitic_token_feats() are copied/adapted, with attribution, from
CAMeL-Lab/camel_parser (MIT licence, Copyright 2023 NYU Abu Dhabi),
src/parse_disambiguation/feature_extraction.py (get_clitic_feats,
build_clitic_feats_dict). That table is the only record of a clitic's own
case/state (e.g. an attached pronoun's case is not the stem's case), and
this port reads it with the stdlib csv module instead of camel_parser's
pandas lookup.
"""
from __future__ import annotations

import csv
import json
import logging
import threading
import time

import onnxruntime as ort  # must precede camel_tools (Windows DLL load-order bug, see module docstring)

import numpy as np
from tokenizers import Tokenizer

from backend.services.arabic_text import bare_letters
from backend.config import data_path, get_settings
from backend.services.syntax import decode
from backend.services.syntax.mask import book_mask
from backend.services.syntax.vowels import agrees_with_typed, past_passive_shape, typed_case

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Module state, built once by _ensure_loaded (at startup by warm(), or else by
# the first parse())
# ─────────────────────────────────────────────────────────────────────────────
_enc_sess = None
_scorer_sess = None
_bpe: Tokenizer | None = None
_cfg: dict | None = None
_rel_labels: list[str] | None = None
_clitic_table: list[dict[str, str]] | None = None
_disambiguator = None
_ar2bw = None

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
    if _disambiguator is not None:
        return "ready"
    if _load_error:
        return f"failed: {_load_error}"
    return "loading" if _load_lock.locked() else "not loaded"


def warm() -> None:
    """Load everything now, so the first sentence typed does not wait for it."""
    _ensure_loaded()


def _ensure_loaded() -> None:
    """Load the ONNX sessions, tokenizer and BERT disambiguator once, and
    keep them in the module globals above. Heavy (a ~110MB int8 encoder plus
    CAMeL's BERT disambiguator), so it runs in the background at startup
    (warm()), or on the first parse() when warming is off.

    Everything is loaded into locals and published together, last of all the
    disambiguator, so a reader that sees it set sees a whole parser.
    """
    global _enc_sess, _scorer_sess, _bpe, _cfg, _rel_labels, _clitic_table, _disambiguator, _ar2bw
    global _load_error
    if _disambiguator is not None:
        return
    with _load_lock:
        if _disambiguator is not None:
            return
        if _load_error:
            raise RuntimeError(f"CATiB parser failed to load: {_load_error}")
        try:
            loaded = _load()
        except Exception as exc:
            _load_error = f"{type(exc).__name__}: {exc}"
            raise
        _cfg, _rel_labels, _clitic_table, _bpe, _enc_sess, _scorer_sess, _ar2bw, _disambiguator = loaded


def _load() -> tuple:
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
    # which must load after onnxruntime (see module docstring).
    from camel_tools.disambig.bert import BERTUnfactoredDisambiguator
    from camel_tools.utils.charmap import CharMapper

    disambiguator = BERTUnfactoredDisambiguator.pretrained(
        "msa", top=settings.catib_readings, use_gpu=False)
    ar2bw = CharMapper.builtin_mapper("ar2bw")
    logger.info("CATiB ONNX parser ready (%s) in %.1fs", d, time.perf_counter() - started)
    return cfg, rel_labels, clitic_table, bpe, enc_sess, scorer_sess, ar2bw, disambiguator


# ─────────────────────────────────────────────────────────────────────────────
# CAMeL analysis -> clitic-split tokens (form, lemma, pos, ud, feats)
# ─────────────────────────────────────────────────────────────────────────────

# CATiB folds the ال determiner into a feature (prc0=Al_det) rather than a
# token, so only these clitic slots ever produce a separate token.
_CLITIC_SLOTS = ("prc3", "prc2", "prc1", "prc0", "enc0")
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


def _clitic_order(token: str) -> str:
    return "prc" if token.endswith("+") else "enc"


def _clitic_token_feats(token: str, order: str, stem: dict) -> dict:
    """Look up token's own asp/vox/stt/cas/pos in clitic_feats.csv, keyed by
    the clitic's surface form and by whichever prcN/enc0 slot is active on
    the stem. UD is not looked up here: the stem analysis's own 'ud' field is
    already split per subtoken by the caller, clitics included, so this only
    supplies what the CSV alone records (a clitic's own case/state/pos).
    See module docstring for where this table comes from.
    """
    from camel_tools.utils.dediac import dediac_ar

    surface = _ar2bw(dediac_ar(token.strip("+")))
    active = [f"{k}:{v}" for k, v in stem.items()
              if k.startswith(order) and v not in ("0", "na")]
    for deciding_feat in active:
        for row in _clitic_table:
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
    add_remaining_features (see module docstring), trimmed to the feature
    set this app keeps.
    """
    from camel_tools.utils.dediac import dediac_ar

    if not a.get("catib6") or "atbtok" not in a:
        # The analyzer found nothing for this word; BERT's own tag is all
        # there is, so it is reported as a single unsplit token.
        catib6 = _POS_TO_CATIB6.get(a.get("pos", ""), "NOM")
        return [{
            "form": dediac_ar(word).replace("_", "").replace("ـ", "") or word,
            "lemma": dediac_ar(a.get("lex", word)),
            "pos": catib6, "pos_camel": a.get("pos", ""), "ud": catib6,
            "asp": a.get("asp", "na"), "vox": a.get("vox", "na"),
            "stt": a.get("stt", "na"), "cas": a.get("cas", "na"),
            "token_type": "baseword",
        }]

    if "+" not in a["catib6"]:
        toks, catib6s, uds = [a["atbtok"]], [a["catib6"]], [a["ud"]]
    else:
        toks = a["atbtok"].split("_")
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
        form = dediac_ar(tok)
        form = form.replace("_", "").replace("ـ", "") or form
        if not _is_clitic(tok):
            out.append({
                "form": form, "lemma": dediac_ar(a.get("lex", tok)),
                "pos": catib6, "pos_camel": a.get("pos", ""), "ud": ud,
                "asp": a.get("asp", "na"), "vox": a.get("vox", "na"),
                "stt": a.get("stt", "na"), "cas": a.get("cas", "na"),
                # the analyser's own word-shape, e.g. 1ا2ِ3 for فاعل: how a participle is told from a noun
                "pattern": a.get("pattern", ""),
                "token_type": "baseword",
            })
        else:
            feats = _clitic_token_feats(tok, _clitic_order(tok), a)
            out.append({
                "form": form, "lemma": form,
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
    and win: the first reading, best first, that agrees with them is used. The
    analyser's guessed proper noun has no vowels to disagree with, so it never
    wins that way. When no real reading agrees the favourite is kept, since the
    naming layer still reads the vowels itself (a passive بُعْثِرَ).
    """
    if not readings:
        return {"pos": "", "lex": word}
    agreeing = [r for r in readings if "NOAN" not in r.get("atbtok", "")
                and agrees_with_typed(word, r.get("diac", ""))]
    # فُعِلَ by its vowels is a passive verb and nothing else: no noun is typed so
    # (أُكِلَ is not the noun آكِل, بُنِيَ is not بُن + ي)
    # The analyser often offers only the active verb of the same letters; the
    # naming layer then reads the passive from the vowels, as it does for بُعْثِرَ.
    verbs = [r for r in readings
             if r.get("pos") == "verb" and bare_letters(r.get("diac", "")) == bare_letters(word)]
    if past_passive_shape(word) and verbs:
        return verbs[0]
    return agreeing[0] if agreeing else readings[0]


# ─────────────────────────────────────────────────────────────────────────────
# ONNX biaffine parser: subtoken forms -> heads + rel labels
# (ports the spike's parse_onnx.py; decoding lives in decode.py)
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize_and_pack(forms: list[str]) -> tuple[np.ndarray, np.ndarray, list[tuple[int, int]]]:
    bos, pad, fix_len = _cfg["bos_index"], _cfg["pad_index"], _cfg["fix_len"]
    groups = [[bos]]
    for w in forms:
        ids = _bpe.encode(w, add_special_tokens=False).ids[:fix_len]
        groups.append(ids if ids else [bos])

    flat: list[int] = []
    spans: list[tuple[int, int]] = []
    for g in groups:
        spans.append((len(flat), len(flat) + len(g)))
        flat.extend(g)

    ids = np.full((1, len(flat)), pad, dtype=np.int64)
    mask = np.zeros((1, len(flat)), dtype=np.int64)
    ids[0, :len(flat)] = flat
    mask[0, :len(flat)] = 1
    return ids, mask, spans


def _pool_words(mixed_hidden: np.ndarray, spans: list[tuple[int, int]]) -> tuple[np.ndarray, np.ndarray]:
    _, _, hidden = mixed_hidden.shape
    out = np.zeros((1, len(spans), hidden), dtype=np.float32)
    wmask = np.zeros((1, len(spans)), dtype=bool)
    for j, (s, e) in enumerate(spans):
        out[0, j] = mixed_hidden[0, s:e].mean(axis=0)
        wmask[0, j] = True
    return out, wmask


def _decode(s_arc: np.ndarray, s_rel: np.ndarray, toks: list[dict]) -> tuple[list[int], list[str]]:
    """Heads and labels, best first among the links the book allows (mask.py)."""
    n_words = len(toks)
    L = n_words + 1
    rel_ok = book_mask(toks, _rel_labels)
    heads = decode.heads(s_arc[:L, :L])
    rels = [_rel_labels[int(np.argmax(np.where(rel_ok[i + 1, heads[i]], s_rel[i + 1, heads[i]], -np.inf)))]
            for i in range(n_words)]
    return heads, rels


def _parse_forms(toks: list[dict]) -> tuple[list[int], list[str]]:
    ids, mask, spans = _tokenize_and_pack([t["form"] for t in toks])
    (mixed,) = _enc_sess.run(None, {"input_ids": ids, "attention_mask": mask})
    word_embed, wmask = _pool_words(mixed, spans)
    s_arc, s_rel = _scorer_sess.run(
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

    _ensure_loaded()

    disambiguated = _disambiguator.disambiguate(words)
    subtokens: list[dict] = []
    for word, dw in zip(words, disambiguated):
        readings = [scored.analysis for scored in dw.analyses]
        subtokens.extend({**t, "case": typed_case(word)} for t in _split_word(word, _reading(word, readings)))

    heads, rels = _parse_forms(subtokens)

    return [
        {"id": i + 1, **tok, "head": heads[i], "rel": rels[i]}
        for i, tok in enumerate(subtokens)
    ]
