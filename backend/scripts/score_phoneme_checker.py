"""Research spike: can a free phoneme model judge articulation and vowel length?

    python backend/scripts/score_phoneme_checker.py --smoke        # 5 clips, proves decode lines up with the reference
    python backend/scripts/score_phoneme_checker.py --limit 40     # a quick look
    python backend/scripts/score_phoneme_checker.py                # everything, resumable
    python backend/scripts/score_phoneme_checker.py --report       # re-read results only

Needs fetch_recitation_checks.py run first (same downloads as
score_recitation_checker.py) and `pip install quranic-phonemizer`. Uses the
system Python (torch 2.12 cpu, transformers 4.43); the project venv has the
same versions if that is preferred instead.

Two things are judged per expected word, from phonemes alone, against
quran-dev/wav2vec2-ctc-quran-phoneme-run66-iqratts-mix-final-20260909's
greedy CTC decode:

  articulation   a consonant the model decoded wrong (substituted or dropped).
  length         a long vowel decoded as short or a short one decoded as long
                 (madd). A vowel quality change counts here too, for lack of a
                 finer reviewer label.

Ikhfaa, idgham, iqlab, ghunnah and qalqalah are out of scope by instruction:
their symbols (the nasalised m̃ ñ j̃ w̃ ŋ, and qalqalah's Q, which the
reference phonemizer emits but this model's vocab has no token for at all) are
stripped from both the reference and the decode before anything is compared.

Reference phonemes come from Hetchy/Quranic-Phonemizer (MIT), word by word.
Checked over the 38 surahs this dataset actually uses: every symbol it wrote
is one of this model's 71 vocab entries, unmapped, including the ':' for a
long vowel; word counts also usually match the imlaei text used for reviewer
marks (score_recitation_checker.py's `as_heard`), except when imlaei splits
the vocative "يَا" as its own word and the phonemizer glues it to what
follows (6 of 571 ayahs checked) -- those rows are skipped rather than guessed.

Held against the reviewer, the same buckets score_recitation_checker.py uses:
"letters"/"wording" marks are articulation mistakes, "tashkeel"/"حركات"
marks are length mistakes. "tajweed"/"تجويد" marks are excluded from
both: of 831 ikhlas rows carrying only a تجويد label, 823 (99%) had an
explanation naming قلقلة (qalqala), which this checker already ignores, so
the whole bucket is left out rather than scored against the wrong thing --
same as the existing checker leaves tajweed out of "page"/"scored".

Vowel length is also tried by duration: how many 20ms frames the CTC decode
held a vowel for, on the words it decoded correctly. Reported as a spike
fraction (how often that is just one frame) because CTC decodes are known to
spike rather than hold a symbol for its true length; the report says plainly
whether the duration signal held up.

Results are appended per recording to phoneme_results.jsonl, so a stopped run
picks up where it was; phoneme_report.txt is the summary.
"""
from __future__ import annotations

import argparse
import audioop
import difflib
import io
import itertools
import json
import statistics
import sys
import time
import wave
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402
from backend.scripts.score_recitation_checker import (  # noqa: E402
    marks_to_places, recordings, seconds, unplaced,
)
from backend.services.recitation.spelling import as_heard  # noqa: E402

HERE = Path(__file__).resolve().parents[1] / "data" / "recitation_checks"
RESULTS = HERE / "phoneme_results.jsonl"
REPORT = HERE / "phoneme_report.txt"

MODEL_ID = "quran-dev/wav2vec2-ctc-quran-phoneme-run66-iqratts-mix-final-20260909"
SAMPLE_RATE = 16_000
# Wav2vec2's usual conv stride at 16kHz; stated directly in the task rather than
# re-derived from the config, since the two agree.
FRAME_MS = 20
# The ear hears 30 seconds at a time in the sibling script; kept the same here
# so both checkers skip the same recordings for the same reason.
LONGEST_S = 30
# One core for the model, so it shares the machine with whatever else is
# running rather than grabbing every core on a box with little RAM to spare.
TORCH_THREADS = 2

