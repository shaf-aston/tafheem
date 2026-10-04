"""Find hadith by what a question means, not the words it uses.

A small multilingual sentence model turns text into a vector of numbers; texts
that mean the same land close, in Arabic or English ("lose your temper" near
"do not get angry"). Every hadith's English is turned once, by
scripts/build_hadith_meaning.py, into hadith_meaning.db; a question is turned
at search time (~30ms) and compared with all of them.

The model runs on onnxruntime with the publisher's own int8 build, so no torch.
It is fetched once from Hugging Face and cached, like the Whisper models. No
meaning index built means search simply runs on words alone.
"""
from __future__ import annotations

import platform
import sqlite3
import threading
import time
from functools import lru_cache
from typing import Protocol

import onnxruntime as ort
import numpy as np

from backend.config import data_path, get_settings


class Encoder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray:
        """One unit-length vector per text, as rows."""


class _OnnxSentenceModel:
    """A sentence-transformers model exported to ONNX: token vectors averaged over the real tokens."""

    def __init__(self, repo: str, max_tokens: int):
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        # The publisher ships one int8 build per processor family.
        arm = platform.machine().lower() in ("aarch64", "arm64")
        weights = "onnx/model_qint8_arm64.onnx" if arm else "onnx/model_quint8_avx2.onnx"
        self._session = ort.InferenceSession(hf_hub_download(repo, weights), providers=["CPUExecutionProvider"])
        self._tokenizer = Tokenizer.from_file(hf_hub_download(repo, "tokenizer.json"))
        self._tokenizer.enable_truncation(max_tokens)
        self._tokenizer.enable_padding()

    def encode(self, texts: list[str]) -> np.ndarray:
        batch = self._tokenizer.encode_batch(texts)
        ids = np.array([b.ids for b in batch], dtype=np.int64)
        mask = np.array([b.attention_mask for b in batch], dtype=np.int64)
        tokens = self._session.run(None, {"input_ids": ids, "attention_mask": mask,
                                          "token_type_ids": np.zeros_like(ids)})[0]
        summed = (tokens * mask[..., None]).sum(axis=1) / mask.sum(axis=1, keepdims=True)
        return (summed / np.linalg.norm(summed, axis=1, keepdims=True)).astype(np.float32)


_lock = threading.Lock()
_model: Encoder | None = None
# When loading last failed: a missing download is not retried by every search.
_failed_at: float | None = None


def encoder() -> Encoder:
    global _model, _failed_at
    if _model is None:
        settings = get_settings()
        with _lock:
            if _model is None:
                if _failed_at is not None and time.monotonic() - _failed_at < settings.hadith_meaning_retry_seconds:
                    raise RuntimeError("meaning model failed to load recently; not retrying yet")
                try:
                    _model = _OnnxSentenceModel(settings.hadith_meaning_model, settings.hadith_meaning_max_tokens)
                except Exception:
                    _failed_at = time.monotonic()
                    raise
    return _model


def is_built() -> bool:
    return data_path("hadith_meaning_path").exists()


def nearest(query: str, k: int, collections: tuple[str, ...] = ()) -> list[tuple[str, int, str]]:
    """The k hadith (collection, number, part) closest in meaning to the question."""
    path = data_path("hadith_meaning_path")
    keys, vectors = _index(str(path), path.stat().st_mtime)
    if not keys:
        return []
    scores = vectors @ encoder().encode([query])[0]
    if collections:
        scores = np.where(np.isin([c for c, _, _ in keys], collections), scores, -np.inf)
    top = np.argpartition(-scores, min(k, len(keys) - 1))[:k]
    return [keys[i] for i in top[np.argsort(-scores[top])] if np.isfinite(scores[i])]


@lru_cache(maxsize=1)
def _index(path: str, _mtime: float) -> tuple[list[tuple[str, int, str]], np.ndarray]:
    """Every stored vector, read once per build of the file (the mtime is the cache key)."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT collection_id, number, part, vector FROM meaning").fetchall()
    finally:
        conn.close()
    if not rows:
        return [], np.zeros((0, 0), dtype=np.float32)
    keys = [(c, n, p) for c, n, p, _ in rows]
    vectors = np.frombuffer(b"".join(v for *_, v in rows), dtype=np.float16).reshape(len(rows), -1)
    return keys, vectors.astype(np.float32)
