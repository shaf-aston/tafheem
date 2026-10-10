"""Request and reply types for routers/tamreen.py."""

from __future__ import annotations

from pydantic import BaseModel



class TamreenTag(BaseModel):
    """A grammar point the exercises are filed under. Shared by every exercise."""
    key: str
    ar: str
    en: str
    meaning: str


class TamreenPart(BaseModel):
    """One thing an example asks: choose, explain, translate, count the mistakes."""
    letter: str
    question: str
    options: list[str] | None = None
    rows: list[str] | None = None     # a grid asks the same options of several words
    answer: list[str] | dict[str, list[str]] | str
    by: str                           # "teacher" or "claude": who gave the answer
    labels: dict[str, str] | None = None  # what a placeholder ("A", "?3") points at in the picture
    picture: str | None = None        # a part with its own picture, e.g. a tarkeeb tree
    doubt: str | None = None          # a reviewer's reason to distrust the marking, kept in view


class TamreenRule(BaseModel):
    """A statement to complete, with the options the teacher marked right."""
    id: str
    question: str
    options: list[str]
    answer: list[str]
    picture: str | None = None
    tags: list[str]


class TamreenExample(BaseModel):
    """A picture question: the sentence as read off the picture, and its parts."""
    id: str
    section: str
    picture: str
    instruction: str
    sentence: str
    marked: list[dict] = []           # which words were underlined, and how
    doubt: str | None = None          # what the readers could not settle from the picture
    parts: list[TamreenPart]
    tags: list[str]


class TamreenExercise(BaseModel):
    key: str
    title: str
    form: str
    harvested: str
    rules: list[TamreenRule]
    examples: list[TamreenExample]


class TamreenLibrary(BaseModel):
    """The tags beside the exercises, and a count per tag so a gap is a number."""
    tags: list[TamreenTag]
    exercises: list[TamreenExercise]
    coverage: dict[str, int]
