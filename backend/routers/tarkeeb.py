"""Worked tarkeeb examples, taken from the books that drew them."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter

from backend.models.schemas import Source, TarkeebExampleBook, TarkeebExamples
from backend.services import provenance, tarkeeb_examples

router = APIRouter(prefix="/api/tarkeeb", tags=["tarkeeb"])


@router.get("/examples", response_model=TarkeebExamples)
async def get_examples() -> TarkeebExamples:
    """Every worked example the app carries, grouped by the book it came from.

    Small and fixed, 47 sentences today, so it is sent in one go and the panel
    filters it in the browser rather than asking again per keystroke.
    """
    topics, books = await asyncio.to_thread(
        lambda: (tarkeeb_examples.topics(), tarkeeb_examples.books())
    )
    return TarkeebExamples(
        topics=topics,
        books=[
            TarkeebExampleBook(**book, source=Source(**provenance.of(book["key"])))
            for book in books
        ],
    )
