"""Merge two scholars' lists of verbally similar verses into one catalogue.

    python -m backend.scripts.build_mutashabihat            # write the catalogue
    python -m backend.scripts.build_mutashabihat --dry-run  # count everything, write nothing

Inputs, in data/quran/downloads/mutashabihat/:

    benchmark_pairs.csv                 2,229 pairs from Hidayat al-Murtab and Tatimmat
                                        al-Bayan, with a change type (GPL-3.0, the paper
                                        "Detecting and Localizing Verbally Similar Verses")
    waqar144_mutashabiha_data.json      a hafiz's list from Qari Idrees Al Asim; free to
                                        use with credit. Ayahs are global 0-based indexes 0..6235
                                        (its top keys are juz, not surah), checked by text.

Output is data/quran/mutashabihat.json: groups of verses that resemble one another,
each pair carrying the word spans where the two differ. The spans are computed here
from our own imlaei text with services.mutashabihat.diff, never copied from either
source: the benchmark's verse text is Tanzil's spelling, not ours, so its word
positions would point at the wrong words.

Rejected: finding pairs here by an algorithm. This file only joins what people
recorded; the finder in services/mutashabihat.py proposes the rest for review.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services import mutashabihat  # noqa: E402

SOURCES_DIR = "downloads/mutashabihat"
BENCHMARK = "benchmark"
WAQAR = "waqar144"
SOURCE_ORDER = (BENCHMARK, WAQAR)


def quran_dir() -> Path:
    return data_path("quran_imlaei_path").parent


def benchmark_rows(directory: Path) -> list[tuple[str, str, str, str]]:
    with (directory / "benchmark_pairs.csv").open(encoding="utf-8-sig", newline="") as handle:
        return [(r["key_a"], r["key_b"], BENCHMARK, r["change_type"]) for r in csv.DictReader(handle)]


def waqar_rows(directory: Path, keys: list[str]) -> tuple[list[tuple[str, str, str, str]], int]:
    """Global 0-based ayah index -> "s:a" (1-based put 9% of pairs on shared words, 0-based 92%).

    An entry may be a run of ayahs; two runs of one length pair up ayah by ayah,
    and runs of different lengths are skipped and counted rather than guessed at.
    """
    data = json.loads((directory / "waqar144_mutashabiha_data.json").read_text(encoding="utf-8"))
    ordered = sorted(keys, key=lambda k: tuple(map(int, k.split(":"))))
    if len(ordered) != 6236:
        raise SystemExit(f"imlaei.json has {len(ordered)} ayahs, not 6236; global indexes would drift.")

    def run(node) -> list[int]:
        return node if isinstance(node, list) else [node]

    rows, skipped = [], 0
    for entry in (e for rows_ in data.values() for e in rows_):
        src = run(entry["src"]["ayah"])
        for mut in entry["muts"]:
            other = run(mut["ayah"])
            if len(src) != len(other):
                skipped += 1
                continue
            rows += [(ordered[i], ordered[j], WAQAR, "") for i, j in zip(src, other)]
    return rows, skipped


def merge(rows, valid: set[str]) -> tuple[dict, Counter]:
    """One entry per unordered pair: its sources and its change type.

    A self-pair, a key we have no text for, or a pair seen again from the same
    source is rejected and counted; seen again from another source it is overlap.
    """
    pairs: dict[tuple[str, str], dict] = {}
    rejected: Counter = Counter()
    for a, b, source, change_type in rows:
        if a == b:
            rejected["self-pair"] += 1
            continue
        if a not in valid or b not in valid:
            rejected["unknown key"] += 1
            continue
        entry = pairs.setdefault(mutashabihat.pair_key(a, b), {"sources": [], "change_type": ""})
        if source in entry["sources"]:
            rejected["duplicate"] += 1
            continue
        entry["sources"].append(source)
        entry["change_type"] = entry["change_type"] or change_type
    return pairs, rejected


def groups_of(pairs: dict, texts: dict[str, str]) -> list[dict]:
    """Verses joined by any pair form one group; ids run in order of each group's first verse."""
    parent: dict[str, str] = {}

    def find(k: str) -> str:
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for a, b in pairs:
        parent[find(a)] = find(b)
    members: dict[str, list[str]] = {}
    for key in parent:
        members.setdefault(find(key), []).append(key)

    def order(k: str) -> tuple[int, int]:
        s, _, a = k.partition(":")
        return int(s), int(a)

    groups = []
    for keys in sorted((sorted(m, key=order) for m in members.values()), key=lambda m: order(m[0])):
        rows = []
        for (a, b), entry in sorted(pairs.items(), key=lambda kv: (order(kv[0][0]), order(kv[0][1]))):
            if a in keys:
                diff_a, diff_b = mutashabihat.diff(texts[a].split(), texts[b].split())
                rows.append({"a": a, "b": b, "diff_a": diff_a, "diff_b": diff_b,
                             "change_type": entry["change_type"], "sources": sorted(entry["sources"], key=SOURCE_ORDER.index)})
        types = Counter(p["change_type"] for p in rows if p["change_type"])
        groups.append({
            "id": len(groups) + 1,
            "keys": keys,
            "change_type": types.most_common(1)[0][0] if types else "",
            "sources": [s for s in SOURCE_ORDER if any(s in p["sources"] for p in rows)],
            "pairs": rows,
        })
    return groups


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Count everything, write nothing")
    args = parser.parse_args()

    directory = quran_dir() / SOURCES_DIR
    texts = mutashabihat.texts()
    missing = [n for n in ("benchmark_pairs.csv", "waqar144_mutashabiha_data.json") if not (directory / n).exists()]
    if missing:
        raise SystemExit(f"Missing in {directory}: {', '.join(missing)}")

    bench = benchmark_rows(directory)
    waqar, unaligned = waqar_rows(directory, list(texts))
    pairs, rejected = merge(bench + waqar, set(texts))
    if unaligned:
        rejected["waqar144 runs of unequal length"] = unaligned
    groups = groups_of(pairs, texts)

    by_source = Counter(s for entry in pairs.values() for s in entry["sources"])
    overlap = sum(1 for entry in pairs.values() if len(entry["sources"]) > 1)
    print(f"  {len(groups)} groups, {len(pairs)} pairs over {sum(len(g['keys']) for g in groups)} verses")
    print(f"    benchmark {by_source[BENCHMARK]}, waqar144 {by_source[WAQAR]}, in both {overlap}")
    print(f"    read {len(bench)} + {len(waqar)} rows; rejected: {dict(rejected) or 'none'}")
    if args.dry_run:
        return 0

    target = data_path("mutashabihat_path")
    target.write_text(json.dumps({
        "_comment": "Verbally similar verses, joined from the benchmark (Hidayat al-Murtab, Tatimmat al-Bayan) and Waqar144's list (Qari Idrees Al Asim). Spans are [start, end) word positions in data/quran/imlaei.json split on whitespace. Built by scripts/build_mutashabihat.py; never hand-edited.",
        "groups": groups,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  -> {target.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
