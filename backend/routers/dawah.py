"""The dawah questions, sent whole."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter

from backend.services import dawah

router = APIRouter(prefix="/api/dawah", tags=["dawah"])


@router.get("")
async def get_library() -> dict:
    """Every topic, its questions, and the collections its references name."""
    return await asyncio.to_thread(dawah.library)
