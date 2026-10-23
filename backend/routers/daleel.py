"""Find the quotation. One question in, passages out, no opinion attached."""
from __future__ import annotations

import asyncio
from typing import Annotated

import time

from fastapi import APIRouter, Query, Response
from pydantic import StringConstraints

from backend.config import get_settings
from backend.models.daleel import DaleelBook, DaleelHit, DaleelResponse
from backend.services import provenance
from backend.services.daleel import catalogue, search
from backend.services.daleel.index.connection import is_built
from backend.utils import Timings, search_query

router = APIRouter(prefix="/api/daleel", tags=["daleel"])

# On each name, not the list: max_length on the list capped how many, not how long.
BookName = Annotated[str, StringConstraints(max_length=get_settings().daleel_max_book_chars)]


@router.get("/books", response_model=list[DaleelBook])
async def list_books() -> list[DaleelBook]:
    """Every book the index holds, for the picker to offer.

    Read from the index itself, so a book can only be offered if searching it
    would actually find something. Empty before the index is built, which the
    panel already has a way of saying.
    """
    found = await asyncio.to_thread(catalogue.books)
    return [
        DaleelBook(
            name=name,
            source=source,
            category=provenance.category_of(source),
            english=catalogue.english_of(name),
        )
        for name, source in found
    ]


@router.get("", response_model=DaleelResponse)
async def find(
    q: str = Query("", max_length=get_settings().search_max_query_chars),
    books: list[BookName] = Query(default=[]),
    response: Response = None,
) -> DaleelResponse:
    """Passages from the app's books that match what was asked.

    Runs off a prebuilt index, so this is a read, not a search of the books
    themselves. Nothing here calls an AI: this endpoint quotes and stops.
    """
    query = search_query(q)
    if not query:
        return DaleelResponse(query="", hits=[], ready=is_built())

    if not is_built():
        return DaleelResponse(query=query, hits=[], ready=False)

    timings = Timings()
    with timings.step("books"):
        chosen = await asyncio.to_thread(catalogue.known_books, books)

    # Each step of the search, timed where it ends, so one curl of the live
    # server names the slow step: `curl -sI ... | grep -i server-timing`.
    since = [time.perf_counter()]

    def lap(step: str) -> None:
        now = time.perf_counter()
        timings.ms[step] = (now - since[0]) * 1000
        since[0] = now

    limit = get_settings().daleel_result_limit
    hits = await asyncio.to_thread(search.search, query, limit, chosen, lap)
    if response is not None:  # FastAPI always passes it; a direct call (tests, scripts) may not
        response.headers["Server-Timing"] = timings.header()

    return DaleelResponse(
        query=query,
        books=list(chosen),
        hits=[
            DaleelHit(
                locator=hit.locator,
                arabic=hit.arabic,
                english=hit.english,
                match=hit.match,
                arabic_marks=list(hit.arabic_marks),
                english_marks=list(hit.english_marks),
                book=hit.book,
                source=provenance.of(hit.source),
            )
            for hit in hits
        ],
    )
