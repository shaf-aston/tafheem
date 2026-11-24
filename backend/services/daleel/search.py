"""One question in, the passages worth showing out, best first.

The whole pipeline, in the order it runs, each step in its own package:

    query/expand   typed words → search terms (synonyms, translations, roots)
    index/         terms → candidate passages from daleel.db, a share per source
    match/rank     candidates → ranked, poor typo guesses dropped, spread over books
    match/marks    each kept passage → where its matched words are, for the screen

Try it from a terminal: `python -m backend.services.daleel صبر`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from backend.config import get_settings
from backend.services.core import provenance
from backend.services.text import fts

from backend.services.daleel.index.around import around as neighbours
from backend.services.daleel.index.candidates import candidates
from backend.services.daleel.index.connection import db
from backend.services.daleel.match.answers import answered, share_of
from backend.services.daleel.match.marks import Span, marks
from backend.services.daleel.match.rank import Tier, page_of
from backend.services.daleel.query.expand import Expansion, expand
from backend.services.daleel.query.lexicon import DictionaryLexicon


@dataclass(frozen=True)
class Hit:
    """One quotation, and how it was found."""

    source: str
    book: str
    """Which book of that source it is. With thirty-four books under one badge the
    badge no longer says which one this is."""
    locator: str
    arabic: str
    english: str
    match: str
    """A `Tier` label: exact / partial / related / root / loose. Carried to the
    screen so a loose match can be labelled as one instead of passing for a clean find."""
    arabic_marks: tuple[Span, ...] = ()
    english_marks: tuple[Span, ...] = ()
    """Where in `arabic` and `english` the words that made it a match are, as
    [start, end) character offsets, so the screen can show why it came back
    without knowing anything about how Arabic is matched."""
    id: int = 0
    """Its place in the index, so `around` can show it among its neighbours."""
    answers: bool = True
    """Covers enough of the question to be offered as an answer (match/answers).
    A search where none does is a "not in these books"."""


def search(
    query: str,
    limit: int | None = None,
    books: tuple[str, ...] = (),
    lap: Callable[[str], None] = lambda step: None,
) -> list[Hit]:
    """Passages worth showing for what was typed, best first.

    `books` narrows the search to those books by name. Empty means every book,
    which is the ordinary case. The router passes them through
    `catalogue.known_books` first. `lap` is told as each step ends, which is
    how the command line times them without a second copy of this pipeline.
    """
    settings = get_settings()
    limit = limit or settings.daleel_result_limit

    expansion = expand_query(query)
    lap("expand")
    if expansion.is_empty():
        return []

    conn = db()
    if conn is None:
        return []
    rows = candidates(conn, expansion, limit * settings.daleel_candidate_factor, tuple(books), lap)
    lap("candidates")

    page = page_of(rows, expansion, limit)
    lap("rank")

    shown = (*expansion.phrase_terms, *expansion.typed, *expansion.related)
    rows = [row for _, row in page]
    passes = answered(
        [share_of(row, expansion, settings.daleel_related_weight) for row in rows],
        [provenance.category_of(row.source) for row in rows],
        len(expansion.typed),
        settings.daleel_answer_share,
    )
    hits = [
        Hit(row.source, row.book, row.locator, row.arabic, row.english, Tier(rank[0]).label,
            marks(row.arabic, shown), marks(row.english, shown), row.id, ok)
        for (rank, row), ok in zip(page, passes)
    ]
    lap("marks")
    return hits


def around(passage_id: int) -> list[Hit]:
    """A passage among its neighbours in the same book, for reading it in context."""
    return [
        Hit(row.source, row.book, row.locator, row.arabic, row.english, Tier.EXACT.label, id=row.id)
        for row in neighbours(passage_id, get_settings().daleel_context_span)
    ]


def warm() -> None:
    """One English and one Arabic search, run at startup (services/core/startup).

    The first search after a restart otherwise loads what expanding a question
    needs, the English word forms and the root reader among them, and reads the
    index's first pages from disk: 823ms of expand alone on the server, waited
    out by whoever asked first, twice a deploy, once per copy.
    """
    for query in ("patience", "الصبر"):
        search(query)


def expand_query(query: str) -> Expansion:
    """What was typed, as the terms to search for, with the app's settings."""
    settings = get_settings()
    return expand(
        query,
        DictionaryLexicon(),
        max_expand=settings.daleel_root_expand_max,
        max_translations=settings.daleel_english_expand_max,
        min_trigram_len=fts.TRIGRAM_MIN,
    )
