"""Sound in, the letters heard out: tilawa's small Qur'an model, for placing.

Whisper writes a recitation out word by word, one guess feeding the next, and
that is most of a reading's seconds. Placing a recitation on the page only needs
the letters, so this model reads every moment of sound at once and says which
letter it is; the letters are the transcript. Its spelling carries few vowels,
which placing never looks at (place.letters folds them away).

Model: yazinsai/tilawa v0.2.0 (MIT), a mixed int4/int8 export of NVIDIA's
stt_ar_fastconformer_hybrid_large_pcd_v1.0 (CC-BY-4.0). Its sound preparation
is inside the model, so it takes the raw 16kHz sound sound_of already made.
Needs onnxruntime 1.23 or newer; 1.22 has no int8 ConvInteger.
"""
from __future__ import annotations

import json
import logging
import time

import numpy as np

from backend.config import data_path, get_settings
from backend.services.recitation.listen import NotInstalled
from backend.services.timing import timed

log = logging.getLogger(__name__)

_MODEL = "fastconformer_full_mixed.onnx"
_loaded: tuple | None = None


def _engine():
    """(session, pieces, blank id), loaded on first use and kept."""
    global _loaded
    if _loaded is not None:
        return _loaded
    folder = data_path("recitation_letters_path")
    try:
        import onnxruntime as ort
        meta = json.loads((folder / "export_metadata.json").read_text(encoding="utf-8"))
        vocab = json.loads((folder / "vocab.json").read_text(encoding="utf-8"))
        started = time.perf_counter()
        options = ort.SessionOptions()
        options.intra_op_num_threads = get_settings().recitation_threads
        session = ort.InferenceSession(str(folder / _MODEL), options,
                                       providers=["CPUExecutionProvider"])
    except Exception as exc:
        raise NotInstalled(f"the letters model could not be loaded from {folder}: {exc}") from exc
    pieces = [vocab[str(i)] for i in range(len(vocab))]
    _loaded = (session, pieces, int(meta["blank_id"]))
    log.info("loaded  model=letters  threads=%d  %.0fms", options.intra_op_num_threads,
             (time.perf_counter() - started) * 1000)
    return _loaded


def installed() -> bool:
    """The model file is here. Whether it loads is found out on first use."""
    return (data_path("recitation_letters_path") / _MODEL).is_file()


def spelled(best: np.ndarray, pieces: list[str], blank: int) -> str:
    """The letters in the model's best piece per moment: a piece held over
    several moments counts once, blanks separate, and ▁ starts a word."""
    kept = [int(p) for i, p in enumerate(best) if p != blank and (i == 0 or p != best[i - 1])]
    return " ".join("".join(pieces[p] for p in kept).replace("▁", " ").split())


def read(sound: np.ndarray) -> str:
    """What was recited, as letters, from sound already decoded by listen.sound_of."""
    if len(sound) == 0:
        return ""
    session, pieces, blank = _engine()
    signal = np.asarray(sound, dtype=np.float32)[None, :]
    (logprobs,) = timed("placed-by-letters", session.run, None,
                        {"audio_signal": signal, "length": np.array([signal.shape[1]], np.int64)},
                        s=round(signal.shape[1] / 16000, 1))
    return spelled(logprobs[0].argmax(axis=-1), pieces, blank)


def warm() -> None:
    """Load it now. Never raises; a missing model is said in the log."""
    try:
        _engine()
    except NotInstalled as exc:
        log.info("placing by letters is unavailable: %s", exc)
