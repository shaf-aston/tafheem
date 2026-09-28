"""What every exercise has, whatever its type.

A type module adds only what its own type needs on top of this: `choose` adds
options, `reorder` adds the words to arrange, and the three typed types add
nothing at all. Keeping the shared half here means a field added to every
exercise is added once.
"""
from __future__ import annotations

from pydantic import BaseModel


class TooFormal(BaseModel):
    """A correct but bookish answer, and why it is not what is being practised.

    Shown as a note beside the answer, never as a mistake: the learner who wrote
    it was not wrong, only formal.
    """
    item: str
    feedback: str


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


def faults(exercise: dict) -> list[str]:
    """What is wrong with the shared half of one exercise. Empty means sound."""
    said = []
    for field in ("id", "prompt", "answer"):
        if not str(exercise.get(field) or "").strip():
            said.append(f"has no {field}")
    accepted = exercise.get("accepted")
    if not isinstance(accepted, list) or not accepted:
        # Without it the only right answer is the one exact string, so every
        # other spelling of the same sentence is marked wrong.
        said.append("has no accepted answers")
    elif any(not str(one or "").strip() for one in accepted):
        said.append("has an empty accepted answer, which would match a blank reply")
    elif exercise.get("answer") not in accepted:
        said.append("does not list its own answer among the accepted ones")
    formal = exercise.get("too_formal")
    if formal is not None and not (formal.get("item") and formal.get("feedback")):
        said.append("has a too_formal without both an item and its feedback")
    return said
