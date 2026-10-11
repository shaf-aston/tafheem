"""Every word a reviewer judged, with what one ear made of it.

Joins the reviewers' marks (downloads/results.jsonl) to one model's pieces
(rescore_recitation.py). Placing is worked out again from the transcript rather
than trusted from either file, so the two always speak about the same words.
"""
from __future__ import annotations

import json
from typing import NamedTuple

from backend.services.recitation.place import reach
from backend.services.recitation.spelling import as_heard
from backend.scripts.rescore_recitation import pieces_path
from backend.scripts.score_recitation_checker import (
    NEIGHBOURS, RESULTS, marks_to_places, page_verdict, stretch,
)

SLIPS = ("vowel slips", "letter or word slips")
RIGHT = "right, in a clean recording"


class Labelled(NamedTuple):
    group: str               # what the reviewer said of the word, e.g. "vowel slips"
    probs: list[float]       # how likely each of its pieces was
    said: bool               # the page found it in the transcript
    app: bool | None         # the app checks it by sound; None when the recording does not place
    recording: str           # recording id, e.g. "ikhlas/train-0/12"
    at: int                  # the word's place in its ayah


def scored_by_app(ayahs: dict, key: str, heard: str) -> tuple[int, int] | None:
    """Which of the ayah's words the app would check by sound, as recitation.check
    does: placed on the ayah and its neighbours, run on to the end of the ayah it
    stops in. None when it does not place, and then nothing is checked by sound."""
    surah, ayah = map(int, key.split(":"))
    words, start = [], 0
    for n in range(ayah - NEIGHBOURS, ayah + NEIGHBOURS + 1):
        if n == ayah:
            start = len(words)
        words += as_heard(ayahs.get(f"{surah}:{n}", ""))
    end = start + len(as_heard(ayahs[key]))
    span = reach(words, heard.split())
    if span is None:
        return None
    first, last = span
    if start <= last - 1 < end:
        last = end
    return max(first, start) - start, max(min(last, end) - start, 0)


def labelled(ayahs: dict, model: str, heard: dict | None = None) -> list[Labelled]:
    """Every word both files agree on. `heard` swaps in another model's transcripts.
    A recording written twice to the pieces file (a resumed run) counts once."""
    reviewed = {}
    for line in RESULTS.open(encoding="utf-8"):
        row = json.loads(line)
        if "skipped" not in row:
            reviewed[row["id"]] = row
    out, seen = [], set()
    for line in pieces_path(model).open(encoding="utf-8"):
        got = json.loads(line)
        row = reviewed.get(got["id"])
        if got["id"] in seen or row is None or len(got["probs"]) != len(row["words"]):
            continue
        seen.add(got["id"])
        page = row["page"]
        if heard is not None:
            if got["id"] not in heard:
                continue
            row = {**row, "heard": heard[got["id"]]}
            page = page_verdict(row["words"], row["heard"])
        marked = marks_to_places(row["words"], row["marks"])
        clean = not row["marks"]
        first, last = stretch(ayahs, row["ayah"], row["heard"])[3]
        app = scored_by_app(ayahs, row["ayah"], row["heard"])
        for i in range(first, min(last, len(got["probs"]))):
            kind = marked.get(i)
            if kind == "tajweed":
                group = "marked for tajweed only"
            elif kind:
                group = f"{kind} slips"
            elif clean:
                group = RIGHT
            else:
                group = "unmarked, in a recording with a slip"
            out.append(Labelled(group, got["probs"][i], page[i], app and app[0] <= i < app[1], got["id"], i))
    return out
