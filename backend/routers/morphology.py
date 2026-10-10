"""Sarf routes: validate, then hand the word to services.sarf_word (which owns the step order).

/meaning is a separate request the frontend fires once the table is on screen, so the AI is never waited on.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from backend.models.common import Source

from backend.models.morphology import (

    ConjugationRequest,

    ConjugationResponse,

    MeaningRequest,

    MeaningResponse,

    MorphologyRequest,

    MorphologyResponse,

)
from backend.services import ai as ai_service
from backend.services import conjugation, morphology, provenance, sarf_word
from backend.utils import call_service, normalize_text, require_arabic

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/morphology", tags=["morphology"])

@router.post("", response_model=MorphologyResponse)
async def analyze_morphology(request: MorphologyRequest) -> MorphologyResponse:
    word = normalize_text(request.word, "Word")
    require_arabic(word, "Word")
    # A form has to be one we actually hold. Rejected here rather than carried
    # down and echoed back inside the "why there is no table" message.
    if request.form and request.form not in conjugation.forms():
        raise HTTPException(422, "Unknown verb form.")
    return await asyncio.to_thread(sarf_word.analyze, word, request.form)


@router.post("/meaning", response_model=MeaningResponse)
async def analyze_meaning(request: MeaningRequest) -> MeaningResponse:
    """The AI enrichment for a word, asked for on its own.

    A network call to an AI backend can take seconds. The main route above never
    waits on this, the table is already on screen by the time the frontend
    fires this request, so the wait is felt only by the one field that needs it.
    """
    word = normalize_text(request.word, "Word")
    require_arabic(word, "Word")

    if not await asyncio.to_thread(ai_service.is_ai_available):
        return MeaningResponse()

    tag = await asyncio.to_thread(morphology.analyze_word, word)
    tags_str = morphology.tags_as_string([tag])
    # Optional enrichment: a failure here is never worth an error screen over a
    # table the reader already has, so it degrades to "no meaning" instead.
    try:
        ai_result = await call_service(
            ai_service.analyze_sarf,
            word,
            tags_str,
            operation="Sarf AI analysis",
            timeout_msg="AI service timed out.",
        )
    except HTTPException as exc:
        logger.warning("Sarf AI failed for '%s': %s", word, exc.detail)
        return MeaningResponse()

    meaning = ai_result.get("meaning") or None
    return MeaningResponse(
        meaning=meaning,
        meaning_source=Source(**provenance.of("ai")) if meaning else None,
        verb_class=ai_result.get("verb_class"),
    )


@router.post("/conjugate", response_model=ConjugationResponse)
async def conjugate_form(request: ConjugationRequest) -> ConjugationResponse:
    """The same root in a different باب, rule tables only.

    Changing the باب changes the table and the وزن beside it. The root and the
    meaning belong to the word, and the page already has them, so this route
    never wakes the tagger or an AI for them: it is the rule engine and
    nothing else, and it answers in about a millisecond.
    """
    root = normalize_text(request.root, "Root")
    require_arabic(root, "Root")
    if request.form not in conjugation.forms():
        raise HTTPException(422, "Unknown verb form.")

    return sarf_word.table_for(conjugation.radicals_of(root), request.form)
