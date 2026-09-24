"""Reports from the page: a mic gate closing, a reading it gave up on.

The page's own half of the recite journal. The server writes its own half
straight to the file through services/journal.note(); this is the one door the
browser has onto that same file, so a session can be read as one sequence of
events, page and server together, joined by the reading id both sides use.

Body is read and size-checked by hand rather than declared as a Pydantic
parameter, so an oversized batch is rejected before the whole thing is parsed
rather than after.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import ValidationError

from backend.config import get_settings
from backend.models.schemas import JournalBatch
from backend.services import journal

router = APIRouter(prefix="/api/journal", tags=["journal"])

# How much of a detail object is kept before it is replaced with a marker. Not
# a config knob: it protects the journal file itself from one oversized event,
# which is a fixed concern of this file rather than something worth tuning.
_DETAIL_BYTES_MAX = 4096


@router.post("", status_code=204)
async def post_events(request: Request) -> Response:
    """File every event the page reports, each as its own line."""
    settings = get_settings()
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > settings.journal_page_bytes_max:
        raise HTTPException(
            status_code=413,
            detail=f"a journal batch is capped at {settings.journal_page_bytes_max} bytes",
        )
    # Content-Length can be absent (a chunked/streamed body) or wrong; read it
    # in pieces and stop as soon as the total passes the cap, rather than
    # buffering an unbounded body first to find out.
    chunks = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > settings.journal_page_bytes_max:
            raise HTTPException(
                status_code=413,
                detail=f"a journal batch is capped at {settings.journal_page_bytes_max} bytes",
            )
        chunks.append(chunk)
    raw = b"".join(chunks)

    try:
        batch = JournalBatch.model_validate_json(raw)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="malformed journal batch") from exc

    if len(batch.events) > settings.journal_page_events_max:
        raise HTTPException(
            status_code=422,
            detail=f"a journal batch is capped at {settings.journal_page_events_max} events",
        )

    for event in batch.events:
        detail = event.detail
        if detail is not None and len(json.dumps(detail, ensure_ascii=False).encode("utf-8")) > _DETAIL_BYTES_MAX:
            detail = {"truncated": True}
        journal.note_page({
            "at": event.at,
            "kind": event.kind,
            "session": event.session,
            "reading": event.reading,
            "detail": detail,
        })
    return Response(status_code=204)
