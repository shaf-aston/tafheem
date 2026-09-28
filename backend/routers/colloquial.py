"""Spoken Arabic: the dialects on offer, and one unit at a time."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.services.colloquial import loader, schema

router = APIRouter(prefix="/api/colloquial", tags=["colloquial"])


@router.get("", response_model=schema.Catalogue)
async def get_catalogue() -> schema.Catalogue:
    """Every dialect with its unit and lesson titles, and nothing else.

    Titles only, because the tab opens on this list and a unit's own lessons are
    tens of kilobytes each. The unit is fetched when one is chosen.
    """
    return schema.Catalogue(**await asyncio.to_thread(loader.catalogue))


@router.get("/{dialect}/{unit}", response_model=schema.Unit)
async def get_unit(dialect: str, unit: str) -> schema.Unit:
    """One whole unit: every lesson, its phrases, its conversation, its practice.

    Sent whole rather than a lesson at a time: a unit is one file on disk and a
    learner moves between its lessons freely, so paging it would only add a wait
    in the middle of a lesson.
    """
    try:
        return schema.Unit(**await asyncio.to_thread(loader.unit, dialect, unit))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/image/{relative:path}")
async def get_image(relative: str) -> FileResponse:
    """One phrase picture. An approved picture never changes, so it is cached for good."""
    path = await asyncio.to_thread(loader.image_path, relative)
    if path is None:
        raise HTTPException(status_code=404, detail=f"no picture {relative}")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=31536000, immutable"})
