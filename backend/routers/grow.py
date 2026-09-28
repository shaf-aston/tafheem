"""Grow's paths: what to learn to say, in order, and a scholar's words on each.

Read from one hand-written file and served as it is. Nothing here judges a
recitation (that is /api/listen/check and /check-text) and nothing here makes
a ruling: every ruling in the file is a scholar's own sentence, quoted.
"""
from __future__ import annotations

import json
from functools import lru_cache

from fastapi import APIRouter

from backend.config import data_path
from backend.models.schemas import GrowPath

router = APIRouter(prefix="/api/grow", tags=["grow"])


@lru_cache(maxsize=1)
def paths() -> list[GrowPath]:
    """Every path, in the order the page offers them. Read once."""
    raw = json.loads(data_path("grow_path_path").read_text(encoding="utf-8"))
    return [GrowPath(**path) for path in raw["paths"]]


@router.get("/paths", response_model=list[GrowPath])
async def all_paths() -> list[GrowPath]:
    return paths()
