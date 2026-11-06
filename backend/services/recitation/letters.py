"""Sound in, the letters heard out: tilawa's small Qur'an model, for placing.

Whisper writes a recitation out word by word, one guess feeding the next, and
that is most of a reading's seconds. Placing a recitation on the page only needs
the letters, so this model reads every moment of sound at once and says which
letter it is; the letters are the transcript. Its spelling carries few vowels,
which placing never looks at (place.bare_word folds them away).

Model: yazinsai/tilawa v0.2.0 (MIT), a mixed int4/int8 export of NVIDIA's
stt_ar_fastconformer_hybrid_large_pcd_v1.0 (CC-BY-4.0). Its sound preparation
is inside the model, so it takes the raw 16kHz sound sound_of already made.
Needs onnxruntime 1.23 or newer; 1.22 has no int8 ConvInteger.
"""
from __future__ import annotations

import json
import logging

import numpy as np

from backend.services.recitation import loudness
from backend.services.recitation.errors import NotInstalled
from backend.services.recitation.local_model import LocalModel

log = logging.getLogger(__name__)


def _pieces_and_blank(folder):
    meta = json.loads((folder / "export_metadata.json").read_text(encoding="utf-8"))
    vocab = json.loads((folder / "vocab.json").read_text(encoding="utf-8"))
    return [vocab[str(i)] for i in range(len(vocab))], int(meta["blank_id"])


_model = LocalModel("letters", "recitation_letters_path", "fastconformer_full_mixed.onnx", _pieces_and_blank)
installed = _model.installed


def spelled(best: np.ndarray, pieces: list[str], blank: int) -> str:
    """The letters in the model's best piece per moment: a piece held over
    several moments counts once, blanks separate, and ▁ starts a word."""
    kept = [int(p) for i, p in enumerate(best) if p != blank and (i == 0 or p != best[i - 1])]
    return " ".join("".join(pieces[p] for p in kept).replace("▁", " ").split())


def read(sound: np.ndarray) -> str:
    """What was recited, as letters, from sound already decoded by whisper.sound_of."""
    if len(sound) == 0:
        return ""
    signal = np.asarray(sound, dtype=np.float32)[None, :]
    # Under the same lock as the Whisper models (LocalModel.run): a spoken search
    # falling back to Whisper does not wait at the route's recitation turn, so
    # without it the two could run at once and each take longer than one after the other.
    (logprobs,) = _model.run("placed-by-letters",
                             {"audio_signal": signal, "length": np.array([signal.shape[1]], np.int64)},
                             s=round(signal.shape[1] / loudness.SAMPLE_RATE, 1))
    return spelled(logprobs[0].argmax(axis=-1), *_model.extra)


def warm() -> None:
    """Load it now. Never raises; a missing model is said in the log."""
    try:
        _model.load()
    except NotInstalled as exc:
        log.info("placing by letters is unavailable: %s", exc)
