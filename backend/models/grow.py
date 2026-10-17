"""Request and reply types for routers/grow.py."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class GrowRuling(BaseModel):
    """A scholar's own words on one step, quoted, never paraphrased.

    `source` names the book in data/grow/sources.json; the router fills in
    `book`, `author` and `known_as` from it. `arabic` is copied from the book
    exactly (tests/test_grow.py holds it to the book's text), and `where` is
    the chapter it is in, so the reader can find it; the app adds no ruling
    of its own."""
    source: str
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


Category = Literal["fard", "wajib", "sunnah", "mustahabb", "makruh", "breaks", "condition"]
School = Literal["hanafi", "maliki", "shafii", "hanbali"]


class ReciteCard(GrowStep):
    """A step to say, as a card: `arabic` or `ayahs`, checked by ear."""
    kind: Literal["recite"]


class ActionCard(GrowStep):
    """A step to do, as a card: `instruction`, tapped Done."""
    kind: Literal["action"]


class RulingCard(BaseModel):
    """One ruling of one school: what it is (`category`) in the book's own words
    (`quote`), and from Level 2 the reason a later book gives (`why`). `order`
    is its place in a sequence, for exercises that ask for one."""
    kind: Literal["ruling"]
    id: str
    title: str
    category: Category
    quote: GrowRuling
    why: GrowRuling | None = None
    order: int | None = None


class Position(BaseModel):
    """What one school says, in its own book's words."""
    school: School
    category: Category
    quote: GrowRuling


class DifferenceCard(BaseModel):
    """One question the schools answer differently: at least two positions."""
    kind: Literal["difference"]
    id: str
    title: str
    positions: list[Position]


# One shape for everything on a world's map, told apart by `kind`.
Card = Annotated[ReciteCard | ActionCard | RulingCard | DifferenceCard, Field(discriminator="kind")]


class GrowLevel(BaseModel):
    """A level of a world's map, mirroring the page's grow.json tiers until the
    page reads levels from here. `proposed` are topics planned for it, shown locked."""
    id: str
    title: str
    proposed: list[str] = []


class GrowUnit(BaseModel):
    """One file of cards under a world's folder, sitting in one level."""
    level: str
    title: str
    arabic: str
    cards: list[Card]


class GrowWorld(BaseModel):
    """A world as /api/grow/worlds/{id} serves it: its levels, its recitation
    paths (the same ones /api/grow/paths serves) and its units of cards."""
    id: str
    levels: list[GrowLevel]
    paths: list[GrowPath]
    units: list[GrowUnit]
