"""I'raab (grammatical case and function) analysis endpoint.

Thin: the reading itself is services/iraab.py, the book's rules and the parser,
offline. No AI: a word the rules cannot settle is shown as a gap, never guessed.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.models.analyze import AnalyzeRequest, AnalyzeResponse, WordAnalysis

from backend.services import iraab
from backend.services.ratelimit import PerMinute, visitor
from backend.utils import arabic_sentence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyze", tags=["analysis"])
_limit = PerMinute("analyze_per_minute")


def _within_limit(http: Request) -> None:
    if _limit.too_many(visitor(http)):
        raise HTTPException(429, "Too many analyses at once; try again in a minute")


@router.post("", response_model=AnalyzeResponse, dependencies=[Depends(_within_limit)])
async def analyze_sentence(request: AnalyzeRequest) -> AnalyzeResponse:
    sentence = arabic_sentence(request.sentence, "Sentence")
    read = await asyncio.to_thread(iraab.analyze, sentence)
    logger.info("Analysed a %d-word sentence from %s", len(read["words"]), read["source"]["label"])
    return AnalyzeResponse(
        sentence=sentence,
        words=[WordAnalysis.from_raw(w) for w in read["words"]],
        summary=read["summary"],
        source=read["source"],
        tree=read["tree"],
    )
