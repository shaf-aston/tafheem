"""Shared HTTP helpers: input validation, Arabic detection, and service error mapping."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from contextlib import contextmanager
from typing import Any, Callable, TypeVar

from fastapi import HTTPException

from backend.config import get_settings
from backend.services.text.arabic_text import has_arabic, spelled_out, unpunctuated, words

logger = logging.getLogger(__name__)

T = TypeVar("T")


def normalize_text(text: str, field: str = "input") -> str:
    """Strip whitespace and raise HTTP 400 if the result is empty."""
    if cleaned := text.strip():
        return cleaned
    else:
        raise HTTPException(status_code=400, detail=f"{field} cannot be empty")


def search_query(text: str, required: bool = False) -> str:
    """What was typed into a search box, read the one way every search reads it:
    punctuation is a break between words, never part of one (arabic_text.unpunctuated).
    A full stop at the end used to ride into the matching as a letter. A root
    spelled out (ك-ت-ب) is joined back into one word (arabic_text.spelled_out).
    `required` makes an empty query a 400, for the searches that have nothing to
    show for one."""
    query = spelled_out(unpunctuated(text))
    return normalize_text(query, "Search query") if required else query


def arabic_sentence(text: str, field: str = "input") -> str:
    """A sentence ready to analyse: non-empty, Arabic, words only, and no longer than
    settings.max_sentence_words (HTTP 422).

    An ayah pasted from the Qur'an tab carries its pause signs and its number;
    left in, the tagger and the AI each gave the ayah number a grammar card.
    """
    text = normalize_text(text, field)
    require_arabic(text, field)
    if not (kept := words(text)):
        raise HTTPException(status_code=422, detail=f"{field} has no Arabic words.")
    if len(kept) > (limit := get_settings().max_sentence_words):
        raise HTTPException(status_code=422, detail=f"{field} is longer than {limit} words.")
    return " ".join(kept)


_ENGLISH_RE = re.compile(r"[A-Za-z0-9'\s,.;:!?\-\"()]+")


def english_sentence(text: str, field: str = "input") -> str:
    """English words ready to look up: Latin letters and basic punctuation only, at least
    two words and no more than settings.max_sentence_words (HTTP 422)."""
    text = normalize_text(text, field)
    if not _ENGLISH_RE.fullmatch(text) or not re.search(r"[A-Za-z]", text):
        raise HTTPException(status_code=422, detail=f"{field} must be English words and basic punctuation.")
    kept = re.findall(r"[A-Za-z0-9']+", text)
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


class Timings:
    """How long each step of one answer took, for the Server-Timing header (the browser's
    Network → Timing tab draws it) and the log line, so a slow answer names its slow step."""

    def __init__(self) -> None:
        self.ms: dict[str, float] = {}

    @contextmanager
    def step(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            self.ms[name] = (time.perf_counter() - start) * 1000

    def header(self) -> str:
        return ", ".join(f"{name};dur={ms:.1f}" for name, ms in self.ms.items())
