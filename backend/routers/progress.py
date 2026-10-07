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

from backend.models.schemas import (
    AttemptIn,
    AttemptSaved,
    Claimed,
    FeedbackIn,
    Forgotten,
    ItemStats,
    ProgressSummary,
    ReviewList,
)
from backend.services import progress_store
from backend.services.profile import clean_name

router = APIRouter(prefix="/api/progress", tags=["progress"])

# Who is answering: the name the page sends, percent-encoded because a header
# cannot carry Arabic. No password, so anyone typing a name reads that record;
# that is agreed. No header is the record kept before names existed.
UNNAMED = "local"


def current_user(x_tafheem_profile: str | None = Header(None)) -> str:
    """The cleaned name from the header, or the shared record when there is none."""
    if x_tafheem_profile is None:
        return UNNAMED
    try:
        return clean_name(unquote(x_tafheem_profile))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


_USER = Depends(current_user)
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
            )
            for row in progress_store.summary(module, user)
        ],
    )


@router.get("/review", response_model=ReviewList)
def get_review(module: str = _MODULE, user: str = _USER) -> ReviewList:
    """Items due for review now, earliest first."""
    return ReviewList(module=module, items=progress_store.review_items(module, user))


@router.post("/claim", response_model=Claimed)
async def claim_progress(user: str = _USER) -> Claimed:
    """Move the answers given before names existed onto the name now typed."""
    if user == UNNAMED:
        raise HTTPException(status_code=422, detail="Type a name first")
    return Claimed(moved=progress_store.claim_local(user))
