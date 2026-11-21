"""The page reader's first step: a picture of Arabic text in, the text out.

Thin: the reading is services/reading. What comes back is translated line by line by the
dictionary's own /api/dictionary/sentence, so a page's line and a typed sentence get one answer.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from backend.config import get_settings
from backend.models.reading import PictureText
from backend.services import reading
from backend.services.core.ratelimit import PICTURE

router = APIRouter(prefix="/api/read", tags=["reading"])


@router.post("/image", response_model=PictureText, dependencies=[Depends(PICTURE)])
async def read_image(image: UploadFile = File(...)) -> PictureText:
    limit = get_settings().read_max_kb * 1024
    body = await image.read(limit + 1)
    if len(body) > limit:
        raise HTTPException(413, "That picture is too large; a photo of one page is plenty")
    try:
        found = await run_in_threadpool(reading.read, body)
    except reading.NotAPicture as exc:
        raise HTTPException(415, "That file is not a picture this can open (PNG, JPEG or WebP)") from exc
    except reading.NoReader as exc:
        raise HTTPException(503, "Reading pictures is not set up on this server") from exc
    return PictureText(**found)
