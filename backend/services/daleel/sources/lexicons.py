"""The classical dictionaries, as passages Daleel can quote.

One adapter, instantiated once per credit, the same shape as OpenItiSource and
LibrarySource. Which books exist is data/lexicons.db, built by
scripts/build_lexicons.py; this file names none of them, so a dictionary added
to that build is searchable here without a line of code being written. That is
the whole point of doing it this way: the registry asks the books which credits
they carry, and grows a source for each.

Grouped by credit rather than one source per book, for the reason written at the
top of sources/openiti.py: Daleel guarantees every matching source one slot, and
a source per book would let three dictionaries take three of the nine places on
a page before anything is judged on merit.

The whole entry is one passage, not a sentence of it. These books state what a
root means several lines in, so an index cut at the first sentence would miss
the sentence a reader is looking for; and the panel already folds a long
passage down to four lines with a way to open it, so length is a display
question that has an answer, not a reason to quote less than the book says.

Ibn Faris is deliberately not here. His book is its own source, sources/
maqayees.py, which carries the app's English translation of each entry as well;
indexing him twice would put the same entry on the page under two badges.
"""
from __future__ import annotations

from typing import Iterable

from backend.services import lexicons
from backend.services.arabic_text import normalize_root
from backend.services.daleel.model import Passage


class LexiconsSource:
    """Every entry of every classical dictionary credited to one source."""

    def __init__(self, credit: str) -> None:
        self.id = credit

    def passages(self) -> Iterable[Passage]:
        for title, head, said in lexicons.entries_by_credit(self.id):
            if not said:
                continue
            yield Passage(
                source=self.id,
                book=title,
                # The book, then the root: with several dictionaries under one
                # badge the badge no longer says which one this is.
                locator=f"{title} · {head}",
                arabic=said,
                # The root is already known, so root search reaches these
                # entries as an index hit rather than by matching their prose.
                roots=normalize_root(head),
            )


def credits() -> list[str]:
    """The credits the installed dictionaries carry, in the books' own order."""
    return lexicons.credits()
