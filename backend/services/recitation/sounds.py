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

The comparison is pure and shared with scripts/recitation/score_phoneme_checker.py,
which measured it against reviewers' marks.
"""
from __future__ import annotations

import difflib
import itertools
import json
import logging
import time
from functools import lru_cache

import numpy as np

from backend.config import data_path, get_settings
from backend.services.core.timing import timed
from backend.services.recitation import loudness, whisper
from backend.services.recitation.errors import NotInstalled, local_lock

log = logging.getLogger(__name__)

MODEL = "model.int8.onnx"
VOCAB = "vocab.json"
# <pad> is the CTC blank and <unk> says nothing; neither is a sound.
SILENT = (0, 1)
# Ikhfaa, idgham, iqlab, ghunnah and qalqalah symbols: out of scope, dropped from
# the expected sounds and from what was heard, so neither side is judged on them.
TAJWEED_EXCLUDE = frozenset({"m̃", "ñ", "j̃", "w̃", "ŋ", "Q"})
VOWELS = frozenset({"a", "a:", "i", "i:", "u", "u:", "aˤ", "aˤ:"})

_loaded: tuple | None = None


def collapse(ids, id2sym: dict[int, str]) -> tuple[list[str], list[int]]:
    """Greedy CTC decode: the symbols, repeats merged, silent moments and tajweed
    symbols dropped, and how many moments (frames) each one was held for, in the
    same order."""
    symbols, runs = [], []
    for sym_id, group in itertools.groupby(ids):
        if sym_id in SILENT or id2sym[sym_id] in TAJWEED_EXCLUDE:
            continue
        symbols.append(id2sym[sym_id])
        runs.append(sum(1 for _ in group))
    return symbols, runs


def flatten(ph_by_word) -> tuple[list[str], list[int]]:
    """Expected sounds, tajweed symbols dropped, with each one's word index."""
    flat, idx = [], []
    for w, word in enumerate(ph_by_word):
        for p in word:
            if p in TAJWEED_EXCLUDE:
                continue
            flat.append(p)
            idx.append(w)
    return flat, idx


def word_verdicts(opcodes, ref_flat: list[str], ref_word_idx: list[int], n_words: int):
    """Per expected word: True (every sound of that kind matched), False (one
    was substituted or dropped), or None (the word has none of that kind)."""
    bad = [False] * len(ref_flat)
    for tag, a1, a2, _b1, _b2 in opcodes:
        if tag in ("replace", "delete"):
            for i in range(a1, a2):
                bad[i] = True
    artic: list[bool | None] = [None] * n_words
    length: list[bool | None] = [None] * n_words
    for i, w in enumerate(ref_word_idx):
        ok = not bad[i]
        if ref_flat[i] in VOWELS:
            length[w] = ok if length[w] is None else (length[w] and ok)
        else:
            artic[w] = ok if artic[w] is None else (artic[w] and ok)
    return artic, length


def heard_by_word(opcodes, ref_word_idx: list[int], heard: list[str], n_words: int) -> list[list[str]]:
    """The heard sounds filed under the word they line up with. A swapped sound
    goes to the word it replaced; an extra one between two expected sounds to the
    word before it; extras before the first or after the last are outside the
    words asked about and are left out."""
    out: list[list[str]] = [[] for _ in range(n_words)]
    for tag, a1, a2, b1, b2 in opcodes:
        if tag == "equal":
            for k in range(b2 - b1):
                out[ref_word_idx[a1 + k]].append(heard[b1 + k])
        elif tag == "replace":
            for k in range(b2 - b1):
                out[ref_word_idx[a1 + min(k, a2 - a1 - 1)]].append(heard[b1 + k])
        elif tag == "insert" and 0 < a1 < len(ref_word_idx):
            out[ref_word_idx[a1 - 1]] += heard[b1:b2]
    return out


def compare(expected_per_word, heard: list[str]) -> list[dict | None]:
    """Per expected word {heard, expected, letter_ok, vowel_ok}, or None for a
    word with no expected sounds. `heard` is the decode, tajweed symbols dropped.

    letter_ok: no consonant substituted or dropped. vowel_ok: no vowel
    substituted, dropped or held the wrong length (a long one decoded short or the
    other way is a different symbol). A word with none of a kind passes it.
    """
    n = len(expected_per_word)
    ref, owner = flatten(expected_per_word)
    opcodes = difflib.SequenceMatcher(a=ref, b=heard, autojunk=False).get_opcodes()
    letter, vowel = word_verdicts(opcodes, ref, owner, n)
    said = heard_by_word(opcodes, owner, heard, n)
    expected = [[] for _ in range(n)]
    for p, w in zip(ref, owner):
        expected[w].append(p)
    return [
        {"heard": said[w], "expected": expected[w], "letter_ok": letter[w] is not False,
         "vowel_ok": vowel[w] is not False} if expected[w] else None
        for w in range(n)
    ]


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
