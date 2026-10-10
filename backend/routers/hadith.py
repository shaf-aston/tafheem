"""Every route of the Hadith tab. One router per address, so the page's URLs never move:
/api/hadith (books and search), /api/rijal (narrators and their chains), /api/usul (rulings)."""
from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import StringConstraints

from backend.config import get_settings
from backend.models.common import Correction
from backend.models.hadith import (
    HadithBook,
    HadithBookResponse,
    HadithChapter,
    HadithCollection,
    HadithEntry,
    HadithReference,
    HadithSearchResponse,
    Narrator,
    NarratorList,
    RijalChains,
    RijalFamily,
    RijalHadithRef,
    RijalSearch,
    UsulFacts,
    UsulTerm,
    UsulTermHadith,
)
from backend.services import provenance
from backend.services.hadith import loader
from backend.services.hadith.chain import cut_of
from backend.services.hadith import search as hadith_search
from backend.services.hadith.rijal import family
from backend.services.hadith.rijal import store as rijal
from backend.services.hadith.usul import store as usul
from backend.utils import search_query

texts = APIRouter(prefix="/api/hadith", tags=["hadith"])
narrators = APIRouter(prefix="/api/rijal", tags=["rijal"])
rulings = APIRouter(prefix="/api/usul", tags=["usul"])

_MAX_COLLECTIONS = 10
CollectionName = Annotated[str, StringConstraints(max_length=60)]


@texts.get("/collections", response_model=list[HadithCollection])
async def get_collections() -> list[HadithCollection]:
    found = await asyncio.to_thread(loader.collections)
    return [HadithCollection(id=cid, name=name, short=short, sahih=sahih) for cid, name, short, *_, sahih in found]


@texts.get("/{collection}/books", response_model=list[HadithBook])
async def get_books(collection: str) -> list[HadithBook]:
    if await asyncio.to_thread(loader.collection_name, collection) is None:
        raise HTTPException(status_code=404, detail=f"No hadith collection called {collection!r}")
    found = await asyncio.to_thread(loader.books, collection)
    return [HadithBook(**b) for b in found]


@texts.get("/{collection}/books/{number}", response_model=HadithBookResponse)
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
        hadiths=[HadithEntry(**h, cut=cut_of(h["arabic"])) for h in hadiths],
        source=provenance.of("hadith"),
    )


@texts.get("/search", response_model=HadithSearchResponse)
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
                cite=loader.cite_url(loader.cite_of(h.collection), h.number, h.part), cut=cut_of(h.arabic),
            )
            for h in found.hits
        ],
        source=provenance.of("hadith"),
    )


@narrators.get("/chains/{collection}/{book}", response_model=RijalChains)
async def get_chains(collection: str, book: int) -> RijalChains:
    chains = await asyncio.to_thread(rijal.chains, collection, book)
    return RijalChains(
        collection=collection, book=book, chains=chains, kin=await asyncio.to_thread(rijal.kin, collection, book),
        notes=await asyncio.to_thread(usul.notes, collection, book, chains), scale=await asyncio.to_thread(usul.scale),
        links=await asyncio.to_thread(usul.links, collection, book, chains), rulings=await asyncio.to_thread(usul.rulings, collection, book),
        link_rules=await asyncio.to_thread(usul.link_rules) or None,
        ready=await asyncio.to_thread(rijal.is_built), source=provenance.of("rijal"),
    )


@narrators.get("/family/{collection}/{number}", response_model=RijalFamily)
async def get_family(collection: str, number: int, part: str = Query("", max_length=3)) -> RijalFamily:
    """The narrations sharing this number, each laid against `part` (the first when not given or unknown)."""
    found = await asyncio.to_thread(family.versions, collection, number, part)
    if found is None:
        raise HTTPException(status_code=404, detail=f"{collection} {number} has fewer than two narrations")
    return RijalFamily(**found)


@narrators.get("/narrators", response_model=NarratorList)
async def list_narrators(generation: str = Query("", max_length=20), offset: int = Query(0, ge=0),
                         limit: int = Query(0, ge=0)) -> NarratorList:
    """Narrators named in our hadith, most narrated first; limit 0 is the configured page, capped at its maximum."""
    cfg = get_settings()
    size = min(limit or cfg.rijal_list_page, cfg.rijal_list_max)
    return NarratorList(**await asyncio.to_thread(rijal.narrators, generation, offset, size))


@narrators.get("/narrators/{narrator_id}", response_model=Narrator)
async def get_narrator(narrator_id: int) -> Narrator:
    found = await asyncio.to_thread(rijal.narrator, narrator_id)
    if found is None:
        raise HTTPException(status_code=404, detail=f"No narrator {narrator_id}")
    return Narrator(**found, usul=UsulFacts(**await asyncio.to_thread(usul.facts, narrator_id), source=provenance.of("usul")), source=provenance.of("rijal"))


@narrators.get("/narrators/{narrator_id}/hadith", response_model=list[RijalHadithRef])
async def get_narrator_hadith(narrator_id: int) -> list[RijalHadithRef]:
    found = await asyncio.to_thread(rijal.hadith_of, narrator_id, get_settings().rijal_hadith_limit)
    return [RijalHadithRef(**h) for h in found]


@narrators.get("/search", response_model=RijalSearch)
async def search_narrators(q: str = Query("", max_length=get_settings().search_max_query_chars)) -> RijalSearch:
    query = search_query(q)
    return RijalSearch(
        query=query, ready=await asyncio.to_thread(rijal.is_built), source=provenance.of("rijal"),
        narrators=await asyncio.to_thread(rijal.search, query, get_settings().rijal_result_limit),
    )


@rulings.get("/terms", response_model=list[UsulTerm])
async def list_terms() -> list[UsulTerm]:
    """Each sort of ruling with its plain meaning and how many hadith carry it; empty while usul.db is not built."""
    return await asyncio.to_thread(usul.terms)


@rulings.get("/terms/{kind}", response_model=UsulTermHadith)
async def get_term(kind: str, offset: int = Query(0, ge=0), limit: int = Query(0, ge=0)) -> UsulTermHadith:
    """A page of the hadith carrying this sort of ruling; limit 0 is the configured page, capped at its maximum."""
    found = await asyncio.to_thread(usul.term, kind, offset, limit)
    if found is None:
        raise HTTPException(status_code=404, detail=f"No sort of ruling {kind}")
    return UsulTermHadith(kind=kind, total=found[0], items=found[1])


router = APIRouter()
for part in (texts, narrators, rulings):
    router.include_router(part)
