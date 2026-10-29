"""Sound in, the letters and vowels heard out, set against the ones the page expects.

The sureness check (checker.py) says how likely each word is; this says which
sounds were there. quran-dev/wav2vec2-ctc-quran-phoneme-run66-iqratts-mix-final
reads every moment of sound at once into one of 71 symbols (consonants, short
and long vowels, doubled letters), and the symbols that come out, set beside the
ones a word should have, show a dropped letter or a vowel held wrong. Display
only: nothing here changes a word's colour.

Run on onnxruntime, not torch (the server has none), from an int8 export that
scripts/recitation/build_sounds_ear.py makes. The sound is levelled and
normalised inside the model, so it takes the raw 16kHz sound sound_of made.
The expected sounds come from the same script, precomputed per ayah into
`recitation_sounds_reference_path`, so the server needs no phonemizer either.

The comparison is sound_compare.py, shared with the yardstick and the training judge.
"""
from __future__ import annotations

import json
import logging
import time
from functools import lru_cache

import numpy as np

from backend.config import data_path, get_settings
from backend.services.core.timing import timed
from backend.services.recitation import loudness, whisper
from backend.services.recitation.sound_compare import collapse, compare
from backend.services.recitation.errors import NotInstalled, local_lock

log = logging.getLogger(__name__)

MODEL = "model.int8.onnx"
VOCAB = "vocab.json"
_loaded: tuple | None = None


@lru_cache(maxsize=1)
def _reference() -> dict[str, list[list[str]]]:
    """Every ayah's expected sounds by word, by "surah:ayah". Empty when not built."""
    path = data_path("recitation_sounds_reference_path")
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def expected_for(key: str, count: int) -> list[list[str]] | None:
    """The expected sounds of the ayah's words, or None when the list does not
    hold `count` words (the phonemizer glues the vocative يَا to the next word,
    and the page does not): a word count that differs is not guessed at."""
    words = _reference().get(key)
    return words if words is not None and len(words) == count else None


def installed() -> bool:
    """The model file is here. Whether it loads is found out on first use."""
    return (data_path("recitation_sounds_path") / MODEL).is_file()


def _engine():
    """(session, symbols by id), loaded on first use and kept."""
    global _loaded
    if _loaded is not None:
        return _loaded
    folder = data_path("recitation_sounds_path")
    try:
        import onnxruntime as ort
        vocab = json.loads((folder / VOCAB).read_text(encoding="utf-8"))
        started = time.perf_counter()
        options = ort.SessionOptions()
        options.intra_op_num_threads = get_settings().recitation_threads
        session = ort.InferenceSession(str(folder / MODEL), options, providers=["CPUExecutionProvider"])
    except Exception as exc:
        raise NotInstalled(f"the sounds model could not be loaded from {folder}: {exc}") from exc
    _loaded = (session, {i: s for s, i in vocab.items()})
    log.info("loaded  model=sounds  threads=%d  %.0fms", options.intra_op_num_threads,
             (time.perf_counter() - started) * 1000)
    return _loaded


def listen(sound: np.ndarray) -> tuple[list[str], list[int]]:
    """The sounds heard in a recording and each one's run in frames (see collapse).
    `sound` is 16kHz mono floats, as whisper.sound_of makes."""
    session, id2sym = _engine()
    signal = np.asarray(sound, dtype=np.float32)[None, :]
    # Under the same lock as the other local models: they share the cores.
    with local_lock:
        (logits,) = timed("sounds-heard", session.run, None, {"audio": signal},
                          s=round(signal.shape[1] / loudness.SAMPLE_RATE, 1))
    return collapse(logits[0].argmax(axis=-1).tolist(), id2sym)


def hear_sounds(audio: bytes, expected_per_word: list[list[str] | None]) -> list[dict | None]:
    """Which sounds were heard against the expected ones, per word:
    {"heard": [...], "expected": [...], "letter_ok": bool, "vowel_ok": bool}.

    None for a word with no expected sounds (a None or empty entry). An empty
    list when switched off, the model is missing or fails, or the recording is
    longer than recitation_sounds_max_seconds: a check never fails for want of this.
    """
    settings = get_settings()
    if not settings.recitation_sounds or not any(expected_per_word) or not installed():
        return []
    try:
        sound = whisper.sound_of(audio)
        if len(sound) > settings.recitation_sounds_max_seconds * loudness.SAMPLE_RATE:
            return []
        heard, _ = listen(sound)
    except Exception as exc:  # display only: whatever goes wrong here, the check still answers
        log.warning("sounds unavailable: %s", exc)
        return []
    return compare([w or () for w in expected_per_word], heard)


def warm() -> None:
    """Load it now. Never raises; a missing model is said in the log."""
    if not get_settings().recitation_sounds or not installed():
        return
    try:
        _engine()
    except NotInstalled as exc:
        log.info("sounds are unavailable: %s", exc)
