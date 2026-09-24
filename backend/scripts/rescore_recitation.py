"""The same 1,950 marked recordings, kept this time in full: every piece of
every word, and where in the sound each word was said.

    python backend/scripts/rescore_recitation.py            # everything
    python backend/scripts/rescore_recitation.py --limit 40 # a quick look

Needs score_recitation_checker.py to have run, because the transcripts it wrote
are reused rather than made again. Placing a recording on its ayah is the only
thing the transcript is for here, and reading the sound a second time to write
down the same words would be two thirds of the cost for nothing.

Why a second file rather than more columns in the first
-------------------------------------------------------
downloads/results.jsonl keeps one number per word: the word's least sure piece.
That one number is a rule already applied, and applying a rule before writing
the evidence down is what made every later question need another hour of model
time. This writes the evidence: `probs` is how likely each piece of the word
was, `at` is the second of the recording its last piece lines up with. Every
rule about how sure a word is can then be tried in seconds, offline, by
sweep_sureness.py, and never needs the model again.

Resumable: each recording is appended as it is done, and a run skips what is
already there for the same model. One file per model, named after it, so two
models can be compared without either overwriting the other.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path, get_settings  # noqa: E402
from backend.services.recitation import listen  # noqa: E402
from backend.scripts.score_recitation_checker import (  # noqa: E402
    DOWNLOADS, RESULTS, recordings, stretch,
)

HERE = Path(__file__).resolve().parents[1] / "data" / "recitation_checks"


def pieces_path(model: str) -> Path:
    """One file per model, named after it, so runs of two models never mix."""
    return DOWNLOADS / f"pieces-{re.sub('[^a-z0-9]+', '-', model.lower()).strip('-')}.jsonl"


def transcripts() -> dict[str, str]:
    """What the ear wrote down for each recording, from the first run."""
    out = {}
    for line in RESULTS.open(encoding="utf-8"):
        row = json.loads(line)
        if "skipped" not in row:
            out[row["id"]] = row["heard"]
    return out


def run(ayahs: dict[str, str], limit: int | None) -> Path:
    model = get_settings().recitation_model
    out_path = pieces_path(model)
    heard_of = transcripts()
    done = set()
    if out_path.exists():
        done = {json.loads(line)["id"] for line in out_path.open(encoding="utf-8")}
    print(f"{model}: {len(done)} already done, {len(heard_of)} to do", flush=True)

    with out_path.open("a", encoding="utf-8") as out:
        for count, (rid, audio, key, _marks) in enumerate(recordings(ayahs)):
            if limit is not None and count >= limit:
                break
            if rid in done or rid not in heard_of:
                continue
            around, a, b, reach = stretch(ayahs, key, heard_of[rid])
            started = time.perf_counter()
            got = listen.scores(audio, around)[a:b]
            row = {
                "id": rid, "model": model, "ayah": key, "reach": reach,
                "probs": [[round(p, 4) for p in w["probs"]] for w in got],
                "at": [w["at"] for w in got],
                "ms": round((time.perf_counter() - started) * 1000),
            }
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            if count % 25 == 0:
                print(f"  {count + 1} {key} {row['ms']}ms", flush=True)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, help="only the first N recordings")
    args = parser.parse_args()
    ayahs = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    where = run(ayahs, args.limit)
    rows = sum(1 for _ in where.open(encoding="utf-8"))
    print(f"{rows} recordings in {where}")


if __name__ == "__main__":
    main()
