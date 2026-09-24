"""Practice question generation endpoint.

When an AI backend is available: generates rich, tailored questions via LLM.
When running offline (no AI): generates template-based questions from the
rule engine's I'raab analysis, still useful, just less explanatory.
"""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter

from backend.models.schemas import (
    PracticeQuestion,
    PracticeRequest,
    PracticeResponse,
    Source,
)
from backend.services import ai as ai_service
from backend.services import morphology, practice_service, provenance, rule_engine
from backend.utils import arabic_sentence, call_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/practice", tags=["practice"])


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
                return PracticeResponse(
                    sentence=sentence,
                    questions=questions,
                    source=Source(**provenance.of("ai")),
                )
        except Exception as exc:
            logger.warning("AI practice failed, falling back to templates: %s", exc)

    # ── Template path (offline) ───────────────────────────────────────────────
    questions = practice_service.from_analysis(sentence, rule_result)
    return PracticeResponse(
        sentence=sentence,
        questions=[PracticeQuestion(**question) for question in questions],
        source=Source(**provenance.of("nahw")),
    )


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
