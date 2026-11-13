"""CAMeL Tools' BERT disambiguator (camel_tools.disambig.bert.BERTUnfactoredDisambiguator,
"msa") run through onnxruntime, so ranking a sentence's readings needs no torch.

CAMeL tags each word with a BERT model, then ranks the analyzer's readings of the
word by how well they agree with the tag. Only the tagger is replaced here: the
graph is the ONNX export made by backend/scripts/nahw/build_disambig_onnx.py from
CAMeL's own weights and tokenizer. Everything after the model (the analyzer, the
feature-match score, the tie-break, the sort) is CAMeL's own torch-free code,
called exactly as CAMeL 1.6 calls it. What is copied from
camel_tools/disambig/bert/unfactored.py and _bert_morph_dataset.py:

  - words are stripped of diacritics before tagging (kept as typed if that empties them)
  - an empty or blank word is skipped, which moves the following words' tags up one
    and drops the last word, as CAMeL does
  - a word the tokenizer turns into nothing, or into nothing but [UNK], is one [UNK]
  - a sentence over 510 word pieces is cut into segments at a word boundary, each
    wrapped in [CLS] ... [SEP]; up to 32 segments run together, padded to the longest
  - a word's tag is the one at its first piece
  - the analyzer reads the word as typed; its readings are scored against the tag,
    scaled by the best score, sorted, and the first `top` kept; a word it cannot
    read gets the tag itself as its one reading
  - rankings are kept in an LFU cache of 100000, keyed by the word and its tag

backend/scripts/nahw/check_disambig_parity.py runs both over the book's sentences
and the Qur'an and fails on any difference in any of the `top` readings.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

import onnxruntime as ort  # must precede camel_tools (see catib_onnx.py)

import numpy as np
from cachetools import LFUCache
from tokenizers import Tokenizer

from camel_tools.disambig.common import DisambiguatedWord, ScoredAnalysis
from camel_tools.disambig.score_function import FEATURE_SET_MAP, score_analysis_uniform
from camel_tools.morphology.analyzer import Analyzer
from camel_tools.morphology.database import MorphologyDB
from camel_tools.utils.dediac import dediac_ar

# The files build_disambig_onnx.py writes, all of which a load needs.
FILES = ("model.onnx", "tokenizer.json", "labels.json", "config.json", "mle_model.json")

# CAMeL's own numbers: BERT's input limit, segments run at once, analyses and rankings kept.
_MAX_SEQ = 512
_BATCH = 32
_ANALYZER_CACHE = 10000
_RANKING_CACHE = 100000


def files_present(model_dir: Path) -> bool:
    return all((model_dir / name).exists() for name in FILES)


class OnnxDisambiguator:
    """`disambiguate(words)` -> one DisambiguatedWord per word, each with its `top`
    ScoredAnalysis best first: what BERTUnfactoredDisambiguator.pretrained("msa", top=top)
    returns for the same words."""

    def __init__(self, model_dir: Path, top: int = 1):
        cfg = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
        if cfg["scorer"] != "uniform":
            raise ValueError(f"unsupported scorer {cfg['scorer']!r}; only 'uniform' is ported")
        self._top = max(top, 1)
        self._features = FEATURE_SET_MAP[cfg["feature"]]
        self._tie_breaker = cfg["tie_breaker"]
        self._mle = json.loads((model_dir / "mle_model.json").read_text(encoding="utf-8"))

        # One parsed feature dict per logit, built once: "pos:noun__prc2:na" -> {...}
        itos = json.loads((model_dir / "labels.json").read_text(encoding="utf-8"))["itos"]
        self._labels = [dict(feat.split(":") for feat in label.split("__")) for label in itos]

        self._tok = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self._cls, self._sep, self._unk = (self._tok.token_to_id(t) for t in ("[CLS]", "[SEP]", "[UNK]"))
        self._sess = ort.InferenceSession(str(model_dir / "model.onnx"), providers=["CPUExecutionProvider"])
        self._analyzer = Analyzer(MorphologyDB.builtin_db(cfg["db_name"], "a"),
                                  backoff=cfg["backoff"], cache_size=_ANALYZER_CACHE)
        # Requests are answered on several threads at once; a cache is not safe to change from two.
        self._ranking_cache = LFUCache(_RANKING_CACHE)
        self._cache_lock = threading.Lock()

    # ── the tagger ───────────────────────────────────────────────────────────

    def _pieces(self, word: str) -> list[int]:
        ids = self._tok.encode(word, add_special_tokens=False).ids
        return ids if ids and any(i != self._unk for i in ids) else [self._unk]

    def _segments(self, words: list[str]) -> list[tuple[list[int], list[int]]]:
        """(input ids, the position of each word's first piece) for each run of
        words that fits the model, [CLS] and [SEP] included."""
        room = _MAX_SEQ - 2
        segments, current, used = [], [], 0
        for word in words:
            if word.strip() == "":
                continue
            pieces = self._pieces(word)
            if current and used + len(pieces) > room:
                segments.append(current)
                current, used = [], 0
            current.append(pieces)
            used += len(pieces)
        if current:
            segments.append(current)
        out = []
        for seg in segments:
            ids, firsts = [self._cls], []
            for pieces in seg:
                firsts.append(len(ids))
                ids.extend(pieces)
            ids.append(self._sep)
            out.append((ids, firsts))
        return out

    def _tags(self, words: list[str]) -> list[dict]:
        """The model's feature dict for each non-blank word, in order."""
        segments = self._segments(words)
        tags: list[dict] = []
        for start in range(0, len(segments), _BATCH):
            batch = segments[start:start + _BATCH]
            width = max(len(ids) for ids, _ in batch)
            input_ids = np.zeros((len(batch), width), dtype=np.int64)  # [PAD] is 0
            mask = np.zeros_like(input_ids)
            for row, (ids, _) in enumerate(batch):
                input_ids[row, :len(ids)] = ids
                mask[row, :len(ids)] = 1
            (logits,) = self._sess.run(None, {"input_ids": input_ids, "attention_mask": mask})
            for row, (_, firsts) in enumerate(batch):
                tags.extend(self._labels[int(i)] for i in np.argmax(logits[row, firsts], axis=-1))
        return tags

    # ── the analyzer's ranking ───────────────────────────────────────────────

    def _scored_analyses(self, word: str, tag: dict) -> list[ScoredAnalysis]:
        analyses = self._analyzer.analyze(word)
        if not analyses:
            return [ScoredAnalysis(0, tag, word, -99, -99)]
        scored = [(score_analysis_uniform(a, tag, self._mle, tie_breaker=self._tie_breaker,
                                          features=self._features), a) for a in analyses]
        best = max(s for s, _ in scored) or 1
        ranked = [ScoredAnalysis(s / best, a, a["diac"], a.get("pos_lex_logprob", -99),
                                 a.get("lex_logprob", -99)) for s, a in scored]
        ranked.sort()
        return ranked

    def _disambiguate_word(self, word: str, tag: dict) -> DisambiguatedWord:
        key = (word, tuple(tag[feat] for feat in self._features))
        with self._cache_lock:
            ranked = self._ranking_cache.get(key)
        if ranked is None:
            ranked = self._scored_analyses(word, tag)
            with self._cache_lock:
                self._ranking_cache[key] = ranked
        return DisambiguatedWord(word, ranked[:self._top])

    def disambiguate(self, sentence: list[str]) -> list[DisambiguatedWord]:
        bare = [d if (d := dediac_ar(w)) else w for w in sentence]
        # lex and diac are what CAMeL copies in for a word the analyzer cannot read. Paired
        # by position, blank words included, so a blank word shifts them as it does in CAMeL.
        tags = [dict(tag, lex=b, diac=b) for b, tag in zip(bare, self._tags(bare))]
        return [self._disambiguate_word(w, tag) for w, tag in zip(sentence, tags)]
