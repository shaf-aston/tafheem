"""Say an Arabic word aloud: GET /api/speak?text=...&accent=... returns its sound.

Thin: it checks the text, hands it to services/speech.py and sets how long the
browser may keep the answer. A GET, so the page's own audio player can play the
address directly and the browser caches it like any file.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from backend.config import get_settings
from backend.services import speech
from backend.services.colloquial import loader as colloquial
from backend.services.ratelimit import PerMinute, visitor

router = APIRouter(prefix="/api/speak", tags=["speak"])

# Arabic words (with the dialect letters for g and ch), single spaces, and the
# pause marks a phrase ends or breathes on. Nothing else is spoken, so nothing
# else can reach the engine.
WORD = "[ء-غف-ٰٕٱگڭچ]+"
ARABIC = re.compile(f"{WORD}{speech.PAUSE}?( {WORD}{speech.PAUSE}?)*")


_limit = PerMinute("speech_per_minute")


@router.get("")
async def speak(request: Request, text: str = Query(..., min_length=1), accent: str | None = None,
                speed: str = "normal") -> Response:
    text = speech.tidy(text)
    settings = get_settings()
    if len(text) > settings.speech_max_chars:
        raise HTTPException(413, "Too long to say")
    if not ARABIC.fullmatch(text):
        raise HTTPException(422, "Only Arabic can be said")
    # A long phrase costs the voice what several words do, so it counts as several asks.
    if _limit.too_many(visitor(request), -(-len(text) // settings.speech_chars_per_ask)):
        raise HTTPException(429, "Too many words at once; try again in a minute")
    # A Colloquial dialect is said by a speaker of it (dialects.json `voice`).
    try:
        first = colloquial.voice_of(accent) if accent else None
    except KeyError as exc:
        raise HTTPException(422, "Unknown accent") from exc
    # A named pace from config only, so no one can ask for a new file per decimal place.
    if speed not in settings.speech_speeds:
        raise HTTPException(422, "Unknown speed")
    # lib/speak.js's `prepare` marks a word made ahead of a press, so a press goes first.
    pressed = request.headers.get("x-speak-ahead") != "1"
    try:
        audio = await run_in_threadpool(speech.say, text, pressed, first, settings.speech_speeds[speed])
    except RuntimeError as exc:
        raise HTTPException(503, "No voice is available right now") from exc
    # The same text always sounds the same, so the browser may keep it, and so
    # may Vercel's edge in front of this server, for every visitor near it.
    return Response(audio, media_type=speech.media_type(audio),
                    headers={"Cache-Control": "public, max-age=31536000, immutable",
                             "CDN-Cache-Control": "public, max-age=31536000"})
