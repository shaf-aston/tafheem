"""Search the Qur'an through api.quran.com. Free, no key, needs the internet.

Worth keeping alongside the local index because it does something the index
cannot: it searches the translations too, so an English phrase finds its ayah.

Not cached on disk, unlike the ayah lookups in quran_service. An ayah is asked
for again and again and never changes; a search is a different question every
time, and a cache of them would grow without ever being read twice.

The deadline is quran_search_timeout_seconds, not the longer one the ayah
lookups use. There a slow answer is still the only answer; here there is a local
index waiting, and making a reader watch a spinner for fifteen seconds before
falling back to it would be the wrong trade.
"""
from __future__ import annotations

import httpx

from backend.config import get_settings
from backend.services.quran_search.hit import Hit

NAME = "remote"

API = "https://api.quran.com/api/v4"

# What Quran.com returns is its own text of the ayah, credited to it rather than
# to the hand-tagged corpus. Same ayah, different book.
_SOURCE = "translation"


def search(query: str, limit: int) -> list[Hit]:
    """Ayahs Quran.com matches. Raises on any network trouble, so the caller
    can move on to the other way of answering rather than guessing why."""
    response = httpx.get(
        f"{API}/search",
        params={"q": query, "size": limit},
        timeout=get_settings().quran_search_timeout_seconds,
    )
    response.raise_for_status()
    results = response.json().get("search", {}).get("results", [])

    return [
        Hit(
            surah=int(key.partition(":")[0] or 0),
            ayah=int(key.partition(":")[2] or 0),
            arabic_text=hit.get("text", ""),
            source=_SOURCE,
        )
        for hit in results
        if (key := hit.get("verse_key", "0:0"))
    ]
