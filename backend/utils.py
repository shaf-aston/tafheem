"""Shared HTTP helpers: input validation, Arabic detection, and service error mapping."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, TypeVar

from fastapi import HTTPException

from backend.services.arabic_text import has_arabic, words

logger = logging.getLogger(__name__)

T = TypeVar("T")


def normalize_text(text: str, field: str = "input") -> str:
    """Strip whitespace and raise HTTP 400 if the result is empty."""
    if cleaned := text.strip():
        return cleaned
    else:
        raise HTTPException(status_code=400, detail=f"{field} cannot be empty")


def arabic_sentence(text: str, field: str = "input") -> str:
    """A sentence ready to analyse: non-empty, Arabic, and words only.

    An ayah pasted from the Qur'an tab carries its pause signs and its number;
    left in, the tagger and the AI each gave the ayah number a grammar card.
    """
    text = normalize_text(text, field)
    require_arabic(text, field)
    return " ".join(words(text))


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
