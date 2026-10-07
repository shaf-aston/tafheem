"""Practice question generation endpoint.

Questions are filled from data/practice/templates.json with the sentence's own
i'raab (services/iraab.py), so every answer is the book's rules, never a model's.

The questions are filed in progress.db as they leave
(`_answer`), under the source the page shows, so there is one way out and one
way in and nothing here names a source twice.
"""
from __future__ import annotations

import asyncio
import logging
import random

from fastapi import APIRouter, HTTPException, Query

from backend.config import get_settings
from backend.models.schemas import (
    CheckedSentence,
    KeptQuestion,
    KeptQuestions,
    PracticeQuestion,
    PracticeRequest,
    PracticeResponse,
    Source,
)
from backend.routers.progress import _USER
from backend.services import ai, iraab, practice_service, progress_store, provenance, sentence_check
from backend.utils import arabic_sentence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/practice", tags=["practice"])

# The panel these questions belong to, as progress.db files it.
MODULE = "nahw"


@router.post("", response_model=PracticeResponse)
async def generate_practice(request: PracticeRequest) -> PracticeResponse:
    sentence = arabic_sentence(request.sentence, "Sentence")
    read = await asyncio.to_thread(iraab.analyse, sentence)
    questions = practice_service.from_analysis(sentence, read)
    return await _answer(sentence, [PracticeQuestion(**q) for q in questions], "nahw")


@router.get("/kept", response_model=KeptQuestions)
async def kept_practice(sentence: str | None = Query(None, max_length=2000)) -> KeptQuestions:
    """Every question filed so far, or only one sentence's."""
    wanted = arabic_sentence(sentence, "Sentence") if sentence else None
    rows = await asyncio.to_thread(progress_store.kept_questions, MODULE, wanted)
    return KeptQuestions(questions=[KeptQuestion(**row) for row in rows])


@router.post("/checked", response_model=CheckedSentence)
async def checked_sentence(user: str = _USER) -> CheckedSentence:
    """A short AI sentence using only words this learner has learnt, every word checked."""
    learnt = [row["item"] for row in await asyncio.to_thread(progress_store.summary, "quiz", user) if row["known"]]
    settings = get_settings()
    words = sentence_check.learnt_words(learnt)
    if len(words) < settings.sentence_min_learnt:
        raise HTTPException(409, f"Learn {settings.sentence_min_learnt} words first")
    if not ai.is_ai_available():
        raise HTTPException(503, "No AI is set up on this server")
    allowed = sentence_check.allowed(words)
    given = random.sample([word["ar"] for word in words], min(len(words), settings.sentence_prompt_words))
    made = await asyncio.to_thread(
        ai.checked_sentence, given, lambda ar: not sentence_check.check(ar, allowed),
    )
    if made is None:
        raise HTTPException(503, "Could not make a checked sentence, try again")
    return CheckedSentence(**made, words=given)


async def _answer(sentence: str, questions: list[PracticeQuestion], source_key: str) -> PracticeResponse:
    """File the questions under the source the page will show, then answer.

    Filing is not allowed to cost the learner their questions: a database that
    will not take them is logged and the answer goes out regardless.
    """
    try:
        added = await asyncio.to_thread(
            progress_store.keep_questions,
            module=MODULE,
            sentence=sentence,
            questions=[q.model_dump() for q in questions],
            source=source_key,
        )
        logger.info("Kept %d new practice question(s) for '%s' (%s)", added, sentence[:40], source_key)
    except Exception as exc:
        logger.warning("Could not keep practice questions: %s", exc)
    return PracticeResponse(sentence=sentence, questions=questions, source=Source(**provenance.of(source_key)))
