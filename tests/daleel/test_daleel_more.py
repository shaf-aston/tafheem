"""Show more: the same question with a bigger page, and whether one could hold more."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import get_settings  # noqa: E402
from backend.routers import daleel as router  # noqa: E402
from backend.services.daleel.search import Hit  # noqa: E402


def _ask(monkeypatch, found: int, limit: int = 0):
    """Ask the router with an index that has `found` passages for anything."""
    asked = []

    def search(query, limit, books, lap):
        asked.append(limit)
        return [Hit("corpus", "corpus", f"1:{n}", "", "", "exact") for n in range(min(found, limit))]

    monkeypatch.setattr(router, "is_built", lambda: True)
    monkeypatch.setattr(router.catalogue, "known_books", lambda books: ())
    monkeypatch.setattr(router.search, "search", search)
    reply = asyncio.run(router.find(q="mercy", books=[], limit=limit, response=None))
    return reply, asked[0]


def test_a_full_page_offers_more(monkeypatch):
    page = get_settings().daleel_result_limit
    reply, limit = _ask(monkeypatch, found=100)
    assert limit == page and len(reply.hits) == page and reply.more


def test_a_short_page_was_everything(monkeypatch):
    reply, _ = _ask(monkeypatch, found=3)
    assert len(reply.hits) == 3 and not reply.more


def test_a_bigger_page_stops_at_the_most_allowed(monkeypatch):
    most = get_settings().daleel_result_limit_max
    reply, limit = _ask(monkeypatch, found=1000, limit=most * 10)
    assert limit == most and not reply.more
