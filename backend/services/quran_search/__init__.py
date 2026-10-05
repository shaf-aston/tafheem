"""Find the ayahs, whether or not there is a network.

The whole of this module's interface is `search` below. Two ways of answering sit
behind it, and a caller learns about neither: the router asks for ayahs and gets
ayahs.

  local.py   the index built from the app's own hand-tagged corpus, offline.
  remote.py  api.quran.com, which searches translations as well as the Arabic.

Neither is simply better. Quran.com can find an ayah by its English; the local
index ranks Arabic by the words shared with the query, answers in under a
quarter of a second, and answers at all when the internet is gone. Measured
2026-08-26: Quran.com replies in ~770ms with a working connection, and takes
15.7 seconds to give up without one, returning nothing. That number is why the
fallback exists, and why a search gives Quran.com a much shorter deadline than
an ayah lookup does.

Which answered is never hidden. Each hit carries its own source, so a local hit
is badged as the corpus and a remote one as Quran.com, because they really are
two different books and the app's rule is that those never look alike.
"""
from __future__ import annotations

import logging

from backend.config import get_settings
from backend.services.arabic_text import has_arabic
from backend.services.quran_search import local, remote
from backend.services.quran_search.hit import Hit
from backend.services.timing import timed

logger = logging.getLogger(__name__)

__all__ = ["Hit", "search"]


def search(query: str, limit: int | None = None) -> tuple[list[Hit], list[tuple[str, str]]]:
    """Ayahs containing what was typed, and any typed words swapped to find them.

    An Arabic word no ayah holds is swapped for the likeliest meant one first
    (local.respelt), and the swaps are returned as (typed, used) for the reader
    to see. Empty is a real answer and the only honest one when the network is
    down and the index has never been built. It is never an exception: a
    search that finds nothing is an ordinary outcome of searching.
    """
    limit = limit or get_settings().quran_search_limit
    query, swaps = local.respelt(query) if has_arabic(query) else (query, [])
    return _first_answer(query, limit), swaps


def _first_answer(query: str, limit: int) -> list[Hit]:
    """The hits of the first search that has any, in the configured order."""
    order = _order(get_settings().quran_search_source, query)

    for adapter in order:
        try:
            hits = timed("quran search", adapter.search, query, limit, adapter=adapter.NAME, chars=len(query))
        except Exception as exc:  # noqa: BLE001, a dead network must not be an error page
            logger.info("quran search  adapter=%s  failed: %s", adapter.NAME, exc)
            continue
        if hits:
            return hits

    return []


def _order(source: str, query: str) -> tuple:
    """Which adapters to try, in order.

    "auto" asks the local index first for Arabic, and Quran.com first for
    anything else. The index ranks Arabic by shared words, so a recited phrase
    finds its ayahs; Quran.com answered the same recitation with 39:74, because
    it matches loosely and orders by its own lights. English it cannot answer at
    all, and Quran.com searches the translations. Each is what catches the other
    falling over. Pinning to one is for testing and for a reader who wants the
    app to stop reaching for the internet at all.
    """
    if source == "online":
        return (remote,)
    if source == "local":
        return (local,)
    return (local, remote) if has_arabic(query) else (remote, local)
