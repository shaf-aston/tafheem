"""Group captured form items for transcription, then merge the checked results.

    python forms_units.py units   # _work/units.json: batches of questions with their section instructions
    python forms_units.py harakat # _work/harakat_results.json (two blind reads + tiebreak) -> batch files
    python forms_units.py merge   # _work/batches/*.json -> iraab.json, tarkeeb.json

A question is a numbered item plus its lettered parts (4a, 4b, 4c), transcribed
together so the explanation and translation parts keep their sentence. Page-by-page
batches were rejected: a batch boundary could split one question.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
WORK = HERE / "_work"
FORMS = [f["id"] for f in json.loads((HERE / "forms.json").read_text(encoding="utf8"))["forms"]]
BATCH = {"single": 8, "lettered": 3}  # statements are short; a lettered question is 2 to 4 pictures
SKIP = re.compile(r"^(End of exercise|Difficulty|How difficult)")
NUMBERED = re.compile(r"^(\d+)([a-z]?)\.")


def units(form):
    data = json.loads((HERE / form / "items.json").read_text(encoding="utf8"))
    out, intro, section, header, current = [], [], None, None, None
    for it in data["items"]:
        text, first = it["text"], it["text"].split("\n", 1)[0].strip()
        if SKIP.match(first):
            continue
        m = NUMBERED.match(first)
        if not m:
            if first != section:  # a new section: its first header carries the instructions
                section, intro, current = first, [it["image"]], None
            else:
                header = it["image"]
            continue
        num, letter = m.groups()
        if current and letter and current["number"] == num and current["lettered"]:
            current["images"].append(it["image"])
            continue
        images = ([header] if header and letter else []) + [it["image"]]
        current = {"form": form, "topic": data["title"], "section": section, "number": num,
                   "lettered": bool(letter), "instructions": intro, "images": images}
        header = None
        out.append(current)
    return out


def build():
    batches = []
    for form in FORMS:
        us = units(form)
        for kind in ("single", "lettered"):
            group = [u for u in us if u["lettered"] == (kind == "lettered")]
            for i in range(0, len(group), BATCH[kind]):
                chunk = group[i:i + BATCH[kind]]
                batches.append({"batch": f"{form}-{kind}-{i // BATCH[kind] + 1:02d}", "dir": str(HERE / form), "units": chunk})
    WORK.mkdir(exist_ok=True)
    (WORK / "units.json").write_text(json.dumps(batches, ensure_ascii=False, indent=1), encoding="utf8")
    print(len(batches), "batches,", sum(len(b["units"]) for b in batches), "questions")


# Flags about the student's blank or typed boxes, or notes already applied, are noise once
# free-text parts are dropped; only doubts about what is printed stay for a person.
NOISE = re.compile(r"blank|placeholder|stray letter|typed response|response is|my_response|no student|"
                   r"Both A and B|ticked \(checkbox|confirmed correct by green|All three rows|scored 1/1|"
                   r"No instructions|no printed haraka|no haraka in the picture|No visible tanween|"
                   r"not a transcription gap|corrected to drop|swapped from the original|as first transcribed|"
                   r"over-vowelled|two occurrences|answer_source is recorded", re.I)


def score(points):
    if isinstance(points, dict):  # a grid scored row by row
        pairs = [p.split("/") for p in points.values()]
        return {"got": sum(int(a) for a, _ in pairs), "of": sum(int(b) for _, b in pairs)}
    if points:
        got, of = points.split("/")
        return {"got": int(got), "of": int(of)}
    return None


def compact(d):
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def publish(q):
    """Finished shape: the student's typed explanations and translations are not kept, only what
    was ticked; the teacher's notes become one explanation. Section text lives once per section."""
    notes = [p["feedback"] for p in q["parts"] if p.get("feedback")]
    parts = [compact({**{k: p.get(k) for k in ("label", "ask", "kind", "options", "rows", "columns",
                                                "answer", "answer_source", "my_response")},
                      "score": score(p.get("points"))})
             for p in q["parts"] if p["kind"] != "free_text"]
    return compact({"id": q["id"], "section": q["id"].rsplit("/", 1)[0], "number": int(q["source"]["number"]),
                    "type": q["type"], "prompt": q.get("prompt"),
                    "sentences": [compact(s) for s in q.get("sentences") or []], "parts": parts,
                    "explanation": "\n\n".join(notes), "images": [f"{q['source']['form']}/{i}" for i in q["source"]["images"]],
                    "flags": [f for f in q.get("flags", []) if not NOISE.search(f)]})


