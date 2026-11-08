"""IqraEval's slips, graded the way the app checks: 1,330 clips by 15 speakers of
137 Qur'an phrases, 955 with one planted letter or vowel slip, each labelled
with the sounds meant (phoneme_ref) and the sounds said (phoneme_mis).

Fetch once (gated: accept the terms on Hugging Face first, then log in with `hf auth login`):

    hf download IqraEval/Iqra_Extra_IS26 --repo-type dataset --local-dir backend/data/recitation_checks/downloads/iqra

Never train on it: it is the only large set of slips no ear has heard.

A slip is put on a word by where it falls in the sounds, as a share of the
phrase's letters. That share is approximate at word edges, so only the slipped
word of a slip clip is graded, and right words come only from clean clips.
A dropped last vowel is how a reciter stops, never a slip, so such a clip is clean.
Scoring a model the first time takes ~8 minutes and is kept, one file per model.
"""
from __future__ import annotations

import bisect
import difflib
import itertools
import json

import pyarrow.parquet as pq

from backend.scripts.recitation.ear_bench.measures import Word
from backend.scripts.recitation.paths import DOWNLOADS
from backend.scripts.recitation.rescore_recitation import pieces_path
from backend.services.recitation import checker
from backend.services.recitation.spelling import LETTERS, as_heard

FOLDER = DOWNLOADS / "iqra"


def slipped_word(row: dict, words: list[str]) -> int | None:
    """Which of `words` holds the clip's slip; None for a clean clip."""
    meant, said = row["phoneme_ref"].split(), row["phoneme_mis"].split()
    changed = [o for o in difflib.SequenceMatcher(None, meant, said, autojunk=False).get_opcodes()
               if o[0] != "equal" and not (o[0] == "delete" and o[1] >= len(meant) - 2)]
    if not changed:
        return None
    ends = list(itertools.accumulate(sum(c in LETTERS for c in w) for w in words))
    return bisect.bisect_right([e / ends[-1] for e in ends], changed[0][1] / len(meant))


def clips() -> list[dict]:
    found = sorted(FOLDER.glob("**/*.parquet"))
    if not found:
        raise SystemExit(f"IqraEval is not downloaded: see {__file__} for the one command")
    return [row for f in found for row in pq.read_table(f).to_pylist()]


def graded_words(model: str, rule: str) -> list[Word]:
    """Slipped words and right words for `model`, scoring any clip it has not heard yet."""
    path = pieces_path(model).with_name("iqra-" + pieces_path(model).name)
    done = {}
    if path.exists():
        done = {r["id"]: r["probs"] for r in map(json.loads, path.open(encoding="utf-8"))}
    out = []
    with path.open("a", encoding="utf-8") as kept:
        for row in clips():
            words = as_heard(row["sentence"].replace("@", ""))
            if row["id"] not in done:
                done[row["id"]] = [w["probs"] for w in checker.scores(row["audio"]["bytes"], words, model)]
                kept.write(json.dumps({"id": row["id"], "probs": done[row["id"]]}) + "\n")
            sure = [checker.aggregate(p, rule) for p in done[row["id"]]]
            k = slipped_word(row, words)
            out += ([Word(row["id"], i, s, False) for i, s in enumerate(sure)] if k is None
                    else [Word(row["id"], k, sure[k], True)])
    return out
