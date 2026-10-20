"""Say an Arabic word aloud: GET /api/speak?text=... returns a WAV.

Thin: it checks the text, hands it to services/speech.py and sets how long the
browser may keep the answer. A GET, so the page's own audio player can play the
address directly and the browser caches it like any file.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query, Response
from starlette.concurrency import run_in_threadpool

from backend.config import get_settings
from backend.services import speech

router = APIRouter(prefix="/api/speak", tags=["speak"])

# Arabic letters and marks, and single spaces between words. Nothing else is
# spoken, so nothing else can reach the engine or the cache's file names.
ARABIC = re.compile(r"[ء-غف-ٰٕٱ]+( [ء-غف-ٰٕٱ]+)*")


@router.get("")
async def speak(text: str = Query(..., min_length=1)) -> Response:
    text = text.strip()
    if len(text) > get_settings().speech_max_chars:
        raise HTTPException(413, "Too long to say")
    if not ARABIC.fullmatch(text):
        raise HTTPException(422, "Only Arabic can be said")
    try:
        audio = await run_in_threadpool(speech.say, text)
    except RuntimeError as exc:
        raise HTTPException(503, "No voice is available right now") from exc
    # The same text always sounds the same, so the browser may keep it.
    return Response(audio, media_type="audio/wav",
                    headers={"Cache-Control": "public, max-age=31536000, immutable"})
