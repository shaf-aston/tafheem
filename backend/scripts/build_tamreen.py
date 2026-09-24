"""The Tamreen exercises, from a Google Form's score page to one clean file each.

Two steps, run from the project root:

    python backend/scripts/build_tamreen.py save     # clipboard -> raw/<slug>.json + images/
    python backend/scripts/build_tamreen.py build    # raw/ + written/ -> exercises/<slug>.json

`save` expects the clipboard to hold what tamreen_harvest.js copied: open the
form's score page, paste that file into the browser console, run
`copyForm('haal')`. The pictures are public, so they are fetched here with
curl, no sign-in.

`build` keeps only what teaches: the question, its options, the right answer.
Scores and the student's own answers are dropped. Anything a person or an
agent wrote afterwards (what a picture says, an explanation, the tags) lives in
written/<slug>.json and is merged in, so harvesting again never loses it.

Fails loud: an answer that is not one of the options, or a grid row with no
right answer, stops the build and names the question.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "tamreen"
RAW, IMAGES, WRITTEN, EXERCISES = (ROOT / d for d in ("raw", "images", "written", "exercises"))

# Google Forms item types worth keeping.
CHECKBOX, TEXT, GRID, SECTION = 4, 0, 7, 8
RULE = re.compile(r"^(\d+)\.\s")            # "3. The حال is..."
PART = re.compile(r"^(\d+) ?([a-z])?\.\s*(.*)$", re.S)  # "3b. Explain", "11 b. ...", or "11." alone


def save() -> None:
    # PowerShell writes its console in the machine's legacy code page unless
    # told otherwise, which turns every Arabic letter into "?" on the way out.
    clip = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw"],
        capture_output=True, text=True, encoding="utf-8").stdout
    body = json.loads(clip)
    if "?" * 3 in json.dumps(body["form"]["items"][2]["entries"]):
        raise ValueError("the Arabic arrived as question marks; the clipboard was not read as UTF-8")
    slug = body["slug"]
    if not re.fullmatch(r"[a-z0-9-]{1,40}", slug):
        # The slug names files on disk and came from a web page's clipboard.
        raise ValueError(f"slug must be short lower-case letters, digits and dashes, got {slug!r}")
    RAW.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(exist_ok=True)
    (RAW / f"{slug}.json").write_text(json.dumps(_scrub(body["form"]), ensure_ascii=False, indent=1), encoding="utf-8")
    for i, url in enumerate(body["images"]):
        path = IMAGES / f"{slug}-{i:02d}.png"
        if not path.exists():
            subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", "-o", str(path), url], check=True)
    print(slug, len(body["form"]["items"]), "items", len(body["images"]), "pictures")


def _scrub(form: dict) -> dict:
    """The form without the people in it: the student's name box and any email address.

    raw/ is only a source to rebuild from, but it still sits on disk, and a
    library of grammar questions has no use for who answered them.
    """
    form["description"] = re.sub(r"\S+@\S+", "[email removed]", form.get("description") or "")
    form["items"] = [item for item in form["items"] if _tidy(item["title"]) != "Name"]
    return form


def _answer(item: dict) -> list | dict | str | None:
    """The right answer as the form's own marking shows it, or None for an unmarked text answer."""
    dom = item["dom"]
    points = dom["points"]
    if item["type"] == GRID:
        # A row ticked right keeps its ticks; a row ticked wrong shows the right
        # ticks again in a second, unmarked grid. Both count; a wrong row's own
        # ticks do not.
        rows: dict[str, list[str]] = {}
        for cell in dom["checked"]:
            column, _, row = cell["label"].partition(", response for ")
            if cell["mark"] != "Incorrect":
                rows.setdefault(row, []).append(column)
        missing = [e["row"] for e in item["entries"] if e["row"] not in rows]
        if missing:
            raise ValueError(f"{item['title']!r}: no right answer for rows {missing}")
        return rows
    if item["type"] == CHECKBOX:
        options = item["entries"][0]["options"]
        got = [c["label"] for c in dom["checked"]] if points and points[0] == points[1] else _block(dom)
        # The page collapses runs of spaces the form's own option text keeps.
        spelled = {_tidy(o): o for o in options}
        bad = [g for g in got or [] if _tidy(g) not in spelled]
        if not got or bad:
            raise ValueError(f"{item['title']!r}: answer {bad or got!r} is not among {options}")
        return [spelled[_tidy(g)] for g in got]
    # Free text: the teacher's model answer if the form has one, else their feedback, else nothing.
    return (_block(dom) or [None])[0] or dom["feedback"]


