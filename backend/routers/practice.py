"""Practice question generation endpoint.

When an AI backend is available: generates rich, tailored questions via LLM.
When running offline (no AI): generates template-based questions from the
rule engine's I'raab analysis, still useful, just less explanatory.

Whichever made them, the questions are filed in progress.db as they leave
(`_answer`), under the source the page shows, so there is one way out and one
way in and nothing here names a source twice.
"""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Query

from backend.models.schemas import (
    KeptQuestion,
    KeptQuestions,
    PracticeQuestion,
    PracticeRequest,
    PracticeResponse,
    Source,
)
from backend.services import ai as ai_service
from backend.services import morphology, practice_service, progress_store, provenance, rule_engine
from backend.utils import arabic_sentence, call_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/practice", tags=["practice"])

# The panel these questions belong to, as progress.db files it.
MODULE = "nahw"


@router.post("", response_model=PracticeResponse)
async def generate_practice(request: PracticeRequest) -> PracticeResponse:
    sentence = arabic_sentence(request.sentence, "Sentence")

    # Always run local analysis first (fast, offline)
    tags = await asyncio.to_thread(morphology.analyze_sentence, sentence)
    rule_result = await asyncio.to_thread(rule_engine.analyze, sentence, tags)

    if await asyncio.to_thread(ai_service.is_ai_available):
        # ── AI path ───────────────────────────────────────────────────────────
        iraab_context = await _build_iraab_context(sentence, tags, rule_result)
        try:
            result = await call_service(
                ai_service.generate_practice,
                sentence,
                iraab_context,
                operation="Practice question generation",
                timeout_msg="Practice question generation timed out.",
            )
            questions = [PracticeQuestion(**q) for q in result.get("questions", [])]
            if questions:
                return await _answer(sentence, questions, "ai")
        except Exception as exc:
            logger.warning("AI practice failed, falling back to templates: %s", exc)

    # ── Template path (offline) ───────────────────────────────────────────────
    questions = practice_service.from_analysis(sentence, rule_result)
    return await _answer(sentence, [PracticeQuestion(**q) for q in questions], "nahw")


@router.get("/kept", response_model=KeptQuestions)
async def kept_practice(sentence: str | None = Query(None, max_length=2000)) -> KeptQuestions:
    """Every question filed so far, or only one sentence's."""
    wanted = arabic_sentence(sentence, "Sentence") if sentence else None
    rows = await asyncio.to_thread(progress_store.kept_questions, MODULE, wanted)
    return KeptQuestions(questions=[KeptQuestion(**row) for row in rows])


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


async def _build_iraab_context(sentence: str, tags: list[dict], rule_result: dict) -> str:
    """Best-effort: run AI I'raab for richer practice context, else use rule engine."""
    tags_str = morphology.tags_as_string(tags)
    try:
        ai_iraab = await asyncio.to_thread(
            ai_service.analyze_iraab, sentence, tags_str
        )
        return json.dumps(ai_iraab.get("words", []), ensure_ascii=False)
    except Exception:
        return json.dumps(rule_result.get("words", []), ensure_ascii=False)
