"""Request and reply types for routers/grow.py."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel



class GrowRuling(BaseModel):
    """A scholar's own words on one step, quoted, never paraphrased.

    `arabic` is copied from the book exactly (tests/test_grow.py holds it to
    the book's text), and `where` is the chapter it is in, so the reader can
    find it; the app adds no ruling of its own."""
    book: str
    author: str
    known_as: str  # the name he goes by, for "What al-Quduri says"
    where: str
    arabic: str
    english: str = ""


class GrowStep(BaseModel):
    """One thing to learn. To say: either `arabic`, a phrase shown and checked
    as written, or `ayahs`, as "1:2", checked the way the Qur'an tab checks. Or,
    with `kind` "action", a posture to take: `instruction` is shown and the
    reader taps Done, since the ear cannot hear it."""
    id: str
    title: str
    kind: Literal["action"] | None = None
    instruction: str = ""
    arabic: str = ""
    ayahs: list[str] = []
    meaning: str = ""
    ruling: GrowRuling | None = None


class GrowGroup(BaseModel):
    """One node on the map: a few steps that belong together. `steps` are step
    ids, and `icon` names the picture the page draws for it (the figures in
    the page's grow/icons.jsx; one it lacks would draw nothing). `alongside`
    marks a group that runs through its whole path (wudu's good manners), which
    the map draws beside the path instead of after the group before it."""
    id: str
    title: str
    arabic: str = ""
    icon: Literal["stand", "bow", "prostrate", "sit", "book", "lock", "drop"]
    steps: list[str]
    alongside: bool = False


class GrowPath(BaseModel):
    """`tier` is one of the ids in the page's grow.json, so a new tier of
    learning is data: a path that names it."""
    id: str
    tier: str
    title: str
    arabic: str
    groups: list[GrowGroup]
    steps: list[GrowStep]
