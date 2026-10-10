"""Find the quotation. One question in, passages out, no opinion attached."""
from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import StringConstraints

from backend.config import get_settings
from backend.models.common import Source
from backend.models.daleel import DaleelBook, DaleelHit, DaleelResponse
from backend.services import provenance
from backend.services.daleel import search as daleel_search
from backend.services.daleel import titles
from backend.utils import search_query

router = APIRouter(prefix="/api/daleel", tags=["daleel"])

# On each name, not the list: max_length on the list capped how many, not how long.
BookName = Annotated[str, StringConstraints(max_length=get_settings().daleel_max_book_chars)]


@router.get("/books", response_model=list[DaleelBook])
async def catalogue() -> list[DaleelBook]:
    """Every book the index holds, for the picker to offer.

    Read from the index itself, so a book can only be offered if searching it
    would actually find something. Empty before the index is built, which the
    panel already has a way of saying.
    """
    found = await asyncio.to_thread(daleel_search.books)
    return [
        DaleelBook(
            name=name,
            source=source,
            category=provenance.category_of(source),
            english=titles.english_of(name),
        )
        for name, source in found
    ]


@router.get("", response_model=DaleelResponse)
async def find(
    q: str = Query("", max_length=get_settings().search_max_query_chars),
    books: list[BookName] = Query(default=[]),
) -> DaleelResponse:
    """Passages from the app's books that match what was asked.

    Runs off a prebuilt index, so this is a read, not a search of the books
    themselves. Nothing here calls an AI: this endpoint quotes and stops.
    """
    query = search_query(q)
    if not query:
        return DaleelResponse(query="", hits=[], ready=daleel_search.is_built())

    if not daleel_search.is_built():
        return DaleelResponse(query=query, hits=[], ready=False)

    chosen = await asyncio.to_thread(daleel_search.known_books, books)

    limit = get_settings().daleel_result_limit
    hits = await asyncio.to_thread(daleel_search.search, query, limit, chosen)

    return DaleelResponse(
        query=query,
        books=list(chosen),
        hits=[
            DaleelHit(
                locator=hit.locator,
                arabic=hit.arabic,
                english=hit.english,
                match=hit.match,
                book=hit.book,
                source=Source(**provenance.of(hit.source)),
            )
            for hit in hits
        ],
    )
