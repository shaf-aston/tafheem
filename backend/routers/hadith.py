"""Browse a hadith collection by book, or search across it."""
from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import StringConstraints

from backend.config import get_settings
from backend.models.schemas import (
    Correction, HadithBook, HadithBookResponse, HadithChapter, HadithCollection, HadithEntry,
    HadithReference, HadithSearchResponse,
)
from backend.services import provenance
from backend.services.hadith import loader
from backend.services.hadith import search as hadith_search
from backend.utils import search_query

router = APIRouter(prefix="/api/hadith", tags=["hadith"])

_MAX_COLLECTIONS = 10
CollectionName = Annotated[str, StringConstraints(max_length=60)]


@router.get("/collections", response_model=list[HadithCollection])
async def get_collections() -> list[HadithCollection]:
    found = await asyncio.to_thread(loader.collections)
    return [HadithCollection(id=cid, name=name, short=short, sahih=sahih) for cid, name, short, *_, sahih in found]


@router.get("/{collection}/books", response_model=list[HadithBook])
async def get_books(collection: str) -> list[HadithBook]:
    if await asyncio.to_thread(loader.collection_name, collection) is None:
        raise HTTPException(status_code=404, detail=f"No hadith collection called {collection!r}")
    found = await asyncio.to_thread(loader.books, collection)
    return [HadithBook(**b) for b in found]


@router.get("/{collection}/books/{number}", response_model=HadithBookResponse)
async def get_book(collection: str, number: int) -> HadithBookResponse:
    name = await asyncio.to_thread(loader.collection_name, collection)
    if name is None:
        raise HTTPException(status_code=404, detail=f"No hadith collection called {collection!r}")
    books = await asyncio.to_thread(loader.books, collection)
    book = next((b for b in books if b["number"] == number), None)
    if book is None:
        raise HTTPException(status_code=404, detail=f"{collection} has no book {number}")

    hadiths = await asyncio.to_thread(loader.hadiths, collection, number)
    return HadithBookResponse(
        collection=HadithCollection(id=collection, name=name),
        book=HadithBook(**book),
        hadiths=[HadithEntry(**h) for h in hadiths],
        source=provenance.of("hadith"),
    )


@router.get("/search", response_model=HadithSearchResponse)
async def search(
    q: str = Query("", max_length=get_settings().search_max_query_chars),
    collections: list[CollectionName] = Query(default=[]),
) -> HadithSearchResponse:
    query = search_query(q)
    if not query:
        return HadithSearchResponse(query="", ready=await asyncio.to_thread(loader.is_built),
                                     source=provenance.of("hadith"))

    if not await asyncio.to_thread(loader.is_built):
        return HadithSearchResponse(query=query, ready=False, source=provenance.of("hadith"))

    known = {cid for cid, *_ in await asyncio.to_thread(loader.collections)}
    chosen = tuple(dict.fromkeys(c for c in collections[:_MAX_COLLECTIONS] if c in known))

    found = await asyncio.to_thread(hadith_search.search, query, None, chosen)
    return HadithSearchResponse(
        query=query,
        collections=list(found.collections),
        corrected=[Correction(typed=t, used=u) for t, u in found.corrected],
        unmatched=found.unmatched,
        partial=found.partial,
        chapters=[HadithChapter(collection=c.collection, number=c.number, name=c.name, count=c.count)
                  for c in found.chapters],
        reference=HadithReference(collection=found.reference[0], asked=found.reference[1], shown=found.reference[2])
        if found.reference else None,
        hits=[
            HadithEntry(
                collection=h.collection, book=h.book, number=h.number, part=h.part,
                arabic=h.arabic, english=h.english, grades=h.grades,
                cite=loader.cite_url(loader.cite_of(h.collection), h.number, h.part),
            )
            for h in found.hits
        ],
        source=provenance.of("hadith"),
    )