def section(q):
    s = q["source"]
    return {"form": s["form"], "title": s["title"], "topic": q["topic"],
            "name": re.sub(r"\s*\|\s*Q\d+$", "", s["section"]), "instructions": q.get("instructions")}


def merge():
    by_cat, seen, problems = {"iraab": [], "tarkeeb": []}, set(), []
    for f in sorted((WORK / "batches").glob("*.json")):
        for q in json.loads(f.read_text(encoding="utf8"))["questions"]:
            if q.get("id") in seen:
                problems.append(f"duplicate id {q.get('id')} in {f.name}")
                continue
            if q.get("category") not in by_cat:
                problems.append(f"bad category {q.get('category')!r} for {q.get('id')} in {f.name}")
                continue
            seen.add(q["id"])
            by_cat[q["category"]].append(q)
    expected = sum(len(b["units"]) for b in json.loads((WORK / "units.json").read_text(encoding="utf8")))
    if len(seen) != expected:
        problems.append(f"{len(seen)} questions merged, {expected} expected")
    out = {}
    for cat, qs in by_cat.items():
        sections, ordered = {}, sorted(qs, key=lambda q: (q["id"].rsplit("/", 1)[0], int(q["source"]["number"])))
        for q in ordered:
            key = q["id"].rsplit("/", 1)[0]
            # Some unit pictures miss the section text; keep the first one that has it.
            if not (sections.get(key) or {}).get("instructions"):
                sections[key] = section(q)
        out[cat] = [publish(q) for q in ordered]
        (HERE / f"{cat}.json").write_text(json.dumps({"sections": sections, "questions": out[cat]},
                                                     ensure_ascii=False, indent=1), encoding="utf8")
        print(cat, len(qs))
    flagged = [q["id"] for qs in out.values() for q in qs if q.get("flags")]
    print("flagged for a person to check:", len(flagged))
    for p in problems:
        print("PROBLEM", p)
    sys.exit(1 if problems else 0)


HARAKAT = re.compile("[ً-ْٰ]")


def bare(s):
    return HARAKAT.sub("", s).replace("ـ", "").strip()


def flag(q, text):
    if text not in q.setdefault("flags", []):  # reruns must not stack the same flag
        q["flags"].append(text)


def harakat():
    """Write the double-read vowels into the batch files; the first pass guessed vowels from grammar."""
    results = {r["id"]: r for r in json.loads((WORK / "harakat_results.json").read_text(encoding="utf8"))}
    changed, problems = 0, []
    for f in sorted((WORK / "batches").glob("*.json")):
        data = json.loads(f.read_text(encoding="utf8"))
        for q in data["questions"]:
            r = results.get(q["id"])
            if not q.get("sentences"):
                continue
            if not r or r.get("error") or r.get("tieFailed"):
                problems.append(f"{q['id']}: no settled read")
                continue
            read = {s["index"]: s for s in r["sentences"]}
            for i, s in enumerate(q["sentences"]):
                if i not in read:
                    problems.append(f"{q['id']} sentence {i}: missing from the read")
                    continue
                words = read[i]["words"]
                ar = " ".join(words)
                if bare(ar).replace(" ", "") != bare(s["ar"]).replace(" ", ""):
                    # Letters moved, not just vowels: a person decides, never silently swapped.
                    flag(q, f"Vowel check read different letters for sentence {i}: {ar}")
                    continue
                changed += s["ar"] != ar
                s["ar"] = ar
                for m in s.get("marked", []):
                    span = m["text"].split()
                    for k in range(len(words) - len(span) + 1):
                        if [bare(w) for w in words[k:k + len(span)]] == [bare(w) for w in span]:
                            m["text"] = " ".join(words[k:k + len(span)])
                            break
                for w in read[i].get("unsure", []):
                    flag(q, f"Vowels on {w} could not be read with certainty.")
        f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf8")
    print("sentences re-vowelled:", changed)
    for p in problems:
        print("PROBLEM", p)


if __name__ == "__main__":
    {"units": build, "merge": merge, "harakat": harakat}[sys.argv[1]]()
