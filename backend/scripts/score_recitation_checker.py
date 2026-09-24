"""Real people reciting, marked by a reviewer: does the checker agree with them?

    python backend/scripts/score_recitation_checker.py            # everything
    python backend/scripts/score_recitation_checker.py --limit 40 # a quick look
    python backend/scripts/score_recitation_checker.py --report   # re-read results only

Needs fetch_recitation_checks.py run first. Each recording is judged two ways,
word by word, against the ayah it should be:

  page     what the app does today: the Qur'an ear writes down what it heard,
           and a word counts as said when its letters match. Vowels ignored.
  scored   the ear is handed the expected words and says how sure it is of
           each (listen.sureness); a word counts as said above a threshold.

And both are held against the reviewer:

  passed right   a word in a recording the reviewer found no mistake in.
                 Every one flagged is a reader wrongly told they slipped.
  caught         a word the reviewer marked, by kind of mistake. Tajweed is
                 reported but is not what either method listens for.

Results are appended per recording to downloads/results.jsonl, so a stopped run
picks up where it was; report.txt beside sources.json is the summary.
"""
from __future__ import annotations

import argparse
import difflib
import io
import json
import re
import sys
import wave
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402
from backend.services.recitation import listen  # noqa: E402
from backend.services.recitation.place import PLACES_IT, letters  # noqa: E402
from backend.services.recitation.spelling import as_heard  # noqa: E402

HERE = Path(__file__).resolve().parents[1] / "data" / "recitation_checks"
DOWNLOADS = HERE / "downloads"
RESULTS = DOWNLOADS / "results.jsonl"
REPORT = HERE / "report.txt"
BATCH = 16
THRESHOLDS = (0.1, 0.3, 0.5, 0.7, 0.9)
# The ear hears 30 seconds at a time; a longer clip is skipped, and counted.
LONGEST_S = 30
# Neighbouring ayahs a recording may run into. The clips are cut loosely: one
# marked 114:4 holds 114:2 to 114:4.
NEIGHBOURS = 2
# Inside the ayah itself one word places the recording, or a one-word ayah
# never places; near it, PLACES_IT words in a row are needed.
# The most checkable kind wins when a reviewer gave a word more than one.
KINDS = {"letters": "letter or word", "wording": "letter or word", "tashkeel": "vowel",
         "حركات": "vowel", "tajweed": "tajweed", "تجويد": "tajweed"}
ORDER = ("letter or word", "vowel", "tajweed")


def kind_of(labels: list[str]) -> str:
    found = {KINDS[k] for label in labels for k in KINDS if k in label.lower()}
    return next((k for k in ORDER if k in found), "tajweed")


def marks_to_places(expected: list[str], marks: dict[str, list[str]]) -> dict[int, str]:
    """Reviewer's marked words to places in the ayah. A word that appears twice is marked twice."""
    folded = [letters(w) for w in expected]
    places = {}
    for word, labels in marks.items():
        for i, f in enumerate(folded):
            if f and f == letters(word):
                places[i] = kind_of(labels)
    return places


def unplaced(row: dict) -> int:
    folded = {letters(w) for w in row["words"]}
    return sum(1 for w in row["marks"] if letters(w) not in folded)


def rows_of(part: Path):
    """One row at a time. A whole set read at once, audio and all, ran the
    machine out of memory alongside the model."""
    for batch in pq.ParquetFile(part).iter_batches(batch_size=BATCH):
        yield from batch.to_pylist()


def recordings(ayahs: dict[str, str]):
    """(id, wav bytes, ayah key, marks) for every Hafs recording of both sets."""
    for part in sorted((DOWNLOADS / "recitation-errors").glob("*.parquet")):
        for row in rows_of(part):
            if row["riwayah"] != "Hafs":
                continue
            marks = {w: v for w, v in (row["errors"] or {}).items() if v}
            yield (f"errors/{row['audio']['path']}", row["audio"]["bytes"],
                   f"{int(row['surah'])}:{int(row['ayah'])}", marks)
    for part in sorted((DOWNLOADS / "ikhlas").glob("*.parquet")):
        for n, row in enumerate(rows_of(part)):
            marks = defaultdict(list)
            if row["label"] == 0:
                words = [w.strip() for w in re.split("[,،]", row["error_location"] or "") if w.strip()]
                kinds = [k.strip() for k in re.split("[,،]", row["error_type"] or "") if k.strip()]
                for i, w in enumerate(words):
                    # Paired by position when the reviewer listed as many kinds
                    # as words; otherwise every word gets all the kinds given.
                    marks[w] += [kinds[i]] if len(kinds) == len(words) else kinds
            marks = dict(marks)
            yield (f"ikhlas/{part.stem}/{n}", row["audio"]["bytes"],
                   f"112:{row['verse_number']}", marks)


def seconds(audio: bytes) -> float:
    """Both sets are WAV. Anything else raises, so a long clip is never let through as zero."""
    with wave.open(io.BytesIO(audio)) as w:
        return w.getnframes() / w.getframerate()


def page_verdict(expected: list[str], heard: str) -> list[bool]:
    """Said or not, per expected word, lined up on letters as the page does."""
    want, got = [letters(w) for w in expected], [letters(w) for w in heard.split()]
    said = [False] * len(expected)
    for block in difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_matching_blocks():
        for i in range(block.a, block.a + block.size):
            said[i] = True
    return said


