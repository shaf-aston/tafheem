"""What every exercise has, whatever its type.

A type module adds only what its own type needs on top of this: `choose` adds
options, `reorder` adds the words to arrange, and the typed types add nothing
at all. Keeping the shared half here means a field added to every exercise is
added once, and so is the rule that checks it: a model is the one description
of an exercise, and a rule it breaks is a ValueError the registry turns into a
sentence.
"""
from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator


class TooFormal(BaseModel):
    """A correct but bookish answer, and why it is not what is being practised.

    Shown as a note beside the answer, never as a mistake: the learner who wrote
    it was not wrong, only formal.
    """
    item: str
    feedback: str

    @model_validator(mode="after")
    def _both_said(self):
        if not (self.item.strip() and self.feedback.strip()):
            raise ValueError("has a too_formal without both an item and its feedback")
        return self


class Exercise(BaseModel):
    """The half of an exercise that does not depend on its type."""
    # Written into the content by hand, never counted from position: a learner's
    # answers are stored against this, so an id that moves loses that history.
    id: str
    prompt: str
    answer: str
    # Every spelling that must be marked right, the transliteration included.
    # Harakat and the alef spellings are folded before comparing, so these are
    # for real alternatives rather than vowel marks.
    accepted: list[str] = []
    too_formal: TooFormal | None = None
    tip: str = ""

    @field_validator("id", "prompt", "answer", mode="before")
    @classmethod
    def _not_blank(cls, value, info):
        if not str(value or "").strip():
            raise ValueError(f"has no {info.field_name}")
        return value

    @model_validator(mode="after")
    def _accepted_answers(self):
        if not self.accepted:
            # Without it the only right answer is the one exact string, so every
            # other spelling of the same sentence is marked wrong.
            raise ValueError("has no accepted answers")
        if any(not one.strip() for one in self.accepted):
            raise ValueError("has an empty accepted answer, which would match a blank reply")
        if self.answer not in self.accepted:
            raise ValueError("does not list its own answer among the accepted ones")
        return self
