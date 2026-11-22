"""Torch-free CATiB dependency parser: whitespace-split words -> a head/rel link
for each word, over the light clitic split those links assume.

The reading picked for each word (morphology.pick, by BERT's ranking) has atbtok/catib6/ud
fields that say whether the word is one token or several (CATiB splits off
conjunctions, prepositions and pronoun suffixes, but folds the determiner ال into
a feature). The split forms go to an ONNX biaffine parser (onnxruntime and numpy
only) for head/rel. onnxruntime must be imported before camel_tools (Windows DLL
load order). data/parser/clitic_feats.csv, the only record of a clitic's own
case/state, is adapted from CAMeL-Lab/camel_parser (MIT, Copyright 2023 NYU Abu Dhabi).
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import NamedTuple

import onnxruntime as ort  # must precede camel_tools (see module docstring)

import numpy as np
from tokenizers import Tokenizer

from backend.config import data_path, get_settings
from backend.services.nahw.syntax import decode, exact_int8, splitter
from backend.services.nahw.syntax.mask import book_mask

logger = logging.getLogger(__name__)


class _Parser(NamedTuple):
    cfg: dict
    rel_labels: list[str]
    bpe: Tokenizer
    enc_sess: object
    scorer_sess: object
    disambiguator: object
    bert: str = ""  # what runs the disambiguator's BERT: "onnxruntime" or "torch" (_disambiguator)


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
    """"ready", "loading", "not loaded" or "failed", for /api/health (the why is in the log)."""
    if _parser is not None:
        return "ready"
    if _load_error:
        return "failed"
    return "loading" if _load_lock.locked() else "not loaded"


def warm() -> None:
    """Load the ONNX sessions, tokenizer and BERT disambiguator once (a ~110MB
    int8 encoder plus CAMeL's BERT, as ONNX when built), at startup so the first sentence typed does
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
            loaded = _load()
            # BERT's first run is slow (torch pulls in ~800 modules, 2.7s; onnxruntime
            # plans its graph); a practice word pays that here, so the first sentence
            # typed reads in 0.3s like every later one
            loaded.disambiguator.disambiguate(["كتب"])
            _parser = loaded
        except Exception as exc:
            _load_error = f"{type(exc).__name__}: {exc}"
            logger.warning("CATiB parser failed to load, the cards read by the MLE: %s", _load_error)
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

    bpe = Tokenizer.from_file(str(d / "tokenizer.json"))
    enc_sess = exact_int8.session(d / "encoder.onnx")  # 8-bit: the same parse on every processor
    scorer_sess = ort.InferenceSession(str(d / "scorer.onnx"), providers=["CPUExecutionProvider"])

    disambiguator, which = _disambiguator(settings.catib_readings)
    logger.info("CATiB ONNX parser ready (%s, BERT on %s) in %.1fs", d, which, time.perf_counter() - started)
    return _Parser(cfg, rel_labels, bpe, enc_sess, scorer_sess, disambiguator, which)


def _disambiguator(top: int) -> tuple[object, str]:
    """CAMeL's BERT disambiguator, ranking `top` readings a word: the ONNX copy
    (disambiguator_onnx.py) when it has been built, which needs no torch, else CAMeL's
    own. The two rank alike (scripts/nahw/check_disambig_parity.py, run in CI)."""
    from backend.services.nahw.syntax import disambiguator_onnx

    onnx_dir = data_path("catib_disambig_dir")
    if disambiguator_onnx.files_present(onnx_dir):
        return disambiguator_onnx.OnnxDisambiguator(onnx_dir, top=top), "onnxruntime"
    from camel_tools.disambig.bert import BERTUnfactoredDisambiguator

    return BERTUnfactoredDisambiguator.pretrained("msa", top=top, use_gpu=False), "torch"


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
    heads = [int(h) for h in decode.heads(s_arc[:L, :L])]  # plain ints: numpy ones break the JSON answer
    rels = [rel_labels[int(np.argmax(np.where(rel_ok[i + 1, heads[i]], s_rel[i + 1, heads[i]], -np.inf)))]
            for i in range(n_words)]
    return heads, rels


def links(toks: list[dict]) -> tuple[list[int], list[str]]:
    """The seam in front of the model: the pieces (splitter.pieces) -> each one's head (1-based, 0 = root) and rel."""
    ids, mask, spans = _tokenize_and_pack([t["form"] for t in toks])
    (mixed,) = _parser.enc_sess.run(None, {"input_ids": ids, "attention_mask": mask})
    word_embed, wmask = _pool_words(mixed, spans)
    s_arc, s_rel = _parser.scorer_sess.run(
        None, {"word_embed": word_embed.astype(np.float32), "mask": wmask})
    return _decode(s_arc[0], s_rel[0], toks)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def disambiguator():
    """The loaded BERT disambiguator, or None while it is not loaded."""
    return _parser.disambiguator if _parser else None


def bert_runtime() -> str:
    """"onnxruntime" or "torch", what the loaded disambiguator runs on; "" while it is not loaded.
    On /api/health, so a server whose ONNX build failed is seen back on torch."""
    return _parser.bert if _parser else ""


def parse(words: list[str], picks: list[dict]) -> list[dict]:
    """Dependency-parse one sentence's already-split words.

    words: the sentence split on whitespace/punctuation (not on clitics --
    that split happens inside this function).
    picks: one CAMeL reading per word (morphology.pick), none read here.

    Returns one dict per output token (a clitic may add tokens beyond
    len(words)), each with: id (1-based), form, lemma, pos (CATiB6 tag),
    pos_camel (CAMeL's own finer tag), ud, vox, asp, stt, cas, token_type,
    head (1-based, 0 = sentence root), rel (CATiB dependency label).
    """
    if not words:
        return []

    warm()

    subtokens = splitter.pieces(words, picks)
    heads, rels = links(subtokens)

    # the parser reads the pieces as it was trained on them (عند_+ني); the card and the column show them as written (+ي)
    return [
        {"id": i + 1, **splitter.shown(tok), "head": heads[i], "rel": rels[i]}
        for i, tok in enumerate(subtokens)
    ]

