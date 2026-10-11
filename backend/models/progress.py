"""Request and reply types for routers/progress.py."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, field_validator



# ── Progress: what a learner has answered ────────────────────────────────────
# Trust boundary as everywhere else in this file: the ids are a module's own
# short names, not prose, so they are capped tightly. `user` is deliberately
# absent, the server decides who is answering, never the page.
class AttemptIn(BaseModel):
    """One answer, as the page reports it."""
    module: str = Field(min_length=1, max_length=32)
    """Which panel asked: 'quiz' today, another tab later."""
    item: str = Field(min_length=1, max_length=200)
    """That panel's own stable id for the thing asked. The quiz sends meaningKey."""
    correct: bool
    ms: int | None = Field(default=None, ge=0, le=86_400_000)
    """How long the answer took. A day is already absurd; past that it is a bug
    or a clock change, and storing it would poison every average made from it."""
    context: dict | None = None
    """Small free-form note about the round it came from, kept for later
    questions nobody has asked yet ("am I worse on Arabic to English?"). Capped
    below, because an unbounded blob is a write endpoint's easiest abuse."""

    @field_validator("context")
    @classmethod
    def _small_enough(cls, value: dict | None) -> dict | None:
        if value is not None and len(json.dumps(value)) > 500:
            raise ValueError("context must serialise to 500 characters or fewer")
        return value


class AttemptSaved(BaseModel):
    saved: bool = True
    id: int


class FeedbackIn(BaseModel):
    """A note from the page about something that looks wrong."""
    module: str = Field(min_length=1, max_length=32)
    item: str | None = Field(default=None, max_length=200)
    """The question it is about, when there is one."""
    message: str = Field(min_length=1, max_length=2000)


class Forgotten(BaseModel):
    """How many answers a wipe removed."""

    deleted: int


class PassphraseIn(BaseModel):
    """Signing in to the username in the profile header."""

    passphrase: str = Field(max_length=256)
    """Capped: every sign-in hashes it many thousand times."""


class ProfileIn(PassphraseIn):
    """Signing up the username in the profile header."""

    keep: bool = False
    """Move the answers given before names existed onto this name."""


class Shelf(BaseModel):
    """Everything the page keeps for one account: its own key -> stored text."""

    data: dict[str, str]


class ProfileSaved(BaseModel):
    """The name as the server spells it, how many unnamed answers moved onto it, and the
    sign-in key every later call sends."""

    name: str
    moved: int
    key: str


class Account(BaseModel):
    """The profile page: who, since when, and how many answers given."""

    name: str
    joined: str
    answers: int
    public: bool


class AccountNames(BaseModel):
    """Every username, for the beta log-in list."""

    names: list[str]


class CircleIn(BaseModel):
    """A new circle: its name, one of the configured kinds, and optionally the circle it sits inside."""

    name: str = Field(min_length=1, max_length=200)
    kind: str = Field(min_length=1, max_length=32)
    parent: int | None = None


class ParentIn(BaseModel):
    """The circle to move a circle inside, or None to stand it on its own."""

    parent: int | None = None


class InviteIn(BaseModel):
    """A username to invite, as typed, and the role on offer."""

    member: str = Field(min_length=1, max_length=200)
    role: str = "member"


class RoleIn(BaseModel):
    role: str


class PublicIn(BaseModel):
    """Whether the account shows in the global ranking."""

    public: bool


class CircleItem(BaseModel):
    """A circle in my list: my role in it, and (while status is "invited") who invited me."""

    id: int
    name: str
    kind: str
    parent: int | None
    role: str
    status: str
    invitedBy: str


class CircleList(BaseModel):
    """Every circle I am in or invited to, and the kinds a new one may take."""

    kinds: list[str]
    circles: list[CircleItem]


class CircleMember(BaseModel):
    """A person in a circle; `seeable` says whether the asker may open their overview."""

    name: str
    role: str
    status: str
    seeable: bool


class CircleInside(BaseModel):
    id: int
    name: str
    kind: str


class CircleDetail(BaseModel):
    """One circle. `role` is the asker's own (None for an admin of a circle above)."""

    id: int
    name: str
    kind: str
    parent: int | None
    role: str | None
    members: list[CircleMember]
    inside: list[CircleInside]


class LeaderRow(BaseModel):
    name: str
    learnt: int
    answers: int
    rank: int


class Leaderboard(BaseModel):
    """The top accounts by words learnt, and where the asker stands (None for a guest)."""

    rows: list[LeaderRow]
    you: LeaderRow | None


class ItemStats(BaseModel):
    """One item's whole record. `avgMs` is None when nothing was timed honestly."""
    item: str
    attempts: int
    wrong: int
    avgMs: int | None = None
    due: bool = False
    known: bool = False
    dueAt: str | None = None
    words: list[str] = []
    """The words of this meaning answered right, as the quiz printed them; ''
    for right answers saved before the word was."""


class ProgressSummary(BaseModel):
    module: str
    items: list[ItemStats] = []


class ModuleOverview(BaseModel):
    module: str
    attempts: int
    correct: int
    learnt: int
    lastAt: str


class Overview(BaseModel):
    """One learner across every module: each one, the totals, and days in a row."""

    modules: list[ModuleOverview]
    attempts: int
    correct: int
    learnt: int
    streak: int


class ReviewList(BaseModel):
    module: str
    items: list[str] = []
