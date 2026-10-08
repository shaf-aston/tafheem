"""Say an Arabic word aloud: GET /api/speak?text=... returns a WAV.

Thin: it checks the text, hands it to services/speech.py and sets how long the
browser may keep the answer. A GET, so the page's own audio player can play the
address directly and the browser caches it like any file.
"""
from __future__ import annotations

import re
import time
from collections import deque

from fastapi import APIRouter, HTTPException, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from backend.config import get_settings
from backend.services import speech

router = APIRouter(prefix="/api/speak", tags=["speak"])

# Arabic words (with the dialect letters for g and ch), single spaces, and the
# pause marks a phrase ends or breathes on. Nothing else is spoken, so nothing
# else can reach the engine.
WORD = "[ء-غف-ٰٕٱگڭچ]+"
ARABIC = re.compile(f"{WORD}{speech.PAUSE}?( {WORD}{speech.PAUSE}?)*")


# Recent asks per visitor, for speech_per_minute. In memory: a restart forgets
# it, which is fine for a limit that only stops someone hammering the voice.
_asks: dict[str, deque[float]] = {}


def _too_many(visitor: str, cost: int) -> bool:
    now = time.monotonic()
    if len(_asks) > 10_000:  # never grows without end
        _asks.clear()
    recent = _asks.setdefault(visitor, deque())
    while recent and now - recent[0] > 60:
        recent.popleft()
    if len(recent) + cost > get_settings().speech_per_minute:
        return True
    recent.extend([now] * cost)
    return False


@router.get("")
async def speak(request: Request, text: str = Query(..., min_length=1)) -> Response:
    # Behind Vercel and Caddy the visitor is the first forwarded address. A
    # visitor can fake that header, so this slows casual abuse, not a determined one.
    forwarded = request.headers.get("x-forwarded-for", "")
    visitor = forwarded.split(",")[0].strip() or (request.client.host if request.client else "")
    text = speech.tidy(text)
    settings = get_settings()
    if len(text) > settings.speech_max_chars:
        raise HTTPException(413, "Too long to say")
    if not ARABIC.fullmatch(text):
        raise HTTPException(422, "Only Arabic can be said")
    # A long phrase costs the voice what several words do, so it counts as several asks.
    if _too_many(visitor, -(-len(text) // settings.speech_chars_per_ask)):
        raise HTTPException(429, "Too many words at once; try again in a minute")
    # lib/speak.js's `prepare` marks a word made ahead of a press, so a press goes first.
    pressed = request.headers.get("x-speak-ahead") != "1"
    try:
        audio = await run_in_threadpool(speech.say, text, pressed)
    except RuntimeError as exc:
        raise HTTPException(503, "No voice is available right now") from exc
    # The same text always sounds the same, so the browser may keep it, and so
    # may Vercel's edge in front of this server, for every visitor near it.
    return Response(audio, media_type="audio/wav",
                    headers={"Cache-Control": "public, max-age=31536000, immutable",
                             "CDN-Cache-Control": "public, max-age=31536000"})
