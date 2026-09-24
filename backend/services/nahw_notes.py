"""The teacher's Nahw theory notes, kept whole so they can be read or hidden.

The only thing that reads data/nahw_notes. One file per topic under topics/,
written by reading the teacher's own pages, which are rendered beside them in
images/ by scripts/render_note_pages.py so any line can be checked against the
handwriting.

A topic is a list of blocks in page order: a heading, a rule in prose, a table,
a worked example, or a picture where the page is a diagram no text would carry.
Inside a block's text the testable pieces are marked in place, `{{term|الحال}}`,
and roles.json says which kinds of piece exist. Nothing here blanks anything:
hiding is decided when the page is opened, so the stored notes stay the
reference and a change of taste is a setting, never a rebuild.

Checked when loaded, not trusted. A block of an unknown kind, a table row that
does not fit its columns, a marker naming a role nobody declared, or two blocks
with the same id would each be a page that reads wrongly, so they stop the app
and name the topic and block.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).parent.parent / "data" / "nahw_notes"
TOPICS_DIR = ROOT / "topics"
IMAGES_DIR = ROOT / "images"

KINDS = {"heading", "rule", "list", "example", "table", "picture"}
MARK = re.compile(r"\{\{([^{}|]+)\|([^{}]*)\}\}")
LOOSE_MARK = re.compile(r"\{\{|\}\}")


@lru_cache(maxsize=1)
def _roles() -> list[dict]:
    return json.loads((ROOT / "roles.json").read_text(encoding="utf-8"))["roles"]


def _texts(block: dict) -> list[str]:
    """Every string in a block that a reader sees, markers and all."""
    flat = [block.get(key) or "" for key in ("ar", "en", "caption", "caption_en", "note_ar", "note_en")]
    flat += block.get("items") or []
    flat += [cell for row in block.get("rows") or [] for cell in row]
    return [text for text in flat if text]


def _marker_faults(text: str, roles: set[str]) -> list[str]:
    said = []
    for role, marked in MARK.findall(text):
        if role not in roles:
            said.append(f"marks {role!r}, which roles.json does not declare")
        if not marked.strip():
            said.append(f"has an empty {role} marker")
    if len(LOOSE_MARK.findall(MARK.sub("", text))) > 0:
        said.append("has a broken marker: every one is {{role|text}}")
    return said


def _faults(block: dict, roles: set[str], pages: int) -> list[str]:
    """What is wrong with one block, in plain words. Empty means sound."""
    said = []
    kind = block.get("kind")
    if kind not in KINDS:
        said.append(f"is a {kind!r} block, which is not one of {sorted(KINDS)}")
    page = block.get("page")
    if not isinstance(page, int) or not 0 <= page < pages:
        said.append(f"names page {page}, and the topic has {pages} pictures")
    if kind == "table":
        columns = len(block.get("columns") or [])
        if not columns:
            said.append("is a table with no columns")
        bad = [i for i, row in enumerate(block.get("rows") or []) if len(row) != columns]
        if bad:
            said.append(f"has rows {bad} that do not fit its {columns} columns")
        answer = block.get("answer_col")
        if answer is not None and not 0 <= answer < columns:
            said.append(f"answers by column {answer}, which it does not have")
    elif kind == "picture":
        if not block.get("caption") and not block.get("caption_en"):
            said.append("is a picture with no caption saying what it shows")
    elif not _texts(block) and not block.get("labels"):
        said.append("has no text at all")
    for label in block.get("labels") or []:
        if not label.get("word") or not label.get("label"):
            said.append(f"has a label with no word or no name: {label}")
        elif LOOSE_MARK.search(label["word"] + label["label"]):
            # A label is itself what a test asks; a mark inside one shows as raw braces.
            said.append(f"marks inside its label for {label['word']!r}; labels take no markers")
    for text in _texts(block):
        said += _marker_faults(text, roles)
    return said


def _page_count(key: str) -> int:
    """How many `<key>-NN.png` pictures there are. Not a glob on `<key>-*`, which
    would also count a topic whose id only starts with this one's."""
    shape = re.compile(rf"{re.escape(key)}-\d+\.png")
    return sum(1 for path in IMAGES_DIR.iterdir() if shape.fullmatch(path.name))


def topic_faults(key: str, data: dict) -> str | None:
    """Everything wrong with one topic, as one line naming each block, or None.

    Public so the build script checks a topic before writing it, rather than
    the app finding out on the first page load.
    """
    roles = {role["key"] for role in _roles()}
    pages = _page_count(key)
    seen, broken = set(), {}
    for block in data["blocks"]:
        name = block.get("id", "?")
        faults = _faults(block, roles, pages)
        if name in seen:
            faults.append("shares its id with an earlier block")
        seen.add(name)
        if faults:
            broken[name] = faults
    if not broken:
        return None
    return f"{key}: " + "; ".join(f"block {name} {' and '.join(why)}" for name, why in broken.items())


@lru_cache(maxsize=1)
def _topics() -> list[dict]:
    # One broken topic stops the whole library on purpose: a page that reads
    # wrongly is worse than no page, and the message names the block to fix.
    topics = []
    for path in sorted(TOPICS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if problem := topic_faults(path.stem, data):
            raise ValueError(problem)
        topics.append({**data, "id": path.stem, "pages": _page_count(path.stem)})
    return topics


def roles() -> list[dict]:
    """The kinds of piece a note marks, and so the kinds a test can hide."""
    return _roles()


def topics() -> list[dict]:
    """Every topic's notes, whole."""
    return _topics()


def topic(key: str) -> dict | None:
    """One topic by its id, or None where there is no such topic."""
    return next((t for t in _topics() if t["id"] == key), None)


def page_picture(key: str, page: int) -> Path | None:
    """The teacher's own page behind a block, or None where there is none.

    The name is built here from the topic and the number, never from anything
    the caller sends, so no request can ask for a file outside images/.
    """
    if topic(key) is None:
        return None
    path = IMAGES_DIR / f"{key}-{page:02d}.png"
    return path if path.exists() else None
