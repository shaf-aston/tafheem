"""The Tamreen exercise library, and which grammar points it covers."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from backend.models.schemas import TamreenLibrary
from backend.services import tamreen

router = APIRouter(prefix="/api/tamreen", tags=["tamreen"])


@router.get("", response_model=TamreenLibrary)
async def get_library(tag: str | None = None) -> TamreenLibrary:
    """Every exercise, or with ?tag= only the questions filed under that grammar point.

    Small and fixed, so it is sent whole and filtered here rather than paged.
    A tag nobody declared is a 404, not an empty list: an empty list would read
    as "this point is not covered", which is a different and worse answer.
    """
    if tag is not None and tag not in {t["key"] for t in tamreen.tags()}:
        raise HTTPException(status_code=404, detail=f"no such tag: {tag}")
    tags, exercises, coverage = await asyncio.to_thread(
        lambda: (tamreen.tags(), tamreen.exercises(tag), tamreen.coverage())
    )
    return TamreenLibrary(tags=tags, exercises=exercises, coverage=coverage)
