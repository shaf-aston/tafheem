"""The narrators of the hadith chains: where each is named in a book, his sheet, his hadith, and a search."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query

from backend.config import get_settings
from backend.models.schemas import Narrator, RijalChains, RijalHadithRef, RijalSearch
from backend.services import provenance
from backend.services.rijal import store

router = APIRouter(prefix="/api/rijal", tags=["rijal"])


@router.get("/chains/{collection}/{book}", response_model=RijalChains)
async def get_chains(collection: str, book: int) -> RijalChains:
    return RijalChains(
        collection=collection, book=book, chains=await asyncio.to_thread(store.chains, collection, book),
        ready=await asyncio.to_thread(store.is_built), source=provenance.of("rijal"),
    )


@router.get("/narrators/{narrator_id}", response_model=Narrator)
async def get_narrator(narrator_id: int) -> Narrator:
    found = await asyncio.to_thread(store.narrator, narrator_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"No narrator {narrator_id}")
    return Narrator(**found, source=provenance.of("rijal"))


@router.get("/narrators/{narrator_id}/hadith", response_model=list[RijalHadithRef])
async def get_narrator_hadith(narrator_id: int) -> list[RijalHadithRef]:
    found = await asyncio.to_thread(store.hadith_of, narrator_id, get_settings().rijal_result_limit)
    return [RijalHadithRef(**h) for h in found]


@router.get("/search", response_model=RijalSearch)
async def search(q: str = Query("", max_length=get_settings().search_max_query_chars)) -> RijalSearch:
    query = q.strip()
    return RijalSearch(
        query=query, ready=await asyncio.to_thread(store.is_built), source=provenance.of("rijal"),
        narrators=await asyncio.to_thread(store.search, query, get_settings().rijal_result_limit),
    )
