"""What the colloquial routes return.

Here rather than in models/schemas.py because an exercise's shape is defined by
its own type module, and the union below is assembled from the registry: a new
exercise type must not mean editing a shared schemas file, or the promise that a
type is one file and one registry line is not true.
"""
from __future__ import annotations

from typing import Annotated, Union

from pydantic import BaseModel, Field

from backend.models.schemas import Source
from backend.services.colloquial.exercises.registry import PAYLOADS

# One model per exercise type, told apart by the `type` field, so every kind
# keeps its real shape in the response and in the docs instead of a loose dict.
AnyExercise = Annotated[Union[tuple(PAYLOADS.values())], Field(discriminator="type")]


class Phrase(BaseModel):
    arabic: str
    transliteration: str
    english: str
    reply: "Phrase | None" = None
    # A short English noun phrase a picture is looked up from. Missing means the
    # phrase has nothing to show, and no picture is invented for it.
    search_term: str = ""
    # The picture file, once one has been fetched and approved by hand.
    image: str = ""
    # Filled in by the loader from attribution.json, never authored in a unit.
    credit: str = ""
    credit_url: str = ""


class DialogueLine(Phrase):
    speaker: str


class Drill(BaseModel):
    """A question and its natural answer, asked one after the other."""
    pair: Phrase
    response: Phrase


class Lesson(BaseModel):
    lesson: str
    title: str
    phrases: list[Phrase]
    dialogue: list[DialogueLine]
    de_book: list[Drill] = []
    culture: str
    exercises: list[AnyExercise]


class Challenge(BaseModel):
    """The unit's own ending: write a conversation. Not graded."""
    title: str
    instructions: str
    required_elements: list[str]
    model: dict


class Unit(BaseModel):
    unit: str
    title: str
    dialect: str
    dialect_key: str
    # The English letters and digits standing for sounds English has no letter
    # for, so the spelling is never a mystery.
    transliteration_key: dict[str, str]
    lessons: list[Lesson]
    challenge: Challenge
    source: Source


class UnitCard(BaseModel):
    """A unit as the list shows it, before it is opened."""
    unit: str
    title: str
    lessons: list[dict]


class DialectCard(BaseModel):
    key: str
    label: str
    arabic: str
    where: str
    units: list[UnitCard]


class Catalogue(BaseModel):
    dialects: list[DialectCard]
    source: Source
