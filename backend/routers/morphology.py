"""Sarf routes: validate, then hand the word to services.sarf_word (which owns the step order).

/meaning is a separate request the frontend fires once the table is on screen, so the AI is never waited on.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException


from backend.models.morphology import (

    ConjugationRequest,

    ConjugationResponse,

    MeaningRequest,

    MeaningResponse,

    MorphologyRequest,

    MorphologyResponse,

)
from backend.services.sarf import conjugation
from backend.services.core import provenance
from backend.services.sarf import answer as sarf_word
from backend.services.sarf import word_meaning
from backend.utils import arabic_word, normalize_text, require_arabic

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
    word = arabic_word(request.word, "Word")

    ai_result = await asyncio.to_thread(word_meaning.of, word)
    if ai_result is None:
        return MeaningResponse()

    # Text or nothing: a model that answers a field with a list or a number is wrong, not a 500.
    def text(key: str, longest: int) -> str | None:
        value = ai_result.get(key)
        return (value.strip()[:longest] or None) if isinstance(value, str) else None

    meaning = text("meaning", 300)
    return MeaningResponse(
        meaning=meaning,
        meaning_source=provenance.of("ai") if meaning else None,
        verb_class=text("verb_class", 60),
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