# Ikhfaa, idgham, iqlab, ghunnah, qalqalah symbols (see module docstring).
# "Q" never appears in a decode (not in this model's vocab); still stripped
# from the reference so it is never compared against.
TAJWEED_EXCLUDE = frozenset({"m̃", "ñ", "j̃", "w̃", "ŋ", "Q"})
VOWELS = frozenset({"a", "a:", "i", "i:", "u", "u:", "aˤ", "aˤ:"})
# The dataset's clips are cut loosely around an ayah (score_recitation_checker.py
# notes the same thing: "the clips split long ayahs"). A clip holding only part
# of the ayah looks, to a whole-ayah comparison, like the reciter dropped every
# word past the cut -- a decode artefact, not a mispronunciation. Seen directly
# in this data: two same-ayah clips that together cover it, one scoring 0.545
# match and the other 0.436, against 0.88-1.00 on clips that hold the whole
# ayah. A floor well below the intact range and well above the observed
# split-clip range excludes those without guessing which words they dropped.
MATCH_RATE_FLOOR = 0.7


def _vocab() -> dict[str, int]:
    """id2sym isn't a tokenizer file (this is CTC over raw phonemes, not
    text), so it is read straight from vocab.json rather than loaded as a
    text processor."""
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(MODEL_ID, "vocab.json")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_model():
    torch.set_num_threads(TORCH_THREADS)
    fe = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_ID, low_cpu_mem_usage=True)
    model.eval()
    id2sym = {i: s for s, i in _vocab().items()}
    return model, fe, id2sym


