"""Search hadith.db's full-text index. One question, matched against the words
of every hadith, in Arabic or in English.

Each typed word is matched as written and, for Arabic, by its dictionary form
(lemma.py), so بالصبر and الصبر meet while the name صبرة stays apart. Words
about the question itself ("hadith about") are dropped; common words need no
dropping, since the ranking already gives them almost no weight (measured: the
yardstick scored the same with or without). A number is matched however a
hadith writes it. Every word must appear; when no hadith holds them all, the
best holding any are returned and flagged partial. A word no hadith holds is
swapped for the likeliest meant word (repair.py) and the swap is reported.
The chapters the hits fall in come back too, for narrowing by topic.
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import dataclass, field

from backend.config import data_path, get_settings
from backend.services.arabic_text import has_arabic
from backend.services.hadith import repair, words
from backend.services.hadith.lemma import lemma
from backend.services.hadith.loader import books, is_built

# How many words one question may put to the index. Past this, more words
# widen the OR fallback rather than narrow the search.
_MAX_TERMS = 12
# How many ranked rows are read so the chapter count has something to count.
_CHAPTER_SAMPLE_FACTOR = 4


@dataclass(frozen=True)
class Hit:
    collection: str
    book: int
    number: int
    part: str
    arabic: str
    english: str
    grades: list[dict]


@dataclass(frozen=True)
class Chapter:
    collection: str
    number: int
    name: str
    count: int


@dataclass(frozen=True)
class Result:
    hits: list[Hit] = field(default_factory=list)
    # (typed, searched instead) for every word swapped for its nearest indexed word.
    corrected: list[tuple[str, str]] = field(default_factory=list)
    # Typed words no hadith holds and nothing is near.
    unmatched: list[str] = field(default_factory=list)
    # True when no hadith holds every word, so the hits hold only some of them.
    partial: bool = False
    chapters: list[Chapter] = field(default_factory=list)


def search(query: str, limit: int | None = None, collections: tuple[str, ...] = ()) -> Result:
    """Hadiths whose Arabic or English holds every word asked for.

    `collections` narrows the search to those collection ids. Empty means
    every collection, the ordinary case; a name no collection has yields
    nothing, on the same reasoning as Daleel's book filter: the caller has
    already dropped unknown names, so this only ever sees real ones.
    """
    if not is_built():
        return Result()

    settings = get_settings()
    limit = limit or settings.hadith_result_limit
    typed = words.tokens(query)
    if not typed:
        return Result()

    only, params = _only_collections(collections)
    conn = sqlite3.connect(f"file:{data_path('hadith_index_path')}?mode=ro", uri=True)
    try:
        asked = _content(typed, settings)[:_MAX_TERMS]
        # An index built before dictionary forms were stored still answers, by spelling alone.
        forms = any(row[1] == "lemma" for row in conn.execute("PRAGMA table_info(hadith_fts)"))
        terms, corrected, unmatched = _terms(conn, asked, settings, forms)
        rows, partial = [], False
        if terms:
            rows = _rows(conn, " AND ".join(terms), only, params, limit * _CHAPTER_SAMPLE_FACTOR)
            if not rows and len(terms) > 1:
                rows = _rows(conn, " OR ".join(terms), only, params, limit * _CHAPTER_SAMPLE_FACTOR)
                partial = bool(rows)
    except sqlite3.OperationalError:
        # A query FTS5 cannot parse (bare punctuation) is nothing found, not a server error.
        return Result()
    finally:
        conn.close()

    hits = [Hit(collection=c, book=b, number=n, part=p, arabic=a, english=e, grades=json.loads(g))
            for c, b, n, p, a, e, g in rows[:limit]]
    return Result(hits, corrected, unmatched, partial, _chapters(rows, settings.hadith_chapter_hints))


def _content(typed, settings) -> list[tuple[str, str]]:
    """The typed words worth searching: all but those about the question itself, unless nothing is left."""
    framing = set(settings.hadith_query_framing)
    return [(t, f) for t, f in typed if f not in framing] or typed


def _terms(conn, asked, settings, forms: bool) -> tuple[list[str], list[tuple[str, str]], list[str]]:
    """Index terms for each word, swapping in the likeliest meant word where the typed one matches nothing."""
    terms, corrected, unmatched = [], [], []
    for typed, folded in asked:
        if _matches(conn, _term(folded, forms)):
            terms.append(_term(folded, forms))
            continue
        lang = "ar" if has_arabic(folded) else "en"
        near = None if words.is_number(folded) else repair.nearest(
            conn, folded, lang, edits_per_letter=settings.hadith_repair_edits_per_letter,
            edit_cost=settings.hadith_repair_edit_cost)
        if near and _matches(conn, _term(near, forms)):
            corrected.append((typed, near))
            terms.append(_term(near, forms))
        else:
            unmatched.append(typed)
    return terms, corrected, unmatched


def _matches(conn, term: str) -> bool:
    return conn.execute("SELECT 1 FROM hadith_fts WHERE hadith_fts MATCH ? LIMIT 1", (term,)).fetchone() is not None


def _rows(conn, match: str, only: str, params, limit: int) -> list:
    return conn.execute(
        "SELECT h.collection_id, h.book_number, h.number, h.part, h.arabic, h.english, h.grades "
        "FROM hadith_fts f JOIN hadith h ON h.rowid = f.rowid "
        f"WHERE hadith_fts MATCH ?{only} "
        "ORDER BY rank LIMIT ?",
        (match, *params, limit),
    ).fetchall()


def _chapters(rows, top: int) -> list[Chapter]:
    """The books the ranked rows fall in, most first, named from the collection's book list."""
    counted = Counter((row[0], row[1]) for row in rows)
    out = []
    for (collection, number), count in counted.most_common(top):
        name = next((b["name"] for b in books(collection) if b["number"] == number), "")
        if name:
            out.append(Chapter(collection, number, name, count))
    return out


def _only_collections(collections: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    if not collections:
        return "", ()
    return " AND h.collection_id IN (" + ",".join("?" * len(collections)) + ")", collections


def _term(folded: str, forms: bool = True) -> str:
    """One folded word as an index term: as written, or its dictionary form, or a number however written."""
    if words.is_number(folded):
        return "(" + " OR ".join(_phrase(p) for p in words.number_phrases(folded) if p) + ")"
    alternatives = [_phrase([folded])]
    if forms and has_arabic(folded):
        # A final ه may be a ة typed plainly (بالنيه for بالنية); both readings are asked.
        readings = (folded, folded[:-1] + "ة") if folded.endswith("ه") else (folded,)
        for form in dict.fromkeys(filter(None, map(lemma, readings))):
            alternatives.append("lemma : " + _phrase([form]))
    return "(" + " OR ".join(alternatives) + ")"


def _phrase(parts: list[str]) -> str:
    """Words that must stand together, quoted for FTS5 (quotes inside a word dropped)."""
    return '"' + " ".join(p.replace('"', "") for p in parts) + '"'
