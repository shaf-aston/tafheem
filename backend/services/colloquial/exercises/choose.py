"""Pick one of several offered answers.

One type covers picking a sentence and picking a picture, because the learner
does the same thing either way: an option is a piece of text, or a picture with
its own word under it. A second type for pictures would be the same code twice
with a different renderer.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from backend.services.colloquial.exercises import base
from backend.services.colloquial.knobs import knob

TYPES = ("choose",)


class PictureOption(BaseModel):
    """A picture to pick, and the word it shows.

    `image` is a file under the dialect's images folder, served by
    /api/colloquial/image. A missing file hides the picture and leaves the label,
    so a lesson never breaks on one absent photo.
    """
    label: str
    image: str


class Choose(base.Exercise):
    type: Literal["choose"]
    # Plain strings are text options; the object form is a picture option. Both
    # in one list because an exercise never mixes them, so the list is one or
    # the other and the renderer asks which once.
    options: list[str | PictureOption]

    def rules(self) -> list[str]:
        said = super().rules()
        least = knob("least-options")
        if len(self.options) < least:
            return said + [f"offers fewer than {least} options"]
        labels = [one.label if isinstance(one, PictureOption) else one for one in self.options]
        if any(not label.strip() for label in labels):
            said.append("has an empty option, which cannot be chosen")
        for dup in sorted({label for label in labels if labels.count(label) > 1}):
            # Two identical options make one of them wrong for no reason a learner
            # can see.
            said.append(f"offers the option {dup!r} twice")
        if self.answer not in labels:
            said.append("has an answer that is not one of its options")
        return said


MODELS = (Choose,)
