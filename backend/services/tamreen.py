"""The Tamreen exercises: a teacher's Google Form quizzes, kept as a library.

The only thing that reads data/tamreen. One file per exercise under
exercises/, built by scripts/build_tamreen.py; the tags every question is
filed under live in tags.json and are shared, so "is the واو حالية covered?"
is one question over every exercise, and nothing here names any exercise.

Each exercise is two lists. "rules" are the statements the form opened with,
with the options the teacher marked right. "examples" are the picture
questions: the sentence read off the picture, which words were underlined,
the parts asked (choose, explain, translate) and the answer to each. Every
answer says who gave it: "teacher" when the form marked it or the teacher
wrote it, "claude" when it was written here because the form kept none.

Checked when loaded, not trusted. A question filed under a tag tags.json does
not declare would be unreachable; an example with no sentence would show a
picture and nothing to read; a part with no answer teaches nothing. Any of
those stops the app and names the question.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).parent.parent / "data" / "tamreen"
EXERCISES_DIR = ROOT / "exercises"
IMAGES_DIR = ROOT / "images"


@lru_cache(maxsize=1)
def _tags() -> list[dict]:
    return json.loads((ROOT / "tags.json").read_text(encoding="utf-8"))["tags"]


def _faults(question: dict, tags: set[str], pictures: set[str]) -> list[str]:
    """What is wrong with one rule or example, in plain words. Empty means sound."""
    said = []
    unknown = [t for t in question.get("tags") or [] if t not in tags]
    if not question.get("tags"):
        said.append("has no tags, so no search would find it")
    elif unknown:
        said.append(f"is tagged {unknown}, which tags.json does not declare")
    if question.get("picture") and question["picture"] not in pictures:
        said.append(f"names picture {question['picture']}, which is not in images/")
    if "parts" in question:
        if not question.get("sentence"):
            said.append("has no sentence read off its picture")
        for part in question["parts"]:
            if part.get("answer") in (None, "", [], {}):
                said.append(f"part {part['letter']} has no answer")
            if not part.get("question"):
                said.append(f"part {part['letter']} has no question")
    elif not question.get("answer"):
        said.append("has no answer")
    return said


@lru_cache(maxsize=1)
def _exercises() -> list[dict]:
    tags = {tag["key"] for tag in _tags()}
    pictures = {path.name for path in IMAGES_DIR.glob("*.png")}
    exercises = []
    for path in sorted(EXERCISES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        broken = {
            q["id"]: faults
            for q in data["rules"] + data["examples"]
            if (faults := _faults(q, tags, pictures))
        }
        if broken:
            raise ValueError(f"{path.name}: " + "; ".join(
                f"{name} {' and '.join(why)}" for name, why in broken.items()
            ))
        exercises.append({"key": path.stem, **data})
    return exercises


def tags() -> list[dict]:
    """Every grammar point the library is filed under."""
    return _tags()


def exercises(tag: str | None = None) -> list[dict]:
    """Every exercise; with a tag, only the questions filed under it, exercises with none left out."""
    if tag is None:
        return _exercises()
    kept = []
    for exercise in _exercises():
        rules = [q for q in exercise["rules"] if tag in q["tags"]]
        examples = [q for q in exercise["examples"] if tag in q["tags"]]
        if rules or examples:
            kept.append({**exercise, "rules": rules, "examples": examples})
    return kept


def coverage() -> dict[str, int]:
    """How many questions each tag has, zero included, so a gap is a number and not an absence."""
    counts = {tag["key"]: 0 for tag in _tags()}
    for exercise in _exercises():
        for q in exercise["rules"] + exercise["examples"]:
            for t in q["tags"]:
                counts[t] += 1
    return counts
