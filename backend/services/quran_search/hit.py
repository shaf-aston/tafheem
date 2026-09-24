"""What a search returns, one ayah of it.

Its own file so that both adapters and the package's front door can use it
without importing each other in a circle. Nothing else belongs in here: it is
the shape, not the search.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Hit:
    """One ayah, and where the match came from."""

    surah: int
    ayah: int
    arabic_text: str
    source: str
    """A key in data/sources.json: "corpus" for the local index, "translation"
    for Quran.com. The badge is worked out from this, never guessed."""
