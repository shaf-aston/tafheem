"""Guard and sampler for the colloquial tashkil pass. Run from the repo root.

    python tashkil_tools.py guard <dialect>          # every string equals git HEAD once harakat are removed
    python tashkil_tools.py sample <dialect> <round> # a fixed ~30% of phrase + reply Arabic, as JSON
    python tashkil_tools.py coverage <dialect>       # share of phrase + reply Arabic carrying harakat
    python tashkil_tools.py list <dialect> <unit>    # that unit's phrase + reply Arabic, as JSON
    python tashkil_tools.py apply <dialect> <unit> <file>  # file: [{"old": ..., "new": ...}], letters must match
    guard also takes an optional <unit>.
"""
import json
import re
import subprocess
import sys
import zlib
from pathlib import Path

HARAKAT = re.compile("[ً-ْٰ]")
ROOT = Path("backend/data/colloquial")
strip = lambda s: HARAKAT.sub("", s)


def units(dialect, unit="*"):
    return sorted((ROOT / dialect).glob(f"{unit}.json" if unit != "*" else "unit-*.json"))


def walk(a, b, path, bad):
    if isinstance(a, dict):
        if set(a) != set(b):
            bad.append(f"{path}: keys changed")
            return
        for k in a:
            walk(a[k], b[k], f"{path}.{k}", bad)
    elif isinstance(a, list):
        if len(a) != len(b):
            bad.append(f"{path}: length changed")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", bad)
    elif isinstance(a, str):
        if strip(a) != strip(b):
            bad.append(f"{path}: letters changed {b!r} -> {a!r}")
    elif a != b:
        bad.append(f"{path}: value changed")


def guard(dialect, unit="*"):
    bad = []
    for f in units(dialect, unit):
        old = json.loads(subprocess.run(["git", "show", f"HEAD:{f.as_posix()}"], capture_output=True, check=True).stdout.decode("utf-8"))
        walk(json.loads(f.read_text(encoding="utf-8")), old, f.stem, bad)
    print("\n".join(bad) or "ok")
    return not bad



def strings(dialect, unit="*"):
    for f in units(dialect, unit):
        for lesson in json.loads(f.read_text(encoding="utf-8"))["lessons"]:
            for p in lesson["phrases"]:
                yield {"unit": f.stem, "lesson": lesson["lesson"], "slot": p["slot"], "field": "arabic", "arabic": p["arabic"], "sound": p.get("transliteration", "")}
                if p.get("reply"):
                    yield {"unit": f.stem, "lesson": lesson["lesson"], "slot": p["slot"], "field": "reply", "arabic": p["reply"]["arabic"], "sound": p["reply"].get("transliteration", "")}


def sample(dialect, rnd):
    # Deterministic, and a different 30% each round: 3 of every 10 hash buckets, shifted by the round.
    picks = {(int(rnd) * 3 + i) % 10 for i in range(3)}
    chosen = [s for s in strings(dialect) if zlib.crc32(f"{s['unit']}/{s['lesson']}/{s['slot']}/{s['field']}".encode()) % 10 in picks]
    print(json.dumps(chosen, ensure_ascii=False, indent=0))


def listing(dialect, unit):
    print(json.dumps(list(strings(dialect, unit)), ensure_ascii=False, indent=0))


LETTER = re.compile("[ء-يٱ-ۓ]")


def transfer(old, new):
    # Copies new's harakat onto old's own letters, so a dropped "؟" or space in new costs
    # nothing; None when the letters themselves differ.
    marks = []
    for ch in new:
        if LETTER.match(ch):
            marks.append("")
        elif HARAKAT.match(ch) and marks:
            marks[-1] += ch
    if [c for c in old if LETTER.match(c)] != [c for c in new if LETTER.match(c)]:
        return None
    out, i = [], 0
    for ch in strip(old):
        out.append(ch)
        if LETTER.match(ch):
            out.append(marks[i])
            i += 1
    return "".join(out)


def apply(dialect, unit, path):
    # Swaps each old string for its vowelled form wherever it is quoted in the file, so the
    # hand-kept layout survives. A string whose letters differ is skipped, not retried: the
    # checker samples later, and looping on it was costing a hundred turns a unit.
    f = units(dialect, unit)[0]
    text, skipped, done = f.read_text(encoding="utf-8"), [], 0
    for e in json.loads(Path(path).read_text(encoding="utf-8")):
        old, new = e["old"], transfer(e["old"], e["new"])
        if new is None:
            skipped.append(old)
        elif old != new:
            q = json.dumps(old, ensure_ascii=False)
            done += text.count(q)
            text = text.replace(q, json.dumps(new, ensure_ascii=False))
    json.loads(text)
    f.write_text(text, encoding="utf-8")
    print(f"ok ({done} replaced, {len(skipped)} skipped because letters differed: left unvowelled). DONE: do not retry, return now.")


def coverage(dialect):
    all_ = list(strings(dialect))
    print(f"{sum(bool(HARAKAT.search(s['arabic'])) for s in all_)}/{len(all_)}")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    ok = {"guard": guard, "sample": sample, "coverage": coverage, "list": listing, "apply": apply}[cmd](*args)
    sys.exit(0 if ok is not False else 1)
