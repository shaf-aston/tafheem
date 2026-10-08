"""What the narrator books say about one narrator, as rows for the narrator page. Pure: no I/O.

Each row is (narrator id, group, kind, value, quote, book, page): the group is a section of the page
(reliability, habits, life, books), the kind says what `value` is, and `quote` is the book's own words
with the page they stand on. The sentence a reader sees is made from kind and value at serve time
(usul.json `facts`), so a wording changes in one place.
"""
from __future__ import annotations

from typing import NamedTuple

from backend.services.usul import mukhtalitin, taqrib
from backend.services.usul.books import Entry


class Fact(NamedTuple):
    narrator: int
    group: str
    kind: str
    value: str
    quote: str
    book: str
    page: str


def died_unread(parsed: taqrib.Parsed, cfg: dict) -> bool:
    """True when the entry gives a year the book writes without its hundreds and his generation cannot supply them."""
    return parsed.death is not None and taqrib.hijri(parsed.death, parsed.generation, cfg["death"]["bands"]) is None


def taqrib_facts(who: int, entry: Entry, parsed: taqrib.Parsed, level: int | None, cfg: dict) -> list[Fact]:
    """The entry's own words for a narrator joined to it: his level, generation and, if read, the year he died."""
    at = lambda quote: entry.where(max(entry.text.find(quote), 0))  # noqa: E731
    rows = []
    if level is not None:
        rows.append(Fact(who, "reliability", "level", str(level), entry.text, "taqrib", entry.where()))
    if parsed.generation:
        rows.append(Fact(who, "life", "generation", str(parsed.generation), parsed.generation_quote, "taqrib",
                         at(parsed.generation_quote)))
    year = taqrib.hijri(parsed.death, parsed.generation, cfg["death"]["bands"]) if parsed.death is not None else None
    if year is not None:   # None where the year has no hundreds and his generation does not say which: left to the gap
        rows.append(Fact(who, "life", "death" if parsed.death >= 100 else "death_hundreds", str(year),
                         parsed.death_quote, "taqrib", entry.where(parsed.death_at)))
    return rows


def tarif_fact(who: int, entry: Entry, level: int) -> Fact:
    return Fact(who, "habits", "tadlis", str(level), entry.text, "tarif", entry.where())


def pair_fact(pair, teacher_name: str, book: str) -> Fact:
    """A scholar's statement that `pair.student` did not hear from (or reach, meet) `pair.teacher`."""
    return Fact(pair.student, "habits", pair.kind, teacher_name, pair.quote, book, pair.page)


def mukhtalit_fact(who: int, entry: Entry) -> Fact:
    return Fact(who, "habits", "mukhtalit", "", mukhtalitin.quote(entry), "mukhtalitin", entry.where())
