"""Search hadith.db's full-text index. One question, matched against the words
of every hadith, in Arabic or in English.

Words are folded the way the index folds them (marks and spelling variants off
Arabic, English stemmed) and matched by prefix. Every word must appear; when no
hadith holds them all, the best hadiths holding any of them are returned
instead, ranked by how rare the matched words are, so a sentence remembered
loosely still finds its hadith.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from backend.config import data_path, get_settings
from backend.services.arabic_text import bare_letters, has_arabic
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
    terms = [_term(t) for t in query.split()]
    terms = [t for t in terms if t]
    if not terms:
        return []

    only, params = _only_collections(collections)
    conn = sqlite3.connect(f"file:{data_path('hadith_index_path')}?mode=ro", uri=True)
    try:
        for joiner in (" ", " OR "):
            rows = conn.execute(
                "SELECT h.collection_id, h.book_number, h.number, h.part, h.arabic, h.english "
                "FROM hadith_fts f JOIN hadith h ON h.rowid = f.rowid "
                f"WHERE hadith_fts MATCH ?{only} "
                "ORDER BY rank LIMIT ?",
                (joiner.join(terms), *params, limit),
            ).fetchall()
            if rows:
                break
    except sqlite3.OperationalError:
        # A query FTS5 cannot parse (bare punctuation) is nothing found, not a server error.
        return []
    finally:
        conn.close()

    return [Hit(collection=c, book=b, number=n, part=p, arabic=a, english=e) for c, b, n, p, a, e in rows]


def _only_collections(collections: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    if not collections:
        return "", ()
    return " AND h.collection_id IN (" + ",".join("?" * len(collections)) + ")", collections


def _term(word: str) -> str:
    """One typed word as a quoted prefix term, folded like the index."""
    word = bare_letters(word) if has_arabic(word) else word
    word = word.replace('"', "")
    return f'"{word}"*' if word.strip() else ""


def cite_url(collection: str, number: int) -> str:
    cite = cite_of(collection)
    return cite.replace("{number}", str(number)) if cite else ""
