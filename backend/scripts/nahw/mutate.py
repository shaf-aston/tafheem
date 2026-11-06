"""Mutation guard for the i'raab engine: change a keyed sentence in a way the grammar says
must move the answer in a known way, and check that it did. The expected answer of each
mutant comes from the source sentence's own key (exact sets of score_iraab).

  bare    harakat stripped                  -> same roles
  rename  one proper name for another       -> same roles
  noun    one ال person-noun for another    -> same roles
  inna    إِنَّ before a nominal sentence     -> حرف, اسم إن, خبر إن
  kana    كَانَ before a nominal sentence     -> فعل, اسم كان, خبر كان
  twice   the same sentence a second time   -> identical cards

A mutant of a sentence the app already got wrong is not counted (base_wrong). A wrong mutant
is "flagged" when every wrong word's card names the key's role as its other reading (`assumed.other`):
the app said it had to choose a reading the typed harakat do not settle, and the other one is
the right one, so the miss is honest. A flag naming some other role is still unflagged. Strict counts every wrong mutant.

Pools and governors: data/nahw_rules/mutation_config.json. Baseline: mutation_baseline.json.
Offline, about 1.5 s per keyed sentence (all exact sets: ~20 min).

    venv/Scripts/python -m backend.scripts.nahw.mutate --limit 60
    venv/Scripts/python -m backend.scripts.nahw.mutate --check
    venv/Scripts/python -m backend.scripts.nahw.mutate --save-baseline
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import zlib
from collections import Counter, defaultdict
from itertools import zip_longest
from pathlib import Path

from backend.scripts.nahw.score_iraab import DATA, EXACT, SETS, plain_role, right_role, routed
from backend.services.text.arabic_text import bare_letters, strip_diacritics, words

RULES = DATA / "nahw_rules"
CONFIG = json.loads((RULES / "mutation_config.json").read_text(encoding="utf-8"))
BASELINE = RULES / "mutation_baseline.json"
MARKS = re.compile("[ً-ْٰ]+$")  # trailing harakat of a word


def swap_one(sentence: str, pool: list[str]) -> str | None:
    """The first word of the pool replaced by the next one, keeping its typed ending."""
    ws = words(sentence)
    for i, w in enumerate(ws):
        bare = bare_letters(w)
        if bare in pool:
            tail = MARKS.search(w)
            ws[i] = pool[(pool.index(bare) + 1) % len(pool)] + (tail.group(0) if tail else "")
            return " ".join(ws)
    return None


def to_nasb(word: str) -> str | None:
    """A raf' ending turned to nasb: ُ -> َ, ٌ -> ً (with alif unless ة/ء/ى before)."""
    if word.endswith("ٌ"):
        stem = word[:-1]
        return stem + ("ً" if stem[-1] in "ةءى" else "ًا")
    if word.endswith("ُ"):
        return word[:-1] + "َ"
    return None


def mutations(ex: dict) -> list[tuple[str, str, list[str]]]:
    """(kind, mutated sentence, expected key) for each mutation that applies."""
    s, key = ex["sentence"], ex["key"]
    out = []
    if strip_diacritics(s) != s:
        out.append(("bare", strip_diacritics(s), key))
    for kind, pool in (("rename", CONFIG["names"]), ("noun", CONFIG["nouns"])):
        if m := swap_one(s, pool):
            out.append((kind, m, key))
    ws = words(s)
    if key == CONFIG["nominal_key"] and len(ws) == 2:
        for kind, gov in CONFIG["governors"].items():
            if nasb := to_nasb(ws[gov["nasb"]]):
                shown = [nasb if i == gov["nasb"] else w for i, w in enumerate(ws)]
                out.append((kind, " ".join([gov["word"], *shown]), gov["key"]))
    return out


def wrong_words(cards: list[dict], key: list[str], by_family: bool, also: dict | None = None) -> list[int]:
    """Indexes of the words whose role is not the key's; every word when the count differs."""
    if len(cards) != len(key):
        return list(range(max(len(cards), len(key))))
    return [i for i, want in enumerate(key) if not right_role(plain_role(cards[i].get("role")), want, (also or {}).get(str(i), []), by_family, cards[i]["word"])]


def names_the_key(card: dict, want: str, also: list[str], by_family: bool) -> bool:
    """The card's other reading (`assumed.other`) is the key's role."""
    other = (card.get("assumed") or {}).get("other")
    return bool(other) and right_role(plain_role(other), want, also, by_family, card["word"])


def keyed_rows(sets: list[str]) -> list[dict]:
    """Each exact set's rows, round robin so a limit still covers every set, one per sentence."""
    seen, rows = set(), []
    per_set = [[{**ex, "set": name, "by": ex.get("by")} for ex in SETS[name]()] for name in sets]
    for group in zip_longest(*per_set):
        for ex in group:
            if ex and ex["sentence"] not in seen:
                seen.add(ex["sentence"])
                rows.append(ex)
    ids = Counter(ex["id"] for ex in rows)
    clash = [i for i, n in ids.items() if n > 1]
    if clash:
        sys.exit(f"sentence ids repeat across sets, the baseline cannot tell them apart: {clash[:5]}")
    return rows


