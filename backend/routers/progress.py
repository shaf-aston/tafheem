"""What a learner has answered, and what it says about them.

Thin on purpose: every rule about what counts as still-to-review, and every
piece of SQL, lives in services/progress_store.py. This file only turns a
request into a call and the answer into a response model.

Nothing here knows what an item is. The quiz sends the id of a meaning; the
tags that say what kind of word that is live in the page's own word list, which
is where the "what do I keep getting wrong" reading is made.
"""
from __future__ import annotations

import json
from contextlib import contextmanager

from fastapi import APIRouter, HTTPException, Query

from backend.config import get_settings
from backend.models.progress import (
    Account,
    AccountNames,
    AttemptIn,
    AttemptSaved,
    CircleDetail,
    CircleIn,
    CircleItem,
    CircleList,
    FeedbackIn,
    Forgotten,
    InviteIn,
    ItemStats,
    Leaderboard,
    ModuleOverview,
    Overview,
    ParentIn,
    ProfileIn,
    ProfileSaved,
    ProgressSummary,
    PublicIn,
    ReviewList,
    RoleIn,
    Shelf,
)
from backend.identity import GUEST, NAMED, TYPED, USER
from backend.services import progress_store
from backend.services.profile import clean_name

router = APIRouter(prefix="/api/progress", tags=["progress"])

_MODULE = Query("quiz", min_length=1, max_length=32, description="Which panel is asking")


@router.post("/attempts", response_model=AttemptSaved)
async def record_attempt(attempt: AttemptIn, user: str = USER) -> AttemptSaved:
    """File one answer, right or wrong."""
    row_id = progress_store.record(
        module=attempt.module,
        item=attempt.item,
        correct=attempt.correct,
        ms=attempt.ms,
        context=attempt.context,
        user=user,
    )
    return AttemptSaved(id=row_id)


@router.post("/feedback", response_model=AttemptSaved)
async def leave_feedback(note: FeedbackIn, user: str = USER) -> AttemptSaved:
    """File a report about a question that looks wrong."""
    message = note.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="message is empty")
    return AttemptSaved(id=progress_store.leave_feedback(
        module=note.module, item=note.item, message=message, user=user,
    ))


@router.delete("", response_model=Forgotten)
async def forget_progress(user: str = USER) -> Forgotten:
    """Delete every answer and the shelf of this name. The Settings wipe calls it."""
    return Forgotten(deleted=progress_store.forget(user))


@router.get("/summary", response_model=ProgressSummary)
def get_summary(module: str = _MODULE, user: str = USER) -> ProgressSummary:
    """Every item answered in this module, with its record and whether it is due or known."""
    return ProgressSummary(
        module=module,
        items=[
            ItemStats(
                item=row["item"],
                attempts=row["attempts"],
                wrong=row["wrong"],
                avgMs=row["avg_ms"],
                due=row["due"],
                known=row["known"],
                dueAt=row["due_at"],
                words=row["words"],
            )
            for row in progress_store.summary(module, user)
        ],
    )


@router.get("/overview", response_model=Overview)
def get_overview(user: str = USER) -> Overview:
    """Every module this learner answered in, with totals and the streak of days."""
    return _overview(progress_store.overview(user))


def _overview(found: dict) -> Overview:
    modules = [ModuleOverview(**{**row, "lastAt": row["last_at"]}) for row in found.pop("modules")]
    return Overview(modules=modules, **found)


@router.get("/review", response_model=ReviewList)
def get_review(module: str = _MODULE, user: str = USER) -> ReviewList:
    """Items due for review now, earliest first."""
    return ReviewList(module=module, items=progress_store.review_items(module, user))


@router.post("/signup", response_model=ProfileSaved)
async def sign_up(body: ProfileIn, user: str = TYPED) -> ProfileSaved:
    """Take a free username and hand back its one spelling, which the page keeps.

    `keep` moves this device's unnamed answers onto it.
    """
    _typed_a_name(user)
    if not progress_store.sign_up(user):
        raise HTTPException(status_code=409, detail="That username is taken")
    return ProfileSaved(name=user, moved=progress_store.claim_local(user) if body.keep else 0)


@router.post("/login", response_model=ProfileSaved)
async def log_in(user: str = TYPED) -> ProfileSaved:
    """Check a username was signed up and hand back its one spelling."""
    _typed_a_name(user)
    if not progress_store.has_account(user):
        raise HTTPException(status_code=404, detail="No account with that username")
    return ProfileSaved(name=user, moved=0)


@router.get("/account", response_model=Account)
def get_account(user: str = NAMED) -> Account:
    """The profile page's facts about this username."""
    return Account(**progress_store.account(user))


@router.delete("/account", response_model=Forgotten)
async def delete_account(user: str = NAMED) -> Forgotten:
    """Delete this username, every answer it gave and its shelf; the name is free again."""
    return Forgotten(deleted=progress_store.delete_account(user))


@router.get("/saved", response_model=Shelf)
def get_shelf(user: str = NAMED) -> Shelf:
    """What the page kept for this account, so it follows the name to another device."""
    return Shelf(data=progress_store.shelf(user))


@router.put("/saved", response_model=Shelf)
async def put_shelf(body: Shelf, user: str = NAMED) -> Shelf:
    """Replace this account's shelf whole with what the page holds now."""
    if len(json.dumps(body.data, ensure_ascii=False).encode()) > get_settings().saved_max_bytes:
        raise HTTPException(status_code=413, detail="Too much saved for one account")
    progress_store.keep_shelf(user, body.data)
    return body


