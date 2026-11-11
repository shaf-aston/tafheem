"""I'raab (grammatical case and function) analysis endpoint.

Thin: the reading itself is services/nahw/iraab.py, the book's rules and the parser,
offline. No AI: a word the rules cannot settle is shown as a gap, never guessed.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, Response

from backend.models.analyze import AnalyzeRequest, AnalyzeResponse, WordAnalysis

from backend.services.nahw import iraab
from backend.services.core.ratelimit import ANALYZE
from backend.utils import Timings, arabic_sentence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyze", tags=["analysis"])


@router.post("", response_model=AnalyzeResponse, dependencies=[Depends(ANALYZE)])
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
        unvowelled=read.get("unvowelled"),
    )
