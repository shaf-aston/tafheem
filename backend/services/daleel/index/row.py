"""One row of the index, as every query reads it.

Not the build's `sources.model.Passage`, which is what an adapter writes; this
is what comes back out, with the book it was filed under and its folded text.
"""
from __future__ import annotations

from typing import NamedTuple


class IndexedPassage(NamedTuple):
    source: str
    book: str
    locator: str
    arabic: str
    english: str
    roots: str
    fold: str
    id: int
    """The row's own number. Neighbouring numbers in one book are its
    neighbouring passages, because the build writes each book in order."""

    @property
    def key(self) -> tuple[str, str]:
        """One passage, however many queries found it."""
        return self.source, self.locator


# The passage columns, read through the FTS table's alias `p`; `id` is FTS5's rowid.
COLUMNS = ", ".join(f"p.{'rowid' if name == 'id' else name}" for name in IndexedPassage._fields)
