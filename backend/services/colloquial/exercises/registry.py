"""Which module owns which exercise type.

Imported by name, not discovered by scanning the folder, so the one line that
puts a type into the app can be found by searching for the type's name. Adding a
kind of practice is: one module beside this, one entry in MODULES, and one
renderer in the frontend registry. Nothing else in the app changes.
"""
from __future__ import annotations

from backend.services.colloquial.exercises import base, choose, reorder, typed_answer

MODULES = (typed_answer, choose, reorder)

# type name -> the module that owns it.
OWNER = {name: module for module in MODULES for name in module.TYPES}
# type name -> its pydantic shape, for the API's discriminated union.
PAYLOADS = {name: shape for module in MODULES for name, shape in module.PAYLOADS.items()}
TYPES = frozenset(OWNER)


def faults(exercise: dict) -> list[str]:
    """What is wrong with one exercise: the shared half, then its own type's."""
    kind = exercise.get("type")
    owner = OWNER.get(kind)
    if owner is None:
        return [f"has type {kind!r}, which is not one of {sorted(TYPES)}"]
    return base.faults(exercise) + owner.faults(exercise)
