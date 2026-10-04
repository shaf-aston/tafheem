"""Score hadith search against the yardstick of real searches.

    python backend/scripts/score_hadith_search.py          # score, list misses
    python backend/scripts/score_hadith_search.py --check  # how many hadith each marker matches

A search scores when one of its top 10 hits carries the marker wording; MRR
also rewards finding it higher. Words "corrected" in a search not marked as a
typo are counted too: each is a real word the fixer rewrote. Needs a built
hadith.db.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services.hadith import search, words  # noqa: E402

TOP = 10


def _markers(item: dict):
    english = re.compile(item["english"], re.I | re.S) if item.get("english") else None
    arabic = re.compile(words.fold(item["arabic"]), re.S) if item.get("arabic") else None
    return english, arabic


def _carries(english, arabic, hit_english: str, hit_arabic: str) -> bool:
    return bool((english and english.search(hit_english)) or (arabic and arabic.search(words.fold(hit_arabic))))


def _yardstick() -> list[dict]:
    path = data_path("hadith_dir") / "search_yardstick.json"
    return json.loads(path.read_text(encoding="utf-8"))["searches"]


def check() -> None:
    """Every marker must match at least one hadith, or the search can never score."""
    conn = sqlite3.connect(f"file:{data_path('hadith_index_path')}?mode=ro", uri=True)
    rows = conn.execute("SELECT english, arabic FROM hadith").fetchall()
    conn.close()
    for item in _yardstick():
        english, arabic = _markers(item)
        n = sum(_carries(english, arabic, e, a) for e, a in rows)
        print(f"{n:6}  {item['q']}")


def score(show_misses: bool = True) -> float:
    by_kind: dict[str, list[float]] = defaultdict(list)
    misses, needless = [], []
    for item in _yardstick():
        english, arabic = _markers(item)
        result = search.search(item["q"], TOP)
        hits = result.hits
        if "typo" not in item["kind"]:
            needless += [f"{typed} -> {near}" for typed, near in result.corrected]
        rank = next((i for i, h in enumerate(hits, 1) if _carries(english, arabic, h.english, h.arabic)), None)
        by_kind[item["kind"]].append(1 / rank if rank else 0.0)
        if not rank:
            misses.append(item["q"])
    total = [r for ranks in by_kind.values() for r in ranks]
    found = sum(r > 0 for r in total)
    for kind, ranks in sorted(by_kind.items()):
        print(f"  {kind:14} {sum(r > 0 for r in ranks):2}/{len(ranks):<2}  MRR {sum(ranks) / len(ranks):.2f}")
    print(f"  {'all':14} {found:2}/{len(total):<2}  MRR {sum(total) / len(total):.2f}")
    print(f"  needless corrections: {len(needless)}", *needless, sep="\n    ")
    if show_misses and misses:
        print("missed:", *misses, sep="\n  ")
    return found / len(total)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Arabic searches print on a Windows console
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    check() if args.check else score()
