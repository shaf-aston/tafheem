"""The timelines library, sent whole."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from backend.models.schemas import TimelineAsbab, TimelineLibrary
from backend.services import timelines

router = APIRouter(prefix="/api/timelines", tags=["timelines"])


@router.get("", response_model=TimelineLibrary)
async def get_library() -> TimelineLibrary:
    """About fifty events and their vocabulary: small and fixed, so never paged."""
    return TimelineLibrary(**await asyncio.to_thread(timelines.library))


@router.get("/{section}/{event}/asbab", response_model=TimelineAsbab)
async def get_asbab(section: str, event: str) -> TimelineAsbab:
    """Why the ayahs of this moment came down, one line per report.

    An event nobody declared is a 404 rather than an empty list: an empty list
    would read as "nothing was revealed about this", which is a different answer.
    """
    try:
        return TimelineAsbab(**await asyncio.to_thread(timelines.asbab, section, event))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
