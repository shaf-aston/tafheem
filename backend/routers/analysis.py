"""I'raab (grammatical case and function) analysis endpoint.

Strategy:
  1. Run local morphology (CAMeL / Qalsadi / PyArabic), always fast, offline.
  2. Run the rule engine, deterministic Nahw rules, no network needed.
  2b. Let the syntax parser (services/syntax) name the roles it can; it reads the
     links between the words and scores far better than the rules alone, so its
     name wins wherever it has one and the rules fill the gaps.
  3. If rule engine confidence < settings.confidence_threshold **and** an AI backend is
     available, call the AI to get richer explanations / handle complex cases.
  4. Merge: AI word list is preferred when present; rule engine is the fallback.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter

from backend.config import get_settings
from backend.models.schemas import AnalyzeRequest, AnalyzeResponse, Source, WordAnalysis
from backend.services import ai as ai_service
from backend.services import morphology, provenance, rule_engine, syntax
from backend.utils import arabic_sentence, call_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analyze", tags=["analysis"])


@router.post("", response_model=AnalyzeResponse)
async def analyze_sentence(request: AnalyzeRequest) -> AnalyzeResponse:
    sentence = arabic_sentence(request.sentence, "Sentence")

    # ── Step 1: Local morphological analysis ─────────────────────────────────
    tags = await asyncio.to_thread(morphology.analyze_sentence, sentence)
    tags_str = morphology.tags_as_string(tags)

    # ── Step 2: Rule engine (always runs, offline) ────────────────────────────
    rule_result = await asyncio.to_thread(rule_engine.analyze, sentence, tags)
    confidence = rule_result.get("confidence", 0.0)
    threshold = get_settings().confidence_threshold
    logger.info(
        "Rule engine confidence for '%s': %.2f (threshold %.2f)",
        sentence[:40], confidence, threshold,
    )

    # ── Step 2b: the parser names what it can, over the rules ────────────────
    parsed = await asyncio.to_thread(syntax.read, sentence)
    rule_result = syntax.with_parser_roles(rule_result, parsed["roles"])
    confidence = rule_result.get("confidence", 0.0)

    # ── Step 3: AI augmentation (optional) ───────────────────────────────────
    ai_result: dict | None = None
    if await asyncio.to_thread(ai_service.is_ai_available) and confidence < threshold:
        try:
            ai_result = await call_service(
                ai_service.analyze_iraab,
                sentence,
                tags_str,
                operation="AI I'raab analysis",
                timeout_msg="AI service timed out. Showing local analysis.",
            )
        except Exception as exc:
            logger.warning("AI I'raab failed, using rule engine: %s", exc)

    # ── Step 4: Build response ────────────────────────────────────────────────
    if ai_result:
        # AI may return a summary but an empty word list, or a list of bare
        # strings instead of word dicts; either way the rule engine's words
        # stand in, field by field.
        ai_words = ai_result.get("words")
        if not (isinstance(ai_words, list) and ai_words and all(isinstance(w, dict) for w in ai_words)):
            if ai_words:
                logger.warning("AI word list malformed, using rule engine words")
            ai_words = None
        engine_words = rule_result.get("words", [])
        word_dicts = rule_engine.with_engine_roots(ai_words, engine_words) if ai_words else engine_words
        summary = ai_result.get("summary") or rule_result.get("summary")
        source_note = provenance.of("ai")
    else:
        word_dicts = rule_result.get("words", [])
        summary = rule_result.get("summary")
        source_note = provenance.of("nahw")

    logger.info("Analysis source: %s", source_note["label"])

    return AnalyzeResponse(
        sentence=sentence,
        words=[WordAnalysis.from_raw(w) for w in word_dicts],
        summary=summary,
        source=Source(**source_note),
        # the picture is the parser's own reading, so it is only drawn when the
        # words on screen are still the parser's; an AI answer replaces them
        tree=None if ai_result else parsed["tree"],
    )
