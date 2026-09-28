"""Search hadith.db's full-text index. One question, matched against the words
of every hadith, in Arabic or in English.

Simpler than daleel's search on purpose: a hadith collection is words a
narrator actually said, not a dictionary of roots and synonyms, so there is no
root-expansion or loose/typo path here, only what was typed. Every word typed
must appear (FTS5's own AND between quoted terms) rather than any of them,
since "the reward of patience" asked as four ORed words would return half the
book.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from backend.config import data_path, get_settings
from backend.services.hadith.loader import cite_of, is_built


@dataclass(frozen=True)
class Hit:
    collection: str
    book: int
    number: int
    part: str
    arabic: str
    english: str


def search(query: str, limit: int | None = None, collections: tuple[str, ...] = ()) -> list[Hit]:
    """Hadiths whose Arabic or English holds every word asked for.

    `collections` narrows the search to those collection ids. Empty means
    every collection, the ordinary case; a name no collection has yields
    nothing, on the same reasoning as Daleel's book filter: the caller has
    already dropped unknown names, so this only ever sees real ones.
    """
    if not is_built():
        return []

    limit = limit or get_settings().hadith_result_limit
    terms = [t for t in query.split() if t.strip()]
    if not terms:
        return []

    match = " ".join(f'"{_escape(t)}"' for t in terms)
    only, params = _only_collections(collections)

    conn = sqlite3.connect(f"file:{data_path('hadith_index_path')}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT h.collection_id, h.book_number, h.number, h.part, h.arabic, h.english "
            "FROM hadith_fts f JOIN hadith h ON h.rowid = f.rowid "
            f"WHERE hadith_fts MATCH ?{only} "
            "ORDER BY rank LIMIT ?",
            (match, *params, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        # A query FTS5 cannot parse (bare punctuation, an operator with
        # nothing either side) is not a server error, it is nothing found.
        return []
    finally:
        conn.close()

    return [Hit(collection=c, book=b, number=n, part=p, arabic=a, english=e) for c, b, n, p, a, e in rows]


def _only_collections(collections: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    if not collections:
        return "", ()
    return " AND h.collection_id IN (" + ",".join("?" * len(collections)) + ")", collections


def _escape(term: str) -> str:
    return term.replace('"', '""')


def cite_url(collection: str, number: int) -> str:
    cite = cite_of(collection)
    return cite.replace("{number}", str(number)) if cite else ""
