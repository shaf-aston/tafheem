"""Shared HTTP helpers: input validation, Arabic detection, and service error mapping."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, TypeVar

from fastapi import HTTPException

from backend.config import get_settings
from backend.services.arabic_text import has_arabic, spelled_out, unpunctuated, words

logger = logging.getLogger(__name__)

T = TypeVar("T")


def normalize_text(text: str, field: str = "input") -> str:
    """Strip whitespace and raise HTTP 400 if the result is empty."""
    if cleaned := text.strip():
        return cleaned
    else:
        raise HTTPException(status_code=400, detail=f"{field} cannot be empty")


def search_query(text: str, required: bool = False, field: str = "Search query") -> str:
    """What was typed into a search box, read the one way every search reads it:
    punctuation is a break between words, never part of one (arabic_text.unpunctuated).
    A full stop at the end used to ride into the matching as a letter. A root
    spelled out (ك-ت-ب) is joined back into one word (arabic_text.spelled_out).
    `required` makes an empty query a 400, for the searches that have nothing to
    show for one."""
    query = spelled_out(unpunctuated(text))
    return normalize_text(query, field) if required else query


def arabic_sentence(text: str, field: str = "input") -> str:
    """A sentence ready to analyse: non-empty, Arabic, words only, and no longer than
    settings.max_sentence_words (HTTP 422).

    An ayah pasted from the Qur'an tab carries its pause signs and its number;
    left in, the tagger and the AI each gave the ayah number a grammar card.
    """
    text = normalize_text(text, field)
    require_arabic(text, field)
    kept = words(text)
    if len(kept) > (limit := get_settings().max_sentence_words):
        raise HTTPException(status_code=422, detail=f"{field} is longer than {limit} words.")
    return " ".join(kept)


def require_arabic(text: str, field: str = "input") -> None:
    """Raise HTTP 422 if `text` contains no Arabic characters."""
    if not has_arabic(text):
        raise HTTPException(
            status_code=422,
            detail=f"{field} must contain Arabic text (no Arabic characters detected).",
        )


async def call_service(
    func: Callable[..., T],
    *args: Any,
    operation: str,
    timeout_msg: str,
) -> T:
    """Run a blocking service call in a worker thread, mapping failures to HTTP errors.

    Raw exception text is logged server-side only, client responses stay generic
    so SDK internals, paths, and config hints never leak.
    """
    try:
        return await asyncio.to_thread(func, *args)
    except ValueError as exc:
        logger.error("%s configuration error: %s", operation, exc)
        raise HTTPException(
            status_code=500,
            detail=f"{operation} failed: service misconfigured. See server logs.",
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=timeout_msg) from exc
    except Exception as exc:
        logger.exception("%s failed", operation)
        raise HTTPException(status_code=500, detail=f"{operation} failed.") from exc
