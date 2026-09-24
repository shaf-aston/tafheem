"""Worked tarkeeb examples, taken from the books that drew them.

The only thing that reads data/tarkeeb. One file per book under examples/, so
adding a book is adding a file, nothing here names any book. The topics books
are browsed by are shared, in topics.json, so two books teaching kana file their
examples under the same chip instead of each inventing its own name for it.

These are the honest half of the app's tarkeeb: the trees came off a printed
page, where a scholar decided every join. The Qur'an trees in tarkeeb.py are
worked out by rule from morphology tags and are only as good as those rules.
The same diagram draws both, and the source badge is what tells them apart.

Every file is checked when it is loaded rather than trusted, because a tree that
skips a word still draws, it just draws something untrue. A bad file is not
quietly dropped: it stops the app with what is wrong with it.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

TARKEEB_DIR = Path(__file__).parent.parent / "data" / "tarkeeb"
EXAMPLES_DIR = TARKEEB_DIR / "examples"


@lru_cache(maxsize=1)
def _topics() -> list[dict]:
    return json.loads((TARKEEB_DIR / "topics.json").read_text(encoding="utf-8"))["topics"]


def _words_under(node: dict, found: list[int]) -> list[int]:
    if node.get("children"):
        for child in node["children"]:
            _words_under(child, found)
    elif "word" in node:
        found.append(node["word"])
    return found


def _faults(example: dict, topics: set[str]) -> list[str]:
    """What is wrong with one example, in plain words. Empty means it is sound."""
    words = example.get("words") or []
    said = []

    if example.get("topic") not in topics:
        # Browsing is by topic, so an example with none would be unreachable.
        said.append(f"is filed under topic {example.get('topic')!r}, which topics.json does not declare")
    if not words:
        said.append("has no words")
    if "".join(words) != (example.get("sentence") or "").replace(" ", ""):
        said.append("its words do not spell out its sentence")

    covered = _words_under(example.get("tree") or {}, [])
    if sorted(covered) != list(range(len(words))):
        # The one failure that still looks fine on screen, so it is checked hardest.
        said.append(f"its tree covers words {sorted(covered)}, not all {len(words)} of them")
    return said


@lru_cache(maxsize=1)
def _books() -> list[dict]:
    books = []
    topics = {topic["key"] for topic in _topics()}
    for path in sorted(EXAMPLES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        book = data["book"]
        broken = {
            example["id"]: faults
            for example in data["examples"]
            if (faults := _faults(example, topics))
        }
        if broken:
            raise ValueError(f"{path.name}: " + "; ".join(
                f"{name} {' and '.join(why)}" for name, why in broken.items()
            ))
        books.append({**book, "examples": data["examples"]})
    return books


def topics() -> list[dict]:
    """The grammar topics every book files its examples under."""
    return _topics()


def books() -> list[dict]:
    """Each book, with the examples taken from it."""
    return _books()


def all_examples() -> list[dict]:
    """Every example from every book, each carrying the book it came from."""
    return [
        {**example, "book": book["title"]}
        for book in _books()
        for example in book["examples"]
    ]
