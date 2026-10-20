"""The three exercises the learner answers by typing.

One module for three types because the shape and the checking are the same: a
prompt, and a sentence typed into a box. What differs is only what the prompt
asks for, which is content, not code. Splitting them into three files would be
three identical files.

The typing itself is why `accepted` matters, and why the browser folds harakat
and the alef spellings before comparing: a learner who spells a vowel
differently has not made a mistake.
"""
from __future__ import annotations

from typing import Literal

from backend.services.colloquial.exercises import base

# Every type this module answers for. The registry reads this.
TYPES = ("reply", "fill_blank", "translate_to_arabic")


class Reply(base.Exercise):
    """Answer what was just said, the way a person would."""
    type: Literal["reply"]


class FillBlank(base.Exercise):
    """Put the missing word into the sentence."""
    type: Literal["fill_blank"]


class TranslateToArabic(base.Exercise):
    """Say an English sentence in the dialect."""
    type: Literal["translate_to_arabic"]


PAYLOADS = {"reply": Reply, "fill_blank": FillBlank, "translate_to_arabic": TranslateToArabic}


def faults(exercise: dict) -> list[str]:
    """Nothing beyond the shared half: a typed answer needs no extra field."""
    return []
