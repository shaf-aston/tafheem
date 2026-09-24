"""Which model should write down a recitation, now that all it does is place it.

    python backend/scripts/time_placing.py --clips 40

Since the transcript stopped deciding whether a word is wrong, the only thing it
still has to do is say which part of the page a recording sits on: place.reach
needs a couple of page words in a row and nothing more. A smaller model may well
manage that, and on this machine the transcript is three quarters of the wait,
so it is worth knowing rather than assuming.

Judged, per model, on the recordings score_recitation_checker.py already has
transcripts for:

    ms            how long one recording takes to write down
    placed        how often place.reach found the recording on its ayah at all
    whole ayah    how often it found the whole ayah, which is what was recited
    words judged  what share of the recited words fall inside the stretch, so
                  are judged at all; the rest the reciter said and nobody marks

`--only hosted` asks Groq, `--every 5` takes every fifth recording, and
`--only letters` tries tilawa's model (services/recitation/letters.py) instead,
and `--save FILE` keeps each transcript for sweep_sureness.py --heard. Big runs
go in chunks with --skip, because a long run has been killed for memory.

Word timing is measured too, on and off. It costs about a second a reading and
buys a floor under each word's sureness, which mattered when the transcript
could accuse somebody and matters much less now.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psutil  # noqa: E402

import backend.config as config  # noqa: E402
from backend.config import data_path  # noqa: E402
from backend.services.recitation import hosted, letters, listen  # noqa: E402
from backend.services.recitation.place import reach  # noqa: E402
from backend.services.recitation.spelling import as_heard  # noqa: E402
from backend.scripts.score_recitation_checker import RESULTS, recordings  # noqa: E402

TRIED = ("OdyAsh/faster-whisper-base-ar-quran", "Systran/faster-whisper-tiny",
         "Systran/faster-whisper-base")


# Groq allows 20 requests a minute.
HOSTED_GAP_S = 3.1


def sample(ayahs: dict, how_many: int, skip: int = 0, every: int = 1):
    """(id, audio, expected words) each, after the first `skip`."""
    was = {}
    for line in RESULTS.open(encoding="utf-8"):
        row = json.loads(line)
        if "skipped" not in row:
            was[row["id"]] = row["heard"]
    out, seen = [], 0
    for rid, audio, key, _marks in recordings(ayahs):
        if rid not in was:
            continue
        seen += 1
        if seen > skip and (seen - 1) % every == 0:
            out.append((rid, audio, as_heard(ayahs[key])))
        if len(out) >= how_many:
            break
    return out


def run(clips, model: str, timing: bool, save=None) -> str:
    os.environ["RECITATION_MODEL"] = model
    os.environ["RECITATION_WORD_MIN"] = "0.94" if timing else "0"
    config.get_settings.cache_clear()
    listen._models.clear()
    listen._last = None
    if model == "hosted":
        write = lambda audio: hosted.transcribe(audio, "ar", "")  # noqa: E731
    elif model == "letters":
        write = lambda audio: letters.read(listen.sound_of(audio))  # noqa: E731
    else:
        write = lambda audio: listen.transcribe(audio, language="ar")  # noqa: E731
    if model != "hosted":
        write(clips[0][1])  # loaded, not timed
    took = placed = whole = covered = 0.0
    for rid, audio, want in clips:
        if model == "hosted":
            time.sleep(HOSTED_GAP_S)
        started = time.perf_counter()
        heard = write(audio)
        took += time.perf_counter() - started
        if save:
            save.write(json.dumps({"id": rid, "heard": heard}, ensure_ascii=False) + "\n")
        here = reach(want, heard.split())
        placed += here is not None
        # Each of these recordings is one whole ayah, so the true stretch is
        # the whole of it. A word left outside the stretch is never judged, so
        # the reciter said it and the page says nothing: that is the cost of
        # placing badly, and it is what "covered" counts.
        whole += here == (0, len(want))
        covered += 0.0 if here is None else (here[1] - here[0]) / len(want)
    n = len(clips)
    return (f"{model:40} timing {'on ' if timing else 'off'}  {took / n * 1000:6.0f}ms"
            f"  placed {placed / n:5.0%}  whole ayah {whole / n:5.0%}"
            f"  words judged {covered / n:5.0%}"
            f"  peak memory {psutil.Process().memory_info().peak_wset / 2**20:.0f}MB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--clips", type=int, default=40, help="how many recordings to try")
    # One model per run, because three of them in one process filled this
    # machine's memory and the run was killed before it printed a single line.
    parser.add_argument("--only", help="just this model, so the memory goes back when it exits")
    parser.add_argument("--skip", type=int, default=0, help="start after this many recordings")
    parser.add_argument("--save", type=Path, help="append each transcript here, as JSON lines")
    parser.add_argument("--every", type=int, default=1, help="take every Nth recording")
    args = parser.parse_args()
    ayahs = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    clips = sample(ayahs, args.clips, args.skip, args.every)
    print(f"{len(clips)} recordings from {args.skip}", flush=True)
    save = args.save.open("a", encoding="utf-8") if args.save else None
    for model in ([args.only] if args.only else TRIED):
        for timing in ((False,) if model in ("letters", "hosted") or save else (True, False)):
            print(run(clips, model, timing, save), flush=True)


if __name__ == "__main__":
    main()
