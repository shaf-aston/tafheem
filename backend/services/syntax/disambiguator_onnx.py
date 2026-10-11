"""Torch-free port of CAMeL Tools' BERT disambiguator
(camel_tools.disambig.bert.BERTUnfactoredDisambiguator, "msa", top=1).

CAMeL runs a BERT tagger over the sentence to predict each word's features,
then picks the analyzer reading that agrees with them best. Here the tagger is
the ONNX export made by backend/scripts/build_disambig_onnx.py (onnxruntime,
no torch); everything after the model -- the analyzer, the feature-match score,
the tie-breaks -- is CAMeL's own torch-free code, called exactly as CAMeL calls
it. What is ported from camel_tools/disambig/bert/unfactored.py and
_bert_morph_dataset.py:

  - words are stripped of diacritics before tagging (kept if that empties them)
  - a word the tokenizer turns into nothing is skipped, which shifts the labels
    onto the following words, as CAMeL does
  - a sentence over 510 word pieces is cut into segments at a word boundary,
    each wrapped in [CLS] ... [SEP]; the tag of a word is the one at its first
    piece; the segments' tags are joined in order
  - the analyzer is asked about the word as typed, scored against the tags,
    sorted by CAMeL's ScoredAnalysis order, and the first is kept

Not ported: CAMeL's 556 MB pretrained ranking cache. It only stores results of
this same scoring, so leaving it out changes speed, not the chosen reading.
"""
from __future__ import annotations

import json
from pathlib import Path

import onnxruntime as ort  # must precede camel_tools (Windows DLL load-order bug, see catib_onnx.py)

import numpy as np
from tokenizers import Tokenizer

from camel_tools.disambig.common import ScoredAnalysis
from camel_tools.disambig.score_function import FEATURE_SET_MAP, score_analysis_uniform
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.morphology.database import MorphologyDB
from camel_tools.utils.dediac import dediac_ar

# BERT's own input limit, which CAMeL's dataset also uses (max_seq_length).
_MAX_SEQ = 512


class OnnxDisambiguator:
    """`best_analyses(words)` -> one CAMeL analysis dict per word, as
    `BERTUnfactoredDisambiguator.disambiguate(words)[i].analyses[0].analysis`."""

    def __init__(self, model_dir: Path, analyzer_cache: int):
        cfg = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
        if cfg["scorer"] != "uniform":
            raise ValueError(f"unsupported scorer {cfg['scorer']!r}; only 'uniform' is ported")
        self._features = FEATURE_SET_MAP[cfg["feature"]]
        self._tie_breaker = cfg["tie_breaker"]
        self._mle = json.loads((model_dir / "mle_model.json").read_text(encoding="utf-8"))

        # One parsed feature dict per logit, built once: "pos:noun__prc2:na" -> {...}
        itos = json.loads((model_dir / "labels.json").read_text(encoding="utf-8"))["itos"]
        self._labels = [dict(f.split(":") for f in label.split("__")) for label in itos]

        self._tok = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self._cls = self._tok.token_to_id("[CLS]")
        self._sep = self._tok.token_to_id("[SEP]")
        self._sess = ort.InferenceSession(str(model_dir / "model.onnx"), providers=["CPUExecutionProvider"])
        self._analyzer = Analyzer(MorphologyDB.builtin_db(cfg["db_name"], "a"),
                                  backoff=cfg["backoff"], cache_size=analyzer_cache)

    # ── the tagger ───────────────────────────────────────────────────────────

    def _segments(self, words: list[str]) -> list[list[list[int]]]:
        """Word-piece ids per word, grouped into runs that fit the model.
        Words with no pieces are dropped (CAMeL drops them too)."""
        room = _MAX_SEQ - 2
        segments: list[list[list[int]]] = []
        current: list[list[int]] = []
        used = 0
        for w in words:
            pieces = self._tok.encode(w, add_special_tokens=False).ids
            if not pieces:
                continue
            if used + len(pieces) > room:
                segments.append(current)
                current, used = [], 0
            current.append(pieces)
            used += len(pieces)
        if current:
            segments.append(current)
        return segments

    def _tag(self, words: list[str]) -> list[dict]:
        """The model's predicted feature dict for each (non-empty) word."""
        tags: list[dict] = []
        for seg in self._segments(words):
            flat = [self._cls]
            firsts = []
            for pieces in seg:
                firsts.append(len(flat))
                flat.extend(pieces)
            flat.append(self._sep)
            ids = np.asarray([flat], dtype=np.int64)
            (logits,) = self._sess.run(None, {"input_ids": ids, "attention_mask": np.ones_like(ids)})
            tags.extend(self._labels[int(i)] for i in np.argmax(logits[0, firsts], axis=-1))
        return tags

    # ── the analyzer's pick ──────────────────────────────────────────────────

    def _best(self, word: str, tag: dict) -> dict:
        analyses = self._analyzer.analyze(word)
        if not analyses:
            return tag  # the analyzer does not know the word: the tagger's own reading
        scored = [(score_analysis_uniform(a, tag, self._mle, tie_breaker=self._tie_breaker,
                                          features=self._features), a) for a in analyses]
        top = max(s for s, _ in scored) or 1
        ranked = [ScoredAnalysis(s / top, a, a["diac"], a.get("pos_lex_logprob", -99),
                                 a.get("lex_logprob", -99)) for s, a in scored]
        ranked.sort()
        return ranked[0].analysis

    def best_analyses(self, words: list[str]) -> list[dict]:
        bare = [w if not (d := dediac_ar(w)) else d for w in words]
        tags = self._tag(bare)
        out = []
        for w, b, tag in zip(words, bare, tags):
            tag = dict(tag, lex=b, diac=b)  # what CAMeL copies in when the analyzer is not used
            out.append(self._best(w, tag))
        return out
