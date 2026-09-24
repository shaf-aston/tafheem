#!/usr/bin/env python3
"""Join the note parts into one file per topic.

Each chunk of pages is read into `topics/_parts/<id>-<first page>.json`, one
writer per chunk so nothing is written twice. This joins them in page order and
puts the topic's names and its Tamreen links from `notes.json` on top.

    python backend/scripts/build_notes.py [note-id ...]

Fails loud on two blocks sharing an id, on a topic with a gap in its pages,
and on anything the app itself would refuse to load (services/nahw_notes.py),
because each of those means a chunk was read wrongly and would otherwise only
show up when the page is opened.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.services.nahw_notes import topic_faults  # noqa: E402  (the same check the app runs)

ROOT = Path(__file__).resolve().parents[1] / "data" / "nahw_notes"
PARTS_DIR = ROOT / "topics" / "_parts"


def numbered(folder: Path, note_id: str, suffix: str) -> list[Path]:
    """`<id>-NN<suffix>` files only, in number order. A plain glob on `<id>-*`
    would also take a note whose id merely starts with this one's."""
    shape = re.compile(rf"{re.escape(note_id)}-(\d+){re.escape(suffix)}")
    found = [(int(m[1]), p) for p in folder.iterdir() if (m := shape.fullmatch(p.name))]
    return [p for _, p in sorted(found)]


def load_parts(note_id: str) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in numbered(PARTS_DIR, note_id, ".json")]


def join(note: dict, pages: int) -> dict:
    blocks: list[dict] = []
    for part in load_parts(note["id"]):
        blocks += part["blocks"]
    seen = [b["id"] for b in blocks]
    twice = sorted({name for name in seen if seen.count(name) > 1})
    if twice:
        raise SystemExit(f"{note['id']}: two blocks share the id {twice}")
    covered = {b["page"] for b in blocks}
    missing = [n for n in range(pages) if n not in covered]
    if missing:
        raise SystemExit(f"{note['id']}: no block came from pages {missing}")
    return {
        "id": note["id"],
        "title": note["title"],
        "arabic": note["arabic"],
        "tamreen": note["tamreen"],
        "blocks": sorted(blocks, key=lambda b: b["page"]),
    }


def main(wanted: list[str]) -> None:
    conf = json.loads((ROOT / "notes.json").read_text(encoding="utf-8"))
    notes = [n for n in conf["notes"] if not wanted or n["id"] in wanted]
    for note in notes:
        if not numbered(PARTS_DIR, note["id"], ".json"):
            continue
        pages = len(numbered(ROOT / "images", note["id"], ".png"))
        topic = join(note, pages)
        if problem := topic_faults(note["id"], topic):
            raise SystemExit(problem)
        out = ROOT / "topics" / f"{note['id']}.json"
        out.write_text(json.dumps(topic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{note['id']:28s} {len(topic['blocks']):4d} blocks from {pages} pages")


if __name__ == "__main__":
    main(sys.argv[1:])
