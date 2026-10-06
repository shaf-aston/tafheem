"""The narrations of one hadith number (Muslim 1620a, 1620b...) laid against the one being read."""
from __future__ import annotations


def meet(theirs: list[int], viewed: list[int]) -> tuple[list[int], int | None, list[int]]:
    """(own, meeting narrator, borrowed): theirs up to where they join the viewed chain, then the viewed chain's rest.

    Both lists are in text order. The meeting narrator is the first of theirs the viewed chain also names;
    with none, the whole of theirs is their own and nothing is borrowed.
    """
    for i, who in enumerate(theirs):
        if who in viewed:
            return theirs[:i], who, viewed[viewed.index(who) + 1:]
    return list(theirs), None, []
