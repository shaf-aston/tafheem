"""Build the sentence from a bank of pieces.

`words` holds the pieces when they are whole segments, such as "لو سمحت" as one
tile. Left out, the pieces are the words of `answer` itself, which is the usual
case and saves writing the same sentence twice in the content.

How big a piece is, is a property of the data. That is why arranging words and
arranging phrases are one type and not two.
"""
from __future__ import annotations

from typing import Literal

from backend.services.colloquial.exercises import base

TYPES = ("reorder",)


class Reorder(base.Exercise):
    type: Literal["reorder"]
    # Empty means: use the words of the answer. Sent as given rather than
    # shuffled here, because the browser shuffles per attempt and a fixed order
    # from the server would be the same puzzle every time.
    words: list[str] = []


PAYLOADS = {"reorder": Reorder}


def faults(exercise: dict) -> list[str]:
    words = exercise.get("words") or []
    if not isinstance(words, list):
        return ["has words that are not a list"]
    if not words:
        # Derived from the answer instead, so the answer must have pieces to
        # take apart. One word is not something to put in order.
        if len(str(exercise.get("answer") or "").split()) < 2:
            return ["has one word and no word bank, so there is nothing to arrange"]
        return []
    said = []
    if any(not str(word or "").strip() for word in words):
        said.append("has an empty tile in its word bank")
    missing = [word for word in words if word not in str(exercise.get("answer") or "")]
    if missing:
        # A tile that appears nowhere in the answer can only ever be wrong, and
        # the learner is left holding it with the sentence apparently finished.
        said.append(f"offers tiles that are not in its answer: {', '.join(missing)}")
    return said
