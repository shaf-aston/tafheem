"""Which modules make up the exercise types, and the one check that covers them all.

Imported by name, not discovered by scanning the folder, so the one line that
puts a type into the app can be found by searching for the type's name. Adding a
kind of practice is: one module beside this with its model and the rules that
model checks, one entry in MODULES, and one entry in the frontend registry
(components/colloquial/exercises/registry.js). Nothing else in the app changes.
"""
from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field, TypeAdapter, ValidationError

from backend.services.colloquial.exercises import choose, reorder, typed_answer

MODULES = (typed_answer, choose, reorder)

TYPES = frozenset(name for module in MODULES for name in module.TYPES)
# One model per exercise type, told apart by the `type` field, so every kind
# keeps its real shape in the response and in the docs instead of a loose dict.
AnyExercise = Annotated[Union[tuple(model for module in MODULES for model in module.MODELS)], Field(discriminator="type")]

_EXERCISE = TypeAdapter(AnyExercise)
_NO_TAG = ("union_tag_invalid", "union_tag_not_found")


def _said(error: dict, exercise: dict) -> str:
    """One validation error as a plain sentence about the exercise."""
    if error["type"] in _NO_TAG:
        return f"has type {exercise.get('type')!r}, which is not one of {sorted(TYPES)}"
    if error["type"] == "value_error":
        return str(error["ctx"]["error"])
    path = ".".join(str(step) for step in error["loc"][1:])  # the first step is the type tag
    return f"has no {path}" if error["type"] == "missing" else f"{path}: {error['msg']}"


def faults(exercise: dict) -> list[str]:
    """What is wrong with one exercise. Empty means sound.

    A rule that looks at the whole model runs only once every field is sound, so an
    exercise with a blank prompt reports that first and the rest after it is fixed.
    """
    try:
        _EXERCISE.validate_python(exercise)
    except ValidationError as raised:
        return [_said(error, exercise) for error in raised.errors()]
    return []
