"""A search that names a hadith by collection and number: "muslim 8", "Sahih al-Bukhari 1379", "abu dawud 12", "muslim:157c".

The collection is recognised from its own id, short name and full name as the
database stores them, so a new collection needs no change here. Every word
typed before the number must be one of that collection's words, and only one
collection may fit ("sahih 8" fits two, so it stays an ordinary search).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Words, then a number with an optional letter (157c), joined by space, colon, slash, hash or dash.
_REFERENCE = re.compile(r"\s*([a-z][a-z\s'\-]*?)[\s:/#\-]*(\d+)([a-z]?)\s*")


@dataclass(frozen=True)
class Reference:
    collection: str
    number: int
    part: str


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower().replace("'", "")))


def parse(query: str, collections: list[tuple[str, str, str, bool]]) -> Reference | None:
    """The hadith a query names, or None when it names no single collection."""
    match = _REFERENCE.fullmatch(query.lower())
    if not match:
        return None
    typed = _words(match[1])
    fits = [cid for cid, name, short, _ in collections if typed <= _words(f"{cid} {name} {short}")]
    if len(fits) != 1:
        return None
    return Reference(fits[0], int(match[2]), match[3])
