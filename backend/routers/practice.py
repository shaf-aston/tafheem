"""Practice question generation endpoint.

Questions are filled from data/practice/templates.json with the sentence's own
i'raab (services/nahw/iraab.py), so every answer is the book's rules, never a model's.

The questions are filed in progress.db as they leave
(`_answer`), under the source the page shows, so there is one way out and one
way in and nothing here names a source twice.
"""
from __future__ import annotations

import asyncio
import logging
import random

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response

from backend.config import get_settings
from backend.models.practice import (
    CheckedSentence,
    KeptQuestion,
    KeptQuestions,
    PracticeQuestion,
    PracticeRequest,
    PracticeResponse,
)
from backend.identity import USER
from backend.services import ai
from backend.services.nahw import iraab
from backend.services.nahw import practice as practice_service
from backend.services.learner import progress_store
from backend.services.core import provenance
from backend.services.learner import sentence_check
from backend.utils import Timings, arabic_sentence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/practice", tags=["practice"])

# The panel these questions belong to, as progress.db files it.
MODULE = "nahw"


@router.post("", response_model=PracticeResponse)
async def generate_practice(request: PracticeRequest, response: Response, later: BackgroundTasks) -> PracticeResponse:
    sentence = arabic_sentence(request.sentence, "Sentence")
    timings = Timings()
    with timings.step("analyze"):
        read = await asyncio.to_thread(iraab.analyze, sentence)
    with timings.step("questions"):
        questions = [PracticeQuestion(**q) for q in practice_service.from_analysis(sentence, read)]
    response.headers["Server-Timing"] = timings.header()
    logger.info("Practice for a %d-word sentence: %s", len(read["words"]), timings.header())
    return _answer(sentence, questions, "nahw", later)


@router.get("/kept", response_model=KeptQuestions)
async def kept_practice(sentence: str | None = Query(None, max_length=2000)) -> KeptQuestions:
    """Every question filed so far, or only one sentence's. No screen reads it yet: it is the
    way back into what /api/practice filed, for a review screen to come."""
    wanted = arabic_sentence(sentence, "Sentence") if sentence else None
    rows = await asyncio.to_thread(progress_store.kept_questions, MODULE, wanted)
    return KeptQuestions(questions=[KeptQuestion(**row) for row in rows])


@router.post("/checked", response_model=CheckedSentence)
async def checked_sentence(user: str = USER) -> CheckedSentence:
    """A short AI sentence using only words this learner has learnt, every word checked."""
    learnt = [row for row in await asyncio.to_thread(progress_store.summary, "quiz", user) if row["known"]]
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


def _answer(sentence: str, questions: list[PracticeQuestion], source_key: str, later: BackgroundTasks) -> PracticeResponse:
    """Answer, and file the questions under the source the page will show once the answer is sent.

    Filing is not allowed to cost the learner their questions, nor their time: it runs after
    the answer, and a database that will not take them is logged.
    """
    later.add_task(_keep, sentence, [q.model_dump() for q in questions], source_key)
    return PracticeResponse(sentence=sentence, questions=questions, source=provenance.of(source_key))


def _keep(sentence: str, questions: list[dict], source_key: str) -> None:
    try:
        added = progress_store.keep_questions(module=MODULE, sentence=sentence, questions=questions, source=source_key)
        logger.info("Kept %d new practice question(s) for '%s' (%s)", added, sentence[:40], source_key)
    except Exception as exc:
        logger.warning("Could not keep practice questions: %s", exc)
