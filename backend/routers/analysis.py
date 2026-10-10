"""I'raab (grammatical case and function) analysis endpoint.

Thin: the reading itself is services/iraab.py, the book's rules and the parser,
offline. No AI: a word the rules cannot settle is shown as a gap, never guessed.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter

from backend.models.analysis import AnalyzeRequest, AnalyzeResponse, WordAnalysis

from backend.models.common import Source
from backend.services import iraab
from backend.utils import arabic_sentence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyze", tags=["analysis"])


@router.post("", response_model=AnalyzeResponse)
async def analyze_sentence(request: AnalyzeRequest) -> AnalyzeResponse:
    sentence = arabic_sentence(request.sentence, "Sentence")
    read = await asyncio.to_thread(iraab.analyse, sentence)
    logger.info("Analysed a %d-word sentence from %s", len(read["words"]), read["source"]["label"])
    return AnalyzeResponse(
        sentence=sentence,
        words=[WordAnalysis.from_raw(w) for w in read["words"]],
        summary=read["summary"],
        source=Source(**read["source"]),
        tree=read["tree"],
    )
