"""The AI's reading of a word's meaning and verb class: optional enrichment of a table the reader already has."""
from __future__ import annotations

import logging

from backend.services import ai
from backend.services.sarf import morphology

logger = logging.getLogger(__name__)


def of(word: str) -> dict | None:
    """The model's answer, or None when there is no model or it failed: never worth an error screen."""
    if not ai.is_ai_available():
        return None
    tags = morphology.tags_as_string([morphology.analyze_word(word)])
    try:
        return ai.analyze_sarf(word, tags)
    except Exception as exc:
        logger.warning("Sarf AI failed for '%s': %s", word, exc)
        return None
