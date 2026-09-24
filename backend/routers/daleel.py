"""Find the quotation. One question in, passages out, no opinion attached."""
from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import StringConstraints

from backend.config import get_settings
from backend.models.schemas import DaleelBook, DaleelHit, DaleelResponse, Source
from backend.services import provenance
from backend.services.daleel import search as daleel_search
from backend.services.daleel import titles

router = APIRouter(prefix="/api/daleel", tags=["daleel"])

# Long enough for a sentence, short enough that nothing enormous is folded and
# expanded per keystroke. A boundary check, not a style rule.
_MAX_QUERY_CHARS = 200

# How many books one search may be narrowed to. There are twenty-three, and a
# request naming hundreds is not a reader choosing; it is a boundary worth
# holding. Naming every book is the same search as naming none.
_MAX_BOOKS = 40

# The longest book name the index holds, with room to spare. A name longer
# than this matches no book, so the only thing a longer one can do is make the
# query bigger.
_MAX_BOOK_CHARS = 120

# The cap has to sit on the name, not on the list of them. Written as
# max_length on the list itself it capped how many names could be sent and
# said nothing at all about their length, which is not what the line above
# describes: a five-hundred-letter book name was accepted.
BookName = Annotated[str, StringConstraints(max_length=_MAX_BOOK_CHARS)]


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
    q: str = Query("", max_length=_MAX_QUERY_CHARS),
    books: list[BookName] = Query(default=[]),
) -> DaleelResponse:
    """Passages from the app's books that match what was asked.

    Runs off a prebuilt index, so this is a read, not a search of the books
    themselves. Nothing here calls an AI: this endpoint quotes and stops.
    """
    query = q.strip()
    if not query:
        return DaleelResponse(query="", hits=[], ready=daleel_search.is_built())

    if not daleel_search.is_built():
        return DaleelResponse(query=query, hits=[], ready=False)

    # Names no book has are dropped rather than refused. A bookmarked search
    # naming a book that has since been removed should show what the rest of
    # the library says, not an error, and certainly not an empty page that
    # reads as "nothing in any book says this".
    known = {name for name, _ in await asyncio.to_thread(daleel_search.books)}
    chosen = tuple(dict.fromkeys(b for b in books[:_MAX_BOOKS] if b in known))

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
