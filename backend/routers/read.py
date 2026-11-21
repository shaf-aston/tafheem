"""The page reader's first step: a picture of Arabic text in, the text out.

Thin: the reading is services/reading. What comes back is translated line by line by the
dictionary's own /api/dictionary/sentence, so a page's line and a typed sentence get one answer.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from backend.config import get_settings
from backend.models.reading import PictureText
from backend.services import reading
from backend.services.core.ratelimit import PICTURE

router = APIRouter(prefix="/api/read", tags=["reading"])

# Reading is CPU (Pillow, Tesseract) on the threadpool every other route shares: a per-minute limit
# alone lets a burst fill it. read_at_once read together; read_queue_max more wait; past that, 503
# at once, the way routers/listen.py shares out the local ear. Made on first use, in the loop that runs it.
_slots: asyncio.Semaphore | None = None
_waiting = 0


@asynccontextmanager
async def _a_slot():
    global _slots, _waiting
    settings = get_settings()
    if _waiting >= settings.read_queue_max:
        raise HTTPException(503, "Reading pictures is busy right now; try again in a moment")
    _slots = _slots or asyncio.Semaphore(settings.read_at_once)
    _waiting += 1
    try:
        await _slots.acquire()
    finally:
        _waiting -= 1  # let in, or gave up waiting: either way no longer in the queue
    try:
        yield
    finally:
        _slots.release()


@router.post("/image", response_model=PictureText, dependencies=[Depends(PICTURE)])
async def read_image(image: UploadFile = File(...)) -> PictureText:
    limit = get_settings().read_max_kb * 1024
    body = await image.read(limit + 1)
    if len(body) > limit:
        raise HTTPException(413, "That picture is too large; a photo of one page is plenty")
    try:
        async with _a_slot():
            found = await run_in_threadpool(reading.read, body)
    except reading.NotAPicture as exc:
        raise HTTPException(415, "That file is not a picture this can open (PNG, JPEG or WebP)") from exc
    except reading.NotRead as exc:
        raise HTTPException(502, "The picture could not be read just now; try again in a moment") from exc
    except reading.NoReader as exc:
        raise HTTPException(503, "Reading pictures is not set up on this server") from exc
    return PictureText(**found)
