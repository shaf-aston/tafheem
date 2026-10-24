"""I'raab (grammatical case and function) analysis endpoint.

Thin: the reading itself is services/nahw/iraab.py, the book's rules and the parser,
offline. No AI: a word the rules cannot settle is shown as a gap, never guessed.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from backend.models.analyze import AnalyzeRequest, AnalyzeResponse, WordAnalysis

from backend.services.nahw import iraab
from backend.services.core.ratelimit import PerMinute, visitor
from backend.utils import Timings, arabic_sentence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyze", tags=["analysis"])
_limit = PerMinute("analyze_per_minute")


def _within_limit(http: Request) -> None:
    if _limit.too_many(visitor(http)):
        raise HTTPException(429, "Too many analyses at once; try again in a minute")


@router.post("", response_model=AnalyzeResponse, dependencies=[Depends(_within_limit)])
async def analyze_sentence(request: AnalyzeRequest, response: Response = None) -> AnalyzeResponse:
    sentence = arabic_sentence(request.sentence, "Sentence")
    timings = Timings()
    with timings.step("analyze"):
        read = await asyncio.to_thread(iraab.analyze, sentence)
    if response is not None:  # FastAPI always passes it; a direct call (tests, scripts) may not
        response.headers["Server-Timing"] = timings.header()
    logger.info("Analysed a %d-word sentence from %s: %s", len(read["words"]), read["source"]["label"], timings.header())
    return AnalyzeResponse(
        sentence=sentence,
        words=[WordAnalysis.from_raw(w) for w in read["words"]],
        summary=read["summary"],
        source=read["source"],
        tree=read["tree"],
        parse=read.get("parse"),
        read_failed=read.get("read_failed", False),
    )
