"""The worked sentences from Tasheel al-Nahw.

Only the sentence and its English are quoted. The tree beside each one in the
file is a diagram, not a quotation, and the Nahw tab already draws it; putting
its labels into a search index would match questions with pieces of a picture.

The book's own section number is the locator, which is how a reader would find
the page. It is kept here even though the cards stopped printing it, because
here it is the address of the quotation rather than decoration.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from backend.services.daleel.model import Passage
from backend.services.daleel.sources.roots import roots_in

_EXAMPLES = (
    Path(__file__).resolve().parents[3]
    / "data" / "tarkeeb" / "examples" / "tasheel-al-nahw.json"
)


class TasheelSource:
    """Every worked example the book contributes."""

    id = "tasheel"

    def passages(self) -> Iterable[Passage]:
        if not _EXAMPLES.exists():
            return

        book = json.loads(_EXAMPLES.read_text(encoding="utf-8"))
        for example in book.get("examples", []):
            if sentence := example.get("sentence", ""):
                yield Passage(
                    source="tasheel",
                    locator=example.get("ref") or example.get("id", ""),
                    arabic=sentence,
                    english=example.get("translation", ""),
                    roots=roots_in(example.get("words") or sentence.split()),
                )
