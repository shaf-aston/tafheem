"""What a learner has answered, and what it says about them.

Thin on purpose: every rule about what counts as still-to-review, and every
piece of SQL, lives in services/progress_store.py. This file only turns a
request into a call and the answer into a response model.

Nothing here knows what an item is. The quiz sends the id of a meaning; the
tags that say what kind of word that is live in the page's own word list, which
is where the "what do I keep getting wrong" reading is made.
"""
from __future__ import annotations

from urllib.parse import unquote

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from backend.config import get_settings
from backend.models.schemas import (
    Account,
    AttemptIn,
    AttemptSaved,
    FeedbackIn,
    Forgotten,
    ItemStats,
    Leaderboard,
    ProfileIn,
    ProfileSaved,
    ProgressSummary,
    ReviewList,
)
from backend.services import progress_store
from backend.services.profile import clean_name

router = APIRouter(prefix="/api/progress", tags=["progress"])

# Who is answering: the username the page sends, percent-encoded because a
# header cannot carry Arabic. Sign-up and log-in are by username only, no
# password; that is agreed. No header is the shared guest record.
UNNAMED = "local"


def typed_name(x_tafheem_profile: str | None = Header(None)) -> str:
    """The cleaned name from the header, or the guest record when there is none."""
    if x_tafheem_profile is None:
        return UNNAMED
    try:
        return clean_name(unquote(x_tafheem_profile))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


def current_user(name: str = Depends(typed_name)) -> str:
    """`typed_name`, refused unless it was signed up, so a deleted account files nothing."""
    if name != UNNAMED and not progress_store.has_account(name):
        raise HTTPException(status_code=401, detail="Log in again: no account with that username")
    return name


_USER = Depends(current_user)
_TYPED = Depends(typed_name)
_MODULE = Query("quiz", min_length=1, max_length=32, description="Which panel is asking")


@router.post("/attempts", response_model=AttemptSaved)
async def record_attempt(attempt: AttemptIn, user: str = _USER) -> AttemptSaved:
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
async def leave_feedback(note: FeedbackIn, user: str = _USER) -> AttemptSaved:
    """File a report about a question that looks wrong."""
    message = note.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="message is empty")
    return AttemptSaved(id=progress_store.leave_feedback(
        module=note.module, item=note.item, message=message, user=user,
    ))


@router.delete("", response_model=Forgotten)
async def forget_progress(user: str = _USER) -> Forgotten:
    """Delete every answer this name has given. The Settings wipe calls it."""
    return Forgotten(deleted=progress_store.forget(user))


@router.get("/summary", response_model=ProgressSummary)
def get_summary(module: str = _MODULE, user: str = _USER) -> ProgressSummary:
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


@router.get("/review", response_model=ReviewList)
def get_review(module: str = _MODULE, user: str = _USER) -> ReviewList:
    """Items due for review now, earliest first."""
    return ReviewList(module=module, items=progress_store.review_items(module, user))


@router.post("/signup", response_model=ProfileSaved)
async def sign_up(body: ProfileIn, user: str = _TYPED) -> ProfileSaved:
    """Take a free username and hand back its one spelling, which the page keeps.

    `keep` moves this device's unnamed answers onto it.
    """
    _named(user)
    if not progress_store.sign_up(user):
        raise HTTPException(status_code=409, detail="That username is taken")
    return ProfileSaved(name=user, moved=progress_store.claim_local(user) if body.keep else 0)


@router.post("/login", response_model=ProfileSaved)
async def log_in(user: str = _TYPED) -> ProfileSaved:
    """Check a username was signed up and hand back its one spelling."""
    _named(user)
    if not progress_store.has_account(user):
        raise HTTPException(status_code=404, detail="No account with that username")
    return ProfileSaved(name=user, moved=0)


@router.get("/account", response_model=Account)
def get_account(user: str = _USER) -> Account:
    """The profile page's facts about this username."""
    _named(user)
    return Account(**progress_store.account(user))


@router.delete("/account", response_model=Forgotten)
async def delete_account(user: str = _USER) -> Forgotten:
    """Delete this username and every answer it gave; the name is free again."""
    _named(user)
    return Forgotten(deleted=progress_store.delete_account(user))


@router.get("/leaderboard", response_model=Leaderboard)
def get_leaderboard(module: str = _MODULE, user: str = _USER) -> Leaderboard:
    """The top accounts by words learnt, plus the asker's own place."""
    rows = progress_store.leaderboard(module)
    you = next((row for row in rows if row["name"] == user), None)
    return Leaderboard(rows=rows[: get_settings().leaderboard_size], you=you)


def _named(user: str) -> None:
    if user == UNNAMED:
        raise HTTPException(status_code=422, detail="Type a username")
