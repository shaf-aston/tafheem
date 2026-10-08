"""What the colloquial routes return.

Here rather than in models/schemas.py because an exercise's shape is defined by
its own type module, and the union below is assembled from the registry: a new
exercise type must not mean editing a shared schemas file, or the promise that a
type is one file and one registry line is not true.
"""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from backend.models.schemas import Source
from backend.services.colloquial.exercises.registry import PAYLOADS

# One model per exercise type, told apart by the `type` field, so every kind
# keeps its real shape in the response and in the docs instead of a loose dict.
AnyExercise = Annotated[Union[tuple(PAYLOADS.values())], Field(discriminator="type")]


class Word(BaseModel):
    """Anything said: the Arabic, how to say it, what it means."""
    arabic: str
    transliteration: str
    english: str


class Phrase(Word):
    # The spine slot a lesson phrase fills, the same in every dialect; empty on
    # replies and dialogue lines, which fill no slot.
    slot: str = ""
    reply: "Phrase | None" = None
    # A short English noun phrase a picture is looked up from. Missing means the
    # phrase has nothing to show, and no picture is invented for it.
    search_term: str = ""
    # The picture file, once one has been fetched and approved by hand.
    image: str = ""


class DialogueLine(Phrase):
    speaker: str


class Drill(BaseModel):
    """A question and its natural answer, asked one after the other."""
    pair: Phrase
    response: Phrase


class VocabWord(Word):
    """A word of a topic's list: its meaning from words.json, its Arabic from the dialect's."""
    id: str
    category: str = ""


class ComingLesson(BaseModel):
    """A spine lesson this dialect has not begun: its title, shown as coming."""
    lesson: str
    title: str
    section: str | None = None
    written: Literal[False]


class Lesson(BaseModel):
    lesson: str
    title: str
    # A heading shared with its neighbours, only in units long enough to need one.
    section: str | None = None
    written: Literal[True] = True
    phrases: list[Phrase]
    dialogue: list[DialogueLine]
    de_book: list[Drill] = []
    vocabulary: list[VocabWord] = []
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
    lessons: list[Lesson | ComingLesson]
    challenge: Challenge
    source: Source


class Cover(BaseModel):
    """The phrase a unit's card opens with: said aloud, with its picture."""
    arabic: str
    english: str
    image: str


class UnitCard(BaseModel):
    """A unit as the list shows it, before it is opened."""
    unit: str
    title: str
    # False while the dialect has not written this spine unit yet: shown as coming.
    written: bool
    lessons: list[dict]
    # None while no phrase in the unit has a picture: the card shows its title only.
    cover: Cover | None = None


class DialectCard(BaseModel):
    key: str
    label: str
    arabic: str
    where: str
    units: list[UnitCard]


class Catalogue(BaseModel):
    dialects: list[DialectCard]
    source: Source


class Said(BaseModel):
    slot: str
    arabic: str
    transliteration: str


class DialectSays(BaseModel):
    key: str
    label: str
    # None while this dialect has not written the unit: shown as coming.
    phrases: list[Said] | None


class Compare(BaseModel):
    """One lesson's phrases as every dialect says them."""
    unit: str
    lesson: str
    dialects: list[DialectSays]
