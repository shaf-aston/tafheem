"""The narrations of one hadith number (Muslim 1620a, 1620b...) laid against the one being read."""
from __future__ import annotations

from backend.services.rijal import store
from backend.services.usul import store as usul


def meet(theirs: list[int], viewed: list[int]) -> tuple[list[int], int | None, list[int]]:
    """(own, meeting narrator, borrowed): theirs up to where they join the viewed chain, then the viewed chain's rest.

    Both lists are in text order. The meeting narrator is the first of theirs the viewed chain also names;
    with none, the whole of theirs is their own and nothing is borrowed.
    """
    for i, who in enumerate(theirs):
        if who in viewed:
            return theirs[:i], who, viewed[viewed.index(who) + 1:]
    return list(theirs), None, []


def versions(collection: str, number: int, part: str = "") -> dict | None:
    """RijalFamily's data: each narration of the number laid against `part` (the first if not given or unknown); None under two."""
    found = store.family(collection, number)
    if len(found) < 2:
        return None
    viewed = next((f for f in found if f["part"] == part), found[0])
    by_id = {n["id"]: n for f in found for n in f["narrators"]}
    named = lambda seq: [by_id[i] for i in seq]  # noqa: E731
    words = usul.family_words(collection, number)
    parts = []
    for f in found:
        own, met, borrowed = meet([n["id"] for n in f["narrators"]], [n["id"] for n in viewed["narrators"]])
        parts.append(f | {"own": named(own), "meet": by_id[met] if met is not None else None, "borrowed": named(borrowed),
                          **(words["parts"].get(f["part"], {}) if words else {})})
    return {"viewed": viewed["part"], "parts": parts, "places": usul.family_places(collection, number, len(found)), "words": words}
