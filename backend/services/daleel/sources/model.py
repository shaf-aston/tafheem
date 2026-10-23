"""What a searchable book looks like to Daleel, and nothing else.

Daleel quotes books; it never speaks for them. So the unit it deals in is a
Passage: a piece of text exactly as its book has it, plus the address a person
would use to cite it. There is no field for a summary, a paraphrase or an
answer, because producing any of those is not something this tab is allowed
to do.

Every book reaches Daleel through the Source protocol below. The Qur'an, a
grammar rulebook and a classical dictionary have nothing in common as files,
so the protocol asks for the one thing they do share: hand me your passages.
Adding a book later, a fiqh work included, means writing one adapter against
this file and touching nothing else.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, runtime_checkable


@dataclass(frozen=True)
class Passage:
    """One quotable piece of one book.

    Frozen because the index build fans these out across adapters and a
    passage that could be edited in flight is a quotation that could drift
    from what the book actually says.
    """

    source: str
    """Which book. Must match a key in data/sources.json, so the badge, the
    confidence level and the footer all resolve without a second mapping."""

    locator: str
    """How a person cites it: "2:255", "§1.4.4", "ك-ت-ب". Printed on every
    result. A quotation with no address is a rumour, so this is never blank."""

    arabic: str
    """The quotation, exactly as the book has it. Never trimmed, never tidied."""

    english: str = ""
    """The book's own English where it has one. Empty is normal, not a defect."""

    book: str = ""
    """Which book of that source this came from, named as a reader would say it.

    A source is a badge and a badge can cover many books: thirty-four classical
    works share one, and the commentaries share another. Without this the index
    can group and rank, but it cannot answer "only Quduri", because the book's
    name exists nowhere but inside the citation a person reads.

    Left blank by a source that covers exactly one book: the index then fills
    it with that source's own label, so the name is written down once, in
    data/sources.json, instead of a second time here."""

    roots: str = ""
    """Space-joined roots occurring in the passage, worked out at build time.

    Precomputed rather than derived per query because this is what makes root
    search cheap: matching كتاب against كاتب becomes an index hit rather than
    a scan."""


@runtime_checkable
class Source(Protocol):
    """A book Daleel can search.

    Deliberately tiny. The moment this protocol needs a second method, the
    thing being added probably belongs in search or ranking, not in a book.
    """

    id: str

    def passages(self) -> Iterable[Passage]:
        """Every quotable passage in the book, in the book's own order.

        An iterable, not a list: the Qur'an is 6,236 passages and the
        dictionary is 23,715, and the index builder streams them rather than
        holding every book in memory at once.
        """
        ...
