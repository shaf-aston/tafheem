"""The recording studio's two calls: what to record next, and a take to keep.

Both need the recorder key (config recorder_key) in X-Recorder-Key; with no key
set the studio is off and both answer 404, so a public server shows nothing.
"""
from __future__ import annotations

import hmac

from fastapi import APIRouter, File, Form, Header, HTTPException, Query, UploadFile
from starlette.concurrency import run_in_threadpool

from backend.config import get_settings
from backend.services import speech_recordings

router = APIRouter(prefix="/api/recordings", tags=["recordings"])


def _allowed(key: str | None) -> None:
    expected = get_settings().recorder_key.get_secret_value()
    if not expected:
        raise HTTPException(404, "The recording studio is off")
    if not key or not hmac.compare_digest(key, expected):
        raise HTTPException(403, "Wrong recorder key")


@router.get("/todo")
def todo(limit: int = Query(20, ge=1, le=200), x_recorder_key: str | None = Header(None)) -> dict:
    _allowed(x_recorder_key)
    words, left = speech_recordings.todo(limit)
    return {"words": words, "left": left, "done": len(speech_recordings.index())}


@router.post("")
async def keep(text: str = Form(..., min_length=1, max_length=200), audio: UploadFile = File(...),
               x_recorder_key: str | None = Header(None)) -> dict:
    _allowed(x_recorder_key)
    limit = get_settings().recording_max_kb * 1024
    body = await audio.read(limit + 1)
    if len(body) > limit:
        raise HTTPException(413, "That take is too long for one word")
    try:
        name = await run_in_threadpool(speech_recordings.keep, text, body)
    except ValueError as exc:
        raise HTTPException(415, "That is not a recording") from exc
    return {"file": name}