def run(rows: list[dict], fails: dict) -> dict[str, dict]:
    """Per mutation kind: right, wrong (strict), flagged (wrong, every wrong word names the key as its other reading),
    base_wrong (not counted), crashed, and the ids of the sentences whose mutant was right."""
    stats: dict[str, dict] = defaultdict(lambda: {"right": 0, "wrong": 0, "flagged": 0, "base_wrong": 0, "crashed": 0, "whole": []})
    every = CONFIG["twice_every"]
    t0 = time.time()
    for n, ex in enumerate(rows, 1):
        by_family = ex.get("by") == "family"
        base = routed(ex["sentence"], None)
        if base.get("read_failed"):
            stats["base"]["crashed"] += 1
            continue
        base_right = not wrong_words(base["words"], ex["key"], by_family, ex.get("also"))
        if zlib.crc32(ex["id"].encode()) % every == 0:  # by id, so adding a set never moves the sample
            again = routed(ex["sentence"], None)
            shape = lambda a: [(plain_role(c.get("role")), c.get("case")) for c in a["words"]]
            same = shape(base) == shape(again)
            stats["twice"]["right" if same else "wrong"] += 1
            if same:
                stats["twice"]["whole"].append(ex["id"])
            else:
                fails["twice"].append({"id": ex["id"], "sentence": ex["sentence"]})
        for kind, sentence, key in mutations(ex):
            row = stats[kind]
            if kind in ("bare", "rename", "noun") and not base_right:
                row["base_wrong"] += 1
                continue
            ans = routed(sentence, None)
            if ans.get("read_failed"):
                row["crashed"] += 1
                continue
            same_key = kind in ("bare", "rename", "noun")
            bad = wrong_words(ans["words"], key, by_family and same_key, ex.get("also") if same_key else None)
            if not bad:
                row["right"] += 1
                row["whole"].append(ex["id"])
                continue
            row["wrong"] += 1
            flagged = len(ans["words"]) == len(key) and all(
                names_the_key(ans["words"][i], key[i], (ex.get("also") or {}).get(str(i), []), by_family and same_key) for i in bad)
            row["flagged"] += flagged
            fails[kind].append({"id": ex["id"], "set": ex["set"], "sentence": ex["sentence"], "mutated": sentence,
                                "flagged": flagged, "wrong": [f"{strip_diacritics(ans['words'][i]['word'])}: "
                                                              f"{plain_role(ans['words'][i].get('role')) or 'blank'}"
                                                              for i in bad if i < len(ans["words"])]})
        if n % 25 == 0:
            print(f"{n}/{len(rows)}  {time.time() - t0:.0f}s", flush=True)
    return stats


def show(stats: dict[str, dict]) -> None:
    print(f"{'kind':<8} {'right':>6} {'wrong':>6} {'flagged':>8} {'unflagged':>10} {'base_wrong':>11}")
    for kind, s in stats.items():
        print(f"{kind:<8} {s['right']:>6} {s['wrong']:>6} {s['flagged']:>8} {s['wrong'] - s['flagged']:>10} {s['base_wrong']:>11}")


def check(stats: dict[str, dict], ran: set[str], partial: bool) -> int:
    """1 when a kind has a mutant wrong that the baseline had right, or (on a full run) more
    unflagged wrong mutants than the baseline; crashes also fail."""
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    bad = []
    for kind, s in stats.items():
        b = base.get(kind, {})
        lost = sorted((set(b.get("whole", ())) & ran) - set(s["whole"]))
        if lost:
            bad.append(f"{kind}: right in the baseline, wrong now: {' '.join(lost)}")
        if not partial and s["wrong"] - s["flagged"] > b.get("wrong", 0) - b.get("flagged", 0):
            bad.append(f"{kind}: unflagged wrong {s['wrong'] - s['flagged']}, baseline {b.get('wrong', 0) - b.get('flagged', 0)}")
        if s["crashed"]:
            bad.append(f"{kind}: the reader broke on {s['crashed']} mutants")
    print(*bad, sep="\n")
    if not bad and not partial and any(s["right"] > base.get(k, {}).get("right", 0) for k, s in stats.items()):
        print("Better than the baseline: run --save-baseline so it cannot slip back.")
    return int(bool(bad))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, default=0, help="only the first N sentences (round robin over the sets)")
    ap.add_argument("--sets", default=",".join(EXACT), help="comma list of exact sets")
    ap.add_argument("--fails", help="write the wrong mutants (with their flag) to this json file")
    ap.add_argument("--check", action="store_true", help="fail when a kind gets worse than the baseline")
    ap.add_argument("--save-baseline", action="store_true", help="write today's counts as the baseline")
    args = ap.parse_args()
    sets = args.sets.split(",")
    if bad := [s for s in sets if s not in EXACT]:
        ap.error(f"not exact sets: {bad}")
    if args.limit < 0:
        ap.error("--limit cannot be negative")
    rows = keyed_rows(sets)[: args.limit or None]
    partial = bool(args.limit) or sets != list(EXACT)
    if args.save_baseline and partial:
        ap.error("a baseline needs the full run: no --limit, all sets")
    print(f"{len(rows)} keyed sentences", flush=True)
    fails: dict[str, list] = defaultdict(list)
    stats = run(rows, fails)
    show(stats)
    if args.fails:
        Path(args.fails).write_text(json.dumps(fails, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.save_baseline:
        BASELINE.write_text(json.dumps({k: {**s, "whole": sorted(s["whole"])} for k, s in stats.items()},
                                       ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("Baseline saved.")
    elif args.check:
        sys.exit(check(stats, {ex["id"] for ex in rows}, partial))


if __name__ == "__main__":
    main()
