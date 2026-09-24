"""The Nahw theory notes, and the teacher's own page behind any of them."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.models.schemas import NoteLibrary
from backend.services import nahw_notes, provenance

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("", response_model=NoteLibrary)
async def get_library() -> NoteLibrary:
    """Every topic's notes, whole.

    Small and fixed, so it is sent once and the page decides what to hide.
    Hiding here would make the reference unreachable, which is the one thing
    the notes are for.
    """
    roles, topics = await asyncio.to_thread(lambda: (nahw_notes.roles(), nahw_notes.topics()))
    return NoteLibrary(roles=roles, topics=topics, source=provenance.of("nahw-notes"))


@router.get("/{key}/page/{page}.png")
async def get_page(key: str, page: int) -> FileResponse:
    """The teacher's own page a block was read from, so a reader can check it."""
    path = await asyncio.to_thread(nahw_notes.page_picture, key, page)
    if path is None:
        raise HTTPException(status_code=404, detail=f"no page {page} of {key}")
    return FileResponse(path, media_type="image/png")
