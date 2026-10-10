"""The exercises the learner answers by typing.

One model for three types because the shape and the checking are the same: a
prompt, and a sentence typed into a box. What differs is only what the prompt
asks for (answer what was just said, fill the missing word, say an English
sentence in the dialect), which is content, not code.

The typing itself is why `accepted` matters, and why the browser folds harakat
and the alef spellings before comparing: a learner who spells a vowel
differently has not made a mistake.
"""
from __future__ import annotations

from typing import Literal

from backend.services.colloquial.exercises import base

# Every type this module answers for. The registry reads this.
TYPES = ("reply", "fill_blank", "translate_to_arabic")


class Typed(base.Exercise):
    type: Literal["reply", "fill_blank", "translate_to_arabic"]


MODELS = (Typed,)
