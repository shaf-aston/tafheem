"""Request and reply types for routers/nahw_notes.py."""

from __future__ import annotations

from pydantic import BaseModel

from backend.models.common import Source


class NoteRole(BaseModel):
    """A kind of piece a note marks inside its own text, and so a kind a test can hide."""
    key: str
    ar: str
    en: str
    hint: str


class NoteBlock(BaseModel):
    """One piece of a topic's notes, in the order the page has it.

    One model for every kind rather than six, because a block is read as a
    whole: a table is a caption plus rows, a rule is the Arabic plus its
    English, and the kind says which of these the reader will find.
    """
    id: str
    kind: str                         # heading | rule | list | example | table | picture
    page: int                         # which of the teacher's pages it was read from
    ar: str | None = None
    en: str | None = None
    items: list[str] | None = None    # a list block's lines
    caption: str | None = None
    caption_en: str | None = None
    columns: list[str] | None = None
    rows: list[list[str]] | None = None
    answer_col: int | None = None     # which column a test asks for, given the others
    note_ar: str | None = None        # the small print under a table
    note_en: str | None = None
    labels: list[dict] | None = None  # an example's words and what each is called


class NoteTopic(BaseModel):
    """One topic of the teacher's notes, whole. `tamreen` names the exercises that test it."""
    id: str
    title: str
    arabic: str
    tamreen: list[str] = []
    pages: int                        # how many of the teacher's pages sit behind it
    blocks: list[NoteBlock]


class NoteLibrary(BaseModel):
    """Every topic, the roles a test can hide, and where the notes came from."""
    roles: list[NoteRole]
    topics: list[NoteTopic]
    source: Source