def wav_floats(audio: bytes) -> np.ndarray:
    """16kHz mono float32 in [-1, 1]. The recitation-errors clips already are;
    the ikhlas ones mostly are not (44.1k/48k, mono or stereo, measured over
    all 1506 rows), so this always mixes down and resamples rather than
    trusting the header."""
    with wave.open(io.BytesIO(audio)) as w:
        channels, rate, width = w.getnchannels(), w.getframerate(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width != 2:
        raise ValueError(f"expected 16-bit PCM, got {width * 8}-bit")
    if channels > 1:
        raw = audioop.tomono(raw, width, 0.5, 0.5)
    if rate != SAMPLE_RATE:
        raw, _ = audioop.ratecv(raw, width, 1, rate, SAMPLE_RATE, None)
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def decode(model, fe, id2sym: dict[int, str], audio: bytes) -> tuple[list[str], list[int]]:
    """Greedy CTC decode: collapsed symbols (blank/unk dropped) and each one's
    run length in frames, in the same order. Blank is id 0 (<pad>), this
    checkpoint's CTC convention (config.pad_token_id == 0)."""
    inputs = fe(wav_floats(audio), sampling_rate=SAMPLE_RATE, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits[0]
    ids = logits.argmax(-1).tolist()
    symbols, runs = [], []
    for sym_id, group in itertools.groupby(ids):
        n = sum(1 for _ in group)
        if sym_id in (0, 1):  # <pad> (blank), <unk>
            continue
        symbols.append(id2sym[sym_id])
        runs.append(n)
    return symbols, runs


def flatten(ph_by_word: tuple[tuple[str, ...], ...]) -> tuple[list[str], list[int]]:
    """Reference phonemes, tajweed symbols dropped, with each one's word index."""
    flat, idx = [], []
    for w, word in enumerate(ph_by_word):
        for p in word:
            if p in TAJWEED_EXCLUDE:
                continue
            flat.append(p)
            idx.append(w)
    return flat, idx


def word_verdicts(opcodes, ref_flat: list[str], ref_word_idx: list[int], n_words: int):
    """Per expected word: True (every phoneme of that kind matched), False (one
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


def vowel_durations(opcodes, ref_flat: list[str], pred_runs: list[int]) -> tuple[list[float], list[float]]:
    """ms held for each correctly-decoded vowel, split short vs long. Only
    'equal' opcodes are used: duration only means something on a vowel the
    model actually got right."""
    short_ms: list[float] = []
    long_ms: list[float] = []
    for tag, a1, a2, b1, _b2 in opcodes:
        if tag != "equal":
            continue
        for offset in range(a2 - a1):
            sym = ref_flat[a1 + offset]
            if sym not in VOWELS:
                continue
            ms = pred_runs[b1 + offset] * FRAME_MS
            (long_ms if sym.endswith(":") else short_ms).append(ms)
    return short_ms, long_ms


def smoke_line(row: dict) -> str:
    ok_artic = sum(1 for v in row["artic"] if v)
    n_artic = sum(1 for v in row["artic"] if v is not None)
    ok_len = sum(1 for v in row["length"] if v)
    n_len = sum(1 for v in row["length"] if v is not None)
    match = f"{row['match_rate']:.0%}" if row["match_rate"] is not None else "n/a"
    return (f"[{row['id']}] {row['ayah']}  {row['elapsed_s']}s\n"
            f"  ref : {' '.join(row['ref_flat'])}\n"
            f"  pred: {' '.join(row['pred_flat'])}\n"
            f"  phoneme match {match}  articulation {ok_artic}/{n_artic}  length {ok_len}/{n_len}")


def judge_one(hafs, model, fe, id2sym, key: str, expected: list[str], audio: bytes) -> dict:
    """One recording's worth of decode + score. Returns fields to merge into
    the result row; a word-count mismatch is skipped rather than guessed."""
    ph_by_word = hafs.analyse(key).phonemes(by="word")
    if len(ph_by_word) != len(expected):
        return {"skipped": "word count mismatch between imlaei and the reference phonemizer"}
    t0 = time.time()
    pred_flat, pred_runs = decode(model, fe, id2sym, audio)
    elapsed = time.time() - t0
    ref_flat, ref_word_idx = flatten(ph_by_word)
    opcodes = difflib.SequenceMatcher(a=ref_flat, b=pred_flat, autojunk=False).get_opcodes()
    artic, length = word_verdicts(opcodes, ref_flat, ref_word_idx, len(expected))
    short_ms, long_ms = vowel_durations(opcodes, ref_flat, pred_runs)
    matched = sum(a2 - a1 for tag, a1, a2, _b1, _b2 in opcodes if tag == "equal")
    return {
        "artic": artic, "length": length,
        "ref_flat": ref_flat, "pred_flat": pred_flat,
        "match_rate": round(matched / len(ref_flat), 3) if ref_flat else None,
        "short_ms": short_ms, "long_ms": long_ms,
        "elapsed_s": round(elapsed, 2),
    }


def judge(ayahs: dict[str, str], limit: int | None, smoke: int) -> None:
    from quranic_phonemizer import Phonemizer
    hafs = Phonemizer()
    model, fe, id2sym = load_model()

    done: set[str] = set()
    if RESULTS.exists() and not smoke:
        done = {json.loads(line)["id"] for line in RESULTS.open(encoding="utf-8")}

    out = None if smoke else RESULTS.open("a", encoding="utf-8")
    try:
        count = 0
        for rid, audio, key, marks in recordings(ayahs):
            if smoke and count >= smoke:
                break
            if not smoke:
                if limit is not None and count >= limit:
                    break
                if rid in done:
                    continue
            count += 1
            expected = as_heard(ayahs[key])
            row = {"id": rid, "ayah": key, "words": expected, "marks": marks}
            if seconds(audio) > LONGEST_S:
                row["skipped"] = "longer than the ear hears"
            else:
                try:
                    row |= judge_one(hafs, model, fe, id2sym, key, expected, audio)
                except Exception as exc:  # one bad clip must not lose a multi-hour run
                    row["skipped"] = f"error: {type(exc).__name__}: {exc}"
            if smoke:
                print(smoke_line(row) if "skipped" not in row else f"[{rid}] {key} skipped: {row['skipped']}")
            else:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out.flush()
                print(f"  {count} {key} {row.get('skipped', '')}", flush=True)
    finally:
        if out:
            out.close()


def report(ayahs: dict[str, str]) -> str:
    rows = [json.loads(line) for line in RESULTS.open(encoding="utf-8")]
    decoded = [r for r in rows if "skipped" not in r]
    partial = [r for r in decoded if r["match_rate"] is not None and r["match_rate"] < MATCH_RATE_FLOOR]
    judged = [r for r in decoded if r not in partial]
    skip_reasons: dict[str, int] = defaultdict(int)
    for r in rows:
        if "skipped" in r:
            skip_reasons[r["skipped"]] += 1

    artic_tally = defaultdict(lambda: {"n": 0, "flagged": 0})
    length_tally = defaultdict(lambda: {"n": 0, "flagged": 0})
    tajweed_marks = 0
    for r in judged:
        marked = marks_to_places(r["words"], r["marks"])
        clean = not r["marks"]
        for i in range(len(r["words"])):
            kind = marked.get(i)
            if kind == "tajweed":
                tajweed_marks += 1
                continue
            artic_group = ("caught, letter or word" if kind == "letter or word"
                            else "passed right" if clean
                            else "unmarked, in a recording with a mistake" if kind is None
                            else None)
            if artic_group:
                v = r["artic"][i]
                if v is not None:
                    t = artic_tally[artic_group]
                    t["n"] += 1
                    t["flagged"] += (not v)
            length_group = ("caught, vowel" if kind == "vowel"
                             else "passed right" if clean
                             else "unmarked, in a recording with a mistake" if kind is None
                             else None)
            if length_group:
                v = r["length"][i]
                if v is not None:
                    t = length_tally[length_group]
                    t["n"] += 1
                    t["flagged"] += (not v)

    def fmt(tally: dict) -> list[str]:
        lines = [f"{'':38}{'words':>7}{'flagged':>9}"]
        for group in sorted(tally, key=lambda g: (not g.startswith("passed"), g)):
            t = tally[group]
            share = f"{t['flagged'] / t['n']:.0%}" if t["n"] else "n/a"
            lines.append(f"{group:38}{t['n']:>7}{share:>9}")
        return lines

    # Runtime and the duration experiment aren't about word-level correctness,
    # so they use every decode attempted, partial-coverage clips included.
    times = [r["elapsed_s"] for r in decoded if r.get("elapsed_s") is not None]
    all_short = [ms for r in decoded for ms in r.get("short_ms", [])]
    all_long = [ms for r in decoded for ms in r.get("long_ms", [])]
    n_vowels = len(all_short) + len(all_long)
    spikes = sum(1 for ms in all_short + all_long if ms == FRAME_MS)
    per_clip_directional = [
        (statistics.mean(r["long_ms"]), statistics.mean(r["short_ms"]))
        for r in decoded if r.get("short_ms") and r.get("long_ms")
    ]
    agree = sum(1 for lo, sh in per_clip_directional if lo > sh)

    lines = [
        f"{len(rows)} recordings attempted, {len(decoded)} decoded, {len(rows) - len(decoded)} skipped:",
        *(f"  {n}  {reason}" for reason, n in sorted(skip_reasons.items())),
        f"{len(partial)} decoded clips matched under {MATCH_RATE_FLOOR:.0%} of the ayah's phonemes -- likely "
        f"holding only part of it (see MATCH_RATE_FLOOR) -- and are left out of the two tables below, which "
        f"score the remaining {len(judged)}.",
        f"{tajweed_marks} reviewer marks were tajweed-labelled and excluded from both tables below.",
        f"{sum(unplaced(r) for r in judged)} reviewer marks named a word not in the ayah and were left out.",
        "",
        "ARTICULATION -- consonant substituted or dropped. 'passed right' should be",
        "low (false flags on clean words); 'caught, letter or word' should be high.",
        *fmt(artic_tally),
        "",
        "LENGTH -- vowel substituted, dropped, or the wrong length. 'passed right'",
        "should be low; 'caught, vowel' should be high.",
        *fmt(length_tally),
        "",
        (f"Runtime: {len(times)} clips timed, mean {statistics.mean(times):.1f}s, "
         f"median {statistics.median(times):.1f}s per clip." if times else "Runtime: no clips timed."),
        "",
        (f"Duration (CTC frame span): {n_vowels} correctly-decoded vowels measured, "
         f"{spikes / n_vowels:.0%} were exactly one {FRAME_MS}ms frame."
         if n_vowels else "Duration: no correctly-decoded vowels to measure."),
    ]
    if all_short and all_long:
        lines.append(f"Pooled mean: long vowels {statistics.mean(all_long):.0f}ms vs "
                      f"short vowels {statistics.mean(all_short):.0f}ms.")
    if per_clip_directional:
        lines.append(f"Per clip, long held longer than short in {agree}/{len(per_clip_directional)} clips "
                      "with both to compare.")
        lines.append("A spike fraction near 1 means most of that gap is noise, not a usable length signal; "
                      "read the pooled means and per-clip agreement alongside it, not instead of it.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, help="judge only the first N new recordings")
    parser.add_argument("--smoke", type=int, nargs="?", const=5, default=0,
                         help="print N clips' decode vs reference instead of writing results (default 5)")
    parser.add_argument("--report", action="store_true", help="summarise results already judged")
    args = parser.parse_args()
    ayahs = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    if args.smoke:
        judge(ayahs, None, args.smoke)
        return
    if not args.report:
        judge(ayahs, args.limit, 0)
    text = report(ayahs)
    REPORT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