def stretch(ayahs: dict[str, str], key: str, heard: str) -> tuple[list[str], int, int, list[int]]:
    """The words around this ayah that the recording holds, where the ayah sits in
    them, and which of the ayah's words the recording reaches (first, last + 1).

    The transcript only places the recording; every word in the stretch is then
    checked by sureness, so a misheard word inside it is still judged on sound.
    The whole ayah is always inside, so a word the reciter left out is checked
    and found missing rather than cut away.
    """
    surah, ayah = map(int, key.split(":"))
    words, start = [], 0
    for n in range(ayah - NEIGHBOURS, ayah + NEIGHBOURS + 1):
        if f"{surah}:{n}" not in ayahs:
            continue
        if n == ayah:
            start = len(words)
        words += as_heard(ayahs[f"{surah}:{n}"])
    end = start + len(as_heard(ayahs[key]))
    want, got = [letters(w) for w in words], [letters(w) for w in heard.split()]
    blocks = [b for b in difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_matching_blocks()
              if b.size >= PLACES_IT or (b.size and start <= b.a < end)]
    first = min([start] + [b.a for b in blocks])
    last = max([end] + [b.a + b.size for b in blocks])
    # The clips split long ayahs, so part of an ayah can be in no recording at
    # all. Only words between the first and last placed ones are judged.
    # Heard words left over past the outer placed ones are misheard words the
    # clip does hold, so the reach stretches by as many; left out, a misheard
    # last word would vanish from the count and flatter the page.
    if blocks:
        head, tail = blocks[0], blocks[-1]
        reach = [max(head.a - head.b, start) - start,
                 min(tail.a + tail.size + len(got) - tail.b - tail.size, end) - start]
    else:
        # Nothing heard lines up, but the clip is labelled as this ayah: judge
        # all of it. Leaving it out dropped exactly the recordings the ear got
        # most wrong.
        reach = [0, end - start]
    return words[first:last], start - first, end - first, reach


def judge(ayahs: dict[str, str], limit: int | None) -> None:
    done = set()
    if RESULTS.exists():
        done = {json.loads(line)["id"] for line in RESULTS.open(encoding="utf-8")}
    with RESULTS.open("a", encoding="utf-8") as out:
        for count, (rid, audio, key, marks) in enumerate(recordings(ayahs)):
            if limit is not None and count >= limit:
                break
            if rid in done:
                continue
            expected = as_heard(ayahs[key])
            row = {"id": rid, "ayah": key, "words": expected, "marks": marks}
            if seconds(audio) > LONGEST_S:
                row["skipped"] = "longer than the ear hears"
            else:
                heard = listen.transcribe(audio, language="ar")
                around, a, b, reach = stretch(ayahs, key, heard)
                sure = listen.sureness(audio, around)[a:b]
                row |= {"heard": heard, "page": page_verdict(expected, heard),
                        "sure": [round(p, 3) for p in sure], "stretch": len(around), "reach": reach}
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            print(f"  {count + 1} {key} {'skipped' if 'skipped' in row else ''}", flush=True)


def report(ayahs: dict[str, str]) -> str:
    rows = [json.loads(line) for line in RESULTS.open(encoding="utf-8")]
    judged = [r for r in rows if "skipped" not in r]
    for r in judged:
        # Placing is worked out again from the transcript, so a change to it
        # needs no second pass of the model. The stretch the model scored is
        # unchanged by it: the whole ayah was always inside.
        r["reach"] = stretch(ayahs, r["ayah"], r["heard"])[3]
    # tally[group] = [words, page said, scored said at each threshold...]
    tally = defaultdict(lambda: [0, 0] + [0] * len(THRESHOLDS))
    for r in judged:
        marked = marks_to_places(r["words"], r["marks"])
        clean = not r["marks"]
        first, last = r["reach"]
        for i in range(first, last):
            edge = i in (first, last - 1)
            group = (f"caught, {marked[i]}" if i in marked
                     else f"passed right, {'at a clip edge' if edge else 'inside the clip'}" if clean
                     else "unmarked, in a recording with a mistake")
            t = tally[group]
            t[0] += 1
            t[1] += r["page"][i]
            for j, cut in enumerate(THRESHOLDS):
                t[2 + j] += r["sure"][i] >= cut

    lines = [f"{len(judged)} recordings judged, {len(rows) - len(judged)} skipped as longer than the ear hears.",
             f"{sum(unplaced(r) for r in judged)} reviewer marks named a word not in the ayah and were left out.",
             "",
             "Share of words each method counts as SAID. For 'passed right' higher is better;",
             "for 'caught' lower is better, since a caught mistake is a word not counted as said.",
             "",
             f"{'':42}{'words':>7}{'page':>7}" + "".join(f"{'>=' + str(c):>7}" for c in THRESHOLDS)]
    for group in sorted(tally, key=lambda g: (not g.startswith("passed"), g)):
        t = tally[group]
        lines.append(f"{group:42}{t[0]:>7}{t[1] / t[0]:>7.0%}"
                     + "".join(f"{x / t[0]:>7.0%}" for x in t[2:]))
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, help="judge only the first N recordings")
    parser.add_argument("--report", action="store_true", help="summarise results already judged")
    args = parser.parse_args()
    ayahs = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    if not args.report:
        judge(ayahs, args.limit)
    text = report(ayahs)
    REPORT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