@router.put("/account/public", response_model=Account)
def put_public(body: PublicIn, user: str = NAMED) -> Account:
    """Show in, or hide from, the global ranking."""
    progress_store.set_public(user, body.public)
    return Account(**progress_store.account(user))


@router.get("/leaderboard", response_model=Leaderboard)
def get_leaderboard(module: str = _MODULE, circle: int | None = None, user: str = USER) -> Leaderboard:
    """A circle's joined members by words learnt, or the global top accounts plus the asker's own place."""
    if circle is not None:
        with _refused():
            return Leaderboard(rows=progress_store.circle_ranking(circle, module, user), you=None)
    rows, you = progress_store.leaderboard(module, user)
    return Leaderboard(rows=rows[: get_settings().leaderboard_size], you=you)


@router.get("/accounts", response_model=AccountNames)
def list_accounts() -> AccountNames:
    """Every username, for the log-in box while in beta; not found once that is switched off."""
    if not get_settings().beta_list_accounts:
        raise HTTPException(status_code=404, detail="Not found")
    return AccountNames(names=progress_store.account_names())


@contextmanager
def _refused():
    """The store's rules as the answers a page expects: unknown 404, not allowed 403, not valid 422."""
    try:
        yield
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from None
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


def _circles(user: str) -> CircleList:
    mine = [CircleItem(**{**row, "invitedBy": row.pop("invited_by")}) for row in progress_store.my_circles(user)]
    return CircleList(kinds=progress_store.circle_kinds(), circles=mine)


def _member_name(typed: str) -> str:
    with _refused():
        return clean_name(typed)


@router.get("/circles", response_model=CircleList)
def list_circles(user: str = NAMED) -> CircleList:
    """Every circle I am in, and every invite waiting for me."""
    return _circles(user)


@router.post("/circles", response_model=CircleDetail)
def create_circle(body: CircleIn, user: str = NAMED) -> CircleDetail:
    """Make a circle, with me as its admin."""
    with _refused():
        return CircleDetail(**progress_store.circle_detail(
            progress_store.create_circle(user, body.name, body.kind, body.parent), user))


@router.get("/circles/{circle}", response_model=CircleDetail)
def get_circle(circle: int, user: str = NAMED) -> CircleDetail:
    """One circle and the people the asker may see in it."""
    with _refused():
        return CircleDetail(**progress_store.circle_detail(circle, user))


@router.delete("/circles/{circle}", response_model=CircleList)
def delete_circle(circle: int, user: str = NAMED) -> CircleList:
    with _refused():
        progress_store.delete_circle(circle, user)
    return _circles(user)


@router.post("/circles/{circle}/members", response_model=CircleDetail)
def invite_member(circle: int, body: InviteIn, user: str = NAMED) -> CircleDetail:
    """An admin invites an existing username; they see nothing until they accept."""
    member = _member_name(body.member)
    with _refused():
        progress_store.invite(circle, user, member, body.role)
        return CircleDetail(**progress_store.circle_detail(circle, user))


@router.post("/circles/{circle}/accept", response_model=CircleList)
def accept_invite(circle: int, user: str = NAMED) -> CircleList:
    with _refused():
        progress_store.accept(circle, user)
    return _circles(user)


@router.post("/circles/{circle}/decline", response_model=CircleList)
def decline_invite(circle: int, user: str = NAMED) -> CircleList:
    with _refused():
        progress_store.decline(circle, user)
    return _circles(user)


@router.post("/circles/{circle}/leave", response_model=CircleList)
def leave_circle(circle: int, user: str = NAMED) -> CircleList:
    with _refused():
        progress_store.leave(circle, user)
    return _circles(user)


@router.delete("/circles/{circle}/members/{member}", response_model=CircleDetail)
def remove_member(circle: int, member: str, user: str = NAMED) -> CircleDetail:
    name = _member_name(member)
    with _refused():
        progress_store.remove(circle, user, name)
        return CircleDetail(**progress_store.circle_detail(circle, user))


@router.put("/circles/{circle}/members/{member}", response_model=CircleDetail)
def set_member_role(circle: int, member: str, body: RoleIn, user: str = NAMED) -> CircleDetail:
    name = _member_name(member)
    with _refused():
        progress_store.set_role(circle, user, name, body.role)
        return CircleDetail(**progress_store.circle_detail(circle, user))


@router.put("/circles/{circle}/parent", response_model=CircleDetail)
def set_circle_parent(circle: int, body: ParentIn, user: str = NAMED) -> CircleDetail:
    """An admin moves a circle inside another circle they admin, or out to stand on its own."""
    with _refused():
        progress_store.move_circle(circle, user, body.parent)
        return CircleDetail(**progress_store.circle_detail(circle, user))


@router.get("/circles/{circle}/members/{member}/overview", response_model=Overview)
def get_member_overview(circle: int, member: str, user: str = NAMED) -> Overview:
    """A joined member's overview, for whoever the circles' rules let see it."""
    name = _member_name(member)
    with _refused():
        return _overview(progress_store.member_overview(circle, user, name))


def _typed_a_name(user: str) -> None:
    """Sign-up and log-in need a name typed; the account check would be circular."""
    if user == GUEST:
        raise HTTPException(status_code=422, detail="Type a username")
