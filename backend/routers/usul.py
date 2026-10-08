"""What classical ruling books say of our hadith: the sorts of ruling and the hadith carrying each."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query

from backend.config import get_settings
from backend.models.schemas import UsulTerm, UsulTermHadith
from backend.services.usul import store
from backend.services.usul.rule import rule

router = APIRouter(prefix="/api/usul", tags=["usul"])


@router.get("/terms", response_model=list[UsulTerm])
async def list_terms() -> list[UsulTerm]:
    """Each sort of ruling with its plain meaning and how many hadith carry it; empty while usul.db is not built."""
    return await asyncio.to_thread(store.terms)


@router.get("/terms/{kind}", response_model=UsulTermHadith)
async def get_term(kind: str, offset: int = Query(0, ge=0), limit: int = Query(0, ge=0)) -> UsulTermHadith:
    """A page of the hadith carrying this sort of ruling; limit 0 is the configured page, capped at its maximum."""
    if kind not in rule()["rulings"]["kinds"]:
        raise HTTPException(status_code=404, detail=f"No sort of ruling {kind}")
    cfg = get_settings()
    total, items = await asyncio.to_thread(store.term, kind, offset, min(limit or cfg.usul_term_page, cfg.usul_term_max))
    return UsulTermHadith(kind=kind, total=total, items=items)
