"""Vowel each reorder tile from its own answer so tiles and answer agree. Dry run unless --write."""
import json, re, sys
from pathlib import Path
H = re.compile("[ً-ْٰ]")
P = "؟،؛?,.!"
core = lambda s: s.strip(P)
strip = lambda s: H.sub("", core(s))
write = "--write" in sys.argv

def reorders(o):
    if isinstance(o, dict):
        if o.get("type") == "reorder": yield o
        for v in o.values(): yield from reorders(v)
    elif isinstance(o, list):
        for v in o: yield from reorders(v)

n = left = 0; reformatted = []
for f in sorted(Path("backend/data/colloquial").glob("*/unit-*.json")):
    text = f.read_text(encoding="utf-8"); data = json.loads(text); changed = False
    for ex in reorders(data):
        ans, words = ex.get("answer", ""), ex.get("words") or []
        aw = ans.split()
        for i, t in enumerate(words):
            if t in ans: continue
            n += 1; k = len(t.split()); hit = None
            for j in range(len(aw) - k + 1):
                seg = core(" ".join(aw[j:j + k]))
                if strip(seg) == strip(t): hit = seg; break
            if hit:
                tail = t[len(t.rstrip(P)):]
                words[i] = hit + tail; changed = True
            else:
                left += 1; print("unplaced", f.parent.name, f.stem, t, "|", ans)
    if changed and write:
        out = json.dumps(data, ensure_ascii=False, indent=2)
        if out + "\n" != text and out != text: reformatted.append(f"{f.parent.name}/{f.stem}")
        f.write_text(out + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
print(f"mismatched tiles {n}, unplaced {left}, files reformatted {reformatted}")
