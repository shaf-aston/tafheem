"""The yardstick for the similar-verse finder, scored against the benchmark.

    python -m backend.scripts.score_mutashabihat

Every change to services/mutashabihat.py (shingle size, cap, ranking, the diff) or to
its knobs in config.py is judged by this table and by nothing else. Run it before
and after; keep the change only if a number rises and none falls.

Two questions, one row each:

    recall@5, @10    of the benchmark's expert pairs, how many does candidates() find?
                     A pair counts as found when either verse lists the other.
    divergence       for each pair, the words our diff marks against the words the
                     benchmark's `changes` column names (token overlap on folded
                     words, averaged over verses). Recall is how much of what the
                     experts marked we marked; precision, how much of what we marked
                     they did.

The benchmark's own verse text is never used, only its pair list and its `changes`
words: that text is Tanzil's spelling, ours is imlaei.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services import mutashabihat  # noqa: E402

DOWNLOADS = "downloads/mutashabihat"
RECALL_AT = (5, 10)


def read(name: str) -> list[dict]:
    path = data_path("quran_imlaei_path").parent / DOWNLOADS / name
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def folded_set(words) -> set[str]:
    return {w for w in (mutashabihat.fold(word) for word in words) if w}


def overlap(ours: set[str], theirs: set[str]) -> tuple[float, float]:
    """(precision, recall) of our marked words against the experts'."""
    both = len(ours & theirs)
    return (both / len(ours) if ours else 0.0), (both / len(theirs) if theirs else 0.0)


def main() -> int:
    pairs = read("benchmark_pairs.csv")
    changes = {(r["key"], r["connection_id"]): r["changes"] for r in read("benchmark_verses.csv")}
    texts = mutashabihat.texts()

    found = {k: 0 for k in RECALL_AT}
    scored: list[tuple[float, float]] = []
    for row in pairs:
        a, b = row["key_a"], row["key_b"]
        if a not in texts or b not in texts:
            continue
        for k in RECALL_AT:
            if b in mutashabihat.candidates(a, k) or a in mutashabihat.candidates(b, k):
                found[k] += 1
        spans = dict(zip((a, b), mutashabihat.diff(texts[a].split(), texts[b].split())))
        for key in (a, b):
            expert = changes.get((key, row["connection_id"]), "")
            if not expert:
                continue
            words = texts[key].split()
            marked = folded_set(w for start, end in spans[key] for w in words[start:end])
            scored.append(overlap(marked, folded_set(re.split(r"[\s،,]+", expert))))

    total = len(pairs)
    precision = sum(p for p, _ in scored) / len(scored)
    recall = sum(r for _, r in scored) / len(scored)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    print(f"{'measure':<28}{'score':>8}   over")
    for k in RECALL_AT:
        print(f"{f'candidate recall@{k}':<28}{found[k] / total:>8.3f}   {total} pairs")
    print(f"{'divergence precision':<28}{precision:>8.3f}   {len(scored)} verses")
    print(f"{'divergence recall':<28}{recall:>8.3f}")
    print(f"{'divergence F1':<28}{f1:>8.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
