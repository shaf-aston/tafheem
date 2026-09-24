"""What a learner has answered, and what it says about them.

Thin on purpose: every rule about what counts as still-to-review, and every
piece of SQL, lives in services/progress_store.py. This file only turns a
request into a call and the answer into a response model.

Nothing here knows what an item is. The quiz sends the id of a meaning; the
tags that say what kind of word that is live in the page's own word list, which
is where the "what do I keep getting wrong" reading is made.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import (
    AttemptIn,
    AttemptSaved,
    FeedbackIn,
    Forgotten,
    ItemStats,
    ProgressSummary,
    ReviewList,
)
from backend.services import progress_store

router = APIRouter(prefix="/api/progress", tags=["progress"])

# Who is answering. There are no accounts, so there is one learner and the
# server names them; taking a name from the page would mean anybody could read
# or write anybody's record the moment accounts did exist. When they do, this
# becomes an auth dependency and nothing below it changes.
LOCAL_USER = "local"

_MODULE = Query("quiz", min_length=1, max_length=32, description="Which panel is asking")


@router.post("/attempts", response_model=AttemptSaved)
async def record_attempt(attempt: AttemptIn) -> AttemptSaved:
    """File one answer, right or wrong."""
    row_id = progress_store.record(
        module=attempt.module,
        item=attempt.item,
        correct=attempt.correct,
        ms=attempt.ms,
        context=attempt.context,
        user=LOCAL_USER,
    )
    return AttemptSaved(id=row_id)


@router.post("/feedback", response_model=AttemptSaved)
async def leave_feedback(note: FeedbackIn) -> AttemptSaved:
    """File a report about a question that looks wrong."""
    message = note.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="message is empty")
    return AttemptSaved(id=progress_store.leave_feedback(
        module=note.module, item=note.item, message=message, user=LOCAL_USER,
    ))


@router.delete("", response_model=Forgotten)
async def forget_progress() -> Forgotten:
    """Delete every answer this learner has given. The Settings wipe calls it."""
    return Forgotten(deleted=progress_store.forget(LOCAL_USER))


@router.get("/summary", response_model=ProgressSummary)
async def get_summary(module: str = _MODULE) -> ProgressSummary:
    """Every item answered in this module, with its record and whether it is still owed."""
    return ProgressSummary(
        module=module,
        items=[
            ItemStats(
                item=row["item"],
                attempts=row["attempts"],
                wrong=row["wrong"],
                avgMs=row["avg_ms"],
                inReview=row["in_review"],
            )
            for row in progress_store.summary(module, LOCAL_USER)
        ],
    )


@router.get("/review", response_model=ReviewList)
async def get_review(module: str = _MODULE) -> ReviewList:
    """Just the items still waiting to be got right."""
    return ReviewList(module=module, items=progress_store.review_items(module, LOCAL_USER))
