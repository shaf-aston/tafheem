"""The narrators of the hadith chains: where each is named in a book, his sheet, his hadith, and a search."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query

from backend.config import get_settings
from backend.models.schemas import Narrator, NarratorList, RijalChains, RijalFamily, UsulFacts, RijalHadithRef, RijalSearch
from backend.services import provenance
from backend.services.hadith import loader
from backend.services.rijal import family, store
from backend.services.usul import store as usul
from backend.utils import search_query

router = APIRouter(prefix="/api/rijal", tags=["rijal"])


@router.get("/chains/{collection}/{book}", response_model=RijalChains)
async def get_chains(collection: str, book: int) -> RijalChains:
    if not any(b["number"] == book for b in await asyncio.to_thread(loader.books, collection)):
        raise HTTPException(status_code=404, detail=f"{collection} has no book {book}")
    chains = await asyncio.to_thread(store.chains, collection, book)
    return RijalChains(
        collection=collection, book=book, chains=chains, kin=await asyncio.to_thread(store.kin, collection, book),
        notes=await asyncio.to_thread(usul.notes, collection, book, chains), scale=await asyncio.to_thread(usul.scale),
        links=await asyncio.to_thread(usul.links, collection, book, chains), rulings=await asyncio.to_thread(usul.rulings, collection, book),
        link_rules=await asyncio.to_thread(usul.link_rules) or None,
        ready=await asyncio.to_thread(store.is_built), source=provenance.of("rijal"),
    )


@router.get("/family/{collection}/{number}", response_model=RijalFamily)
async def get_family(collection: str, number: int, part: str = Query("", max_length=3)) -> RijalFamily:
    """The narrations sharing this number, each laid against `part` (the first when not given or unknown)."""
    found = await asyncio.to_thread(family.versions, collection, number, part)
    if found is None:
        shown, rows = await asyncio.to_thread(loader.numbered, collection, number)
        raise HTTPException(status_code=404, detail=f"{collection} {number} has one narration" if rows and shown == number else f"No hadith {number} in {collection}")
    return RijalFamily(**found)


@router.get("/narrators", response_model=NarratorList)
async def list_narrators(generation: str = Query("", max_length=20), offset: int = Query(0, ge=0),
                         limit: int = Query(0, ge=0)) -> NarratorList:
    """Narrators named in our hadith, most narrated first; limit 0 is the configured page, capped at its maximum."""
    cfg = get_settings()
    size = min(limit or cfg.rijal_list_page, cfg.rijal_list_max)
    return NarratorList(**await asyncio.to_thread(store.narrators, generation, offset, size))


@router.get("/narrators/{narrator_id}", response_model=Narrator)
async def get_narrator(narrator_id: int) -> Narrator:
    found = await asyncio.to_thread(store.narrator, narrator_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"No narrator {narrator_id}")
    return Narrator(**found, usul=UsulFacts(**await asyncio.to_thread(usul.facts, narrator_id), source=provenance.of("usul")), source=provenance.of("rijal"))


@router.get("/narrators/{narrator_id}/hadith", response_model=list[RijalHadithRef])
async def get_narrator_hadith(narrator_id: int) -> list[RijalHadithRef]:
    found = await asyncio.to_thread(store.hadith_of, narrator_id, get_settings().rijal_hadith_limit)
    return [RijalHadithRef(**h) for h in found]


@router.get("/search", response_model=RijalSearch)
async def search(q: str = Query("", max_length=get_settings().search_max_query_chars)) -> RijalSearch:
    query = search_query(q)
    return RijalSearch(
        query=query, ready=await asyncio.to_thread(store.is_built), source=provenance.of("rijal"),
        narrators=await asyncio.to_thread(store.search, query, get_settings().rijal_result_limit),
    )
