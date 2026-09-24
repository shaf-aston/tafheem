"""The roots of a passage's words, asked for one word at a time.

The Qur'an's passages carry roots because the corpus tagged every word by hand.
A book that was merely typed carries none, so a passage from it can never match
a root search: the very thing the index is best at is closed to it until the
roots are worked out and stored.

Shared by the two hand-typed books rather than written twice. Both are small,
a few hundred words each, and both are read once at index build time; nothing
here ever runs while a search is being answered.
"""
from __future__ import annotations

from typing import Iterable

from backend.services import dictionary_service
from backend.services.arabic_text import bare_letters, normalize_root


def roots_in(words: Iterable[str]) -> str:
    """Every distinct root among these words, space-joined, in the order met."""
    found: list[str] = []
    for word in words:
        bare = bare_letters(word)
        if not bare:
            continue
        for entry in dictionary_service.search_arabic(bare, limit=1):
            root = normalize_root(entry.get("root") or "")
            if root and root not in found:
                found.append(root)
    return " ".join(found)