def _block(dom: dict) -> list[str] | None:
    """The form's "Correct answers" lines, without the teacher's feedback that follows them."""
    lines = dom["correctBlock"] or []
    return lines[: lines.index("Feedback")] if "Feedback" in lines else (lines or None)


def _tidy(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def build_one(slug: str) -> dict:
    raw = json.loads((RAW / f"{slug}.json").read_text(encoding="utf-8"))
    written = json.loads((WRITTEN / f"{slug}.json").read_text(encoding="utf-8")) if (WRITTEN / f"{slug}.json").exists() else {}
    pictures, notes = written.get("pictures", {}), written.get("notes", {})

    rules, examples = [], []
    section, group = "", None
    for item in raw["items"]:
        title = _tidy(item["title"])
        if item["type"] == SECTION:
            section = title.split("|")[0].strip()
            continue
        if item["type"] not in (CHECKBOX, TEXT, GRID) or title == "Name":
            continue
        dom = item["dom"]
        picture = dom["imgs"][0] if dom["imgs"] else None

        if m := RULE.match(title):
            q = {"id": f"{slug}-r{int(m[1]):02d}", "question": title[m.end():].strip(),
                 "options": item["entries"][0]["options"], "answer": _answer(item)}
            if picture:
                q["picture"] = picture
            rules.append(q)
            continue

        m = PART.match(title)
        if not m:
            raise ValueError(f"{slug}: cannot place {title!r}")
        # A picture question with no letter ("11.") is a question of one part.
        number, letter, question = int(m[1]), m[2] or "a", _tidy(m[3])
        if letter == "a":
            group = {"id": f"{slug}-e{len(examples) + 1:02d}", "section": section, "picture": picture,
                     "instruction": _tidy((item["media"] or {}).get("caption")), "parts": []}
            # Only what was read off the picture may come in; never the id or file name.
            read = pictures.get(picture, {})
            group.update({k: read[k] for k in ("sentence", "marked", "doubt") if k in read})
            examples.append(group)
        if group is None:
            raise ValueError(f"{slug}: {title!r} comes before any picture question")
        # A later part with its own picture (the numbered words of a tarkeeb) has
        # its own caption; the first part's would describe the wrong picture.
        own = picture and picture != group["picture"]
        caption = _tidy((item["media"] or {}).get("caption")) if own else group["instruction"]
        part = {"letter": letter, "question": question or caption}
        if own:
            part["picture"] = picture
        if item["type"] == GRID:
            part["options"] = item["entries"][0]["options"]
            part["rows"] = [e["row"] for e in item["entries"]]
        elif item["type"] == CHECKBOX:
            part["options"] = item["entries"][0]["options"]
        part["answer"] = _answer(item)
        part["by"] = "teacher" if part["answer"] is not None else None
        # What was written here afterwards: a wording for a question the form
        # left blank, and an answer only where the teacher gave none.
        ours = notes.get(f"{group['id']}{letter}", {})
        part["question"] = part["question"] or ours.get("question", "")
        if part["answer"] is None and ours.get("answer"):
            part["answer"], part["by"] = ours["answer"], "claude"
        if ours.get("labels"):
            # What a placeholder row ("?1", ">") points at in the picture.
            part["labels"] = ours["labels"]
        if ours.get("doubt"):
            # A reviewer's reason to distrust the teacher's marking, kept in view.
            part["doubt"] = ours["doubt"]
        group["parts"].append(part)

    tags = written.get("tags", {})
    for q in rules + examples:
        q["tags"] = tags.get(q["id"], [])
    return {"title": written.get("title", raw["title"]), "form": raw["title"],
            "harvested": date.today().isoformat(), "rules": rules, "examples": examples}


def build() -> None:
    EXERCISES.mkdir(exist_ok=True)
    for path in sorted(RAW.glob("*.json")):
        out = build_one(path.stem)
        (EXERCISES / path.name).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        unwritten = sum(p["answer"] is None for e in out["examples"] for p in e["parts"])
        unread = sum("sentence" not in e for e in out["examples"])
        print(f"{path.stem}: {len(out['rules'])} rules, {len(out['examples'])} examples, "
              f"{unread} pictures unread, {unwritten} answers unwritten")


if __name__ == "__main__":
    {"save": save, "build": build}[sys.argv[1]]()
