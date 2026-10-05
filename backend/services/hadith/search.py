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
Hadith close in meaning (meaning.py) are merged in by rank, so "lose your
temper" finds "do not get angry"; only once some typed word is known, so
nonsense still finds nothing. The chapters the hits fall in come back too.
A collection named among the words ("fasting in bukhari") narrows the search
to it rather than being searched for (reference.py).
"""
from __future__ import annotations

import json
import logging
import sqlite3
from collections import Counter
from dataclasses import dataclass, field

from backend.config import data_path, get_settings
from backend.services import fts
from backend.services.arabic_text import has_arabic
from backend.services.hadith import meaning, reference, repair, words
from backend.services.hadith.lemma import lemma
from backend.services.hadith.loader import books, is_built, numbered
from backend.services.hadith.loader import collections as collections_of

logger = logging.getLogger(__name__)

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
    # A search naming a hadith ("muslim 8"): (collection, number asked, number shown);
    # naming only a collection ("bukhari"), both numbers are empty.
    reference: tuple[str, str, str] | None = None
    # The collections searched, when the search was narrowed to some.
    collections: tuple[str, ...] = ()


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
    asked = reference.read(query, collections_of())
    if len(asked.collections) == 1 and not asked.rest:
        collection = asked.collections[0]
        if asked.number is None:
            return Result(reference=(collection, "", ""), collections=asked.collections)
        shown, rows = numbered(collection, asked.number, asked.part)
        hits = [Hit(c, b, n, p, a, e, json.loads(g)) for c, b, n, p, a, e, g in rows]
        return Result(hits, reference=(collection, f"{asked.number}{asked.part}", str(shown)),
                      collections=asked.collections)

    collections = collections or asked.collections
    typed = words.tokens(asked.rest)
    if not typed:
        return Result()

    only, params = fts.only_in("h.collection_id", collections)
    conn = sqlite3.connect(f"file:{data_path('hadith_index_path')}?mode=ro", uri=True)
    try:
        content = _content(typed, settings)[:_MAX_TERMS]
        # An index built before dictionary forms were stored still answers, by spelling alone.
        forms = any(row[1] == "lemma" for row in conn.execute("PRAGMA table_info(hadith_fts)"))
        terms, corrected, unmatched = _terms(conn, content, forms)
        rows, partial, pool = [], False, limit * _CHAPTER_SAMPLE_FACTOR
        if terms:
            rows = _rows(conn, " AND ".join(terms), only, params, pool)
            if not rows and len(terms) > 1:
                rows = _rows(conn, " OR ".join(terms), only, params, pool)
                partial = bool(rows)
            if meaning.is_built():
                try:
                    near = meaning.nearest(asked.rest, pool, collections)
                except Exception:
                    # A model that cannot load (no network for the first fetch) costs meaning, not search.
                    logger.exception("hadith meaning search failed; answering by words alone")
                    near = []
                rows = _with_meaning(conn, rows, near, settings, pool)
    except sqlite3.OperationalError:
        # A query FTS5 cannot parse (bare punctuation) is nothing found, not a server error.
        return Result()
    finally:
        conn.close()

    hits = [Hit(collection=c, book=b, number=n, part=p, arabic=a, english=e, grades=json.loads(g))
            for c, b, n, p, a, e, g in rows[:limit]]
    return Result(hits, corrected, unmatched, partial, _chapters(rows, settings.hadith_chapter_hints),
                  collections=collections)


def _content(typed, settings) -> list[tuple[str, str]]:
    """The typed words worth searching: all but those about the question itself, unless nothing is left."""
    framing = set(settings.hadith_query_framing)
    return [(t, f) for t, f in typed if f not in framing] or typed


def _terms(conn, content, forms: bool) -> tuple[list[str], list[tuple[str, str]], list[str]]:
    """Index terms for each word, swapping in the likeliest meant word where the typed one matches nothing."""
    terms, corrected, unmatched = [], [], []
    for typed, folded in content:
        if _matches(conn, _term(folded, forms)):
            terms.append(_term(folded, forms))
            continue
        lang = "ar" if has_arabic(folded) else "en"
        near = None if words.is_number(folded) else repair.nearest(conn, folded, lang)
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


def _with_meaning(conn, rows, near: list[tuple[str, int, str]], settings, pool: int) -> list:
    """Word hits and meaning hits as one ranking: each scores 1/(k + rank) in every list it is in."""
    found = [(r[0], r[2], r[3]) for r in rows]
    by_key = dict(zip(found, rows))
    # One primary-key lookup each: a row-value IN list here scans the table (~100ms).
    for key in near:
        if key not in by_key:
            row = conn.execute(
                "SELECT collection_id, book_number, number, part, arabic, english, grades FROM hadith "
                "WHERE collection_id = ? AND number = ? AND part = ?", key).fetchone()
            if row:
                by_key[key] = row
    score = Counter()
    for ranking in (found, near):
        for rank, key in enumerate(ranking, 1):
            score[key] += 1 / (settings.hadith_meaning_fusion_k + rank)
    return [by_key[k] for k, _ in score.most_common(pool) if k in by_key]


def _chapters(rows, top: int) -> list[Chapter]:
    """The books the ranked rows fall in, most first, named from the collection's book list."""
    counted = Counter((row[0], row[1]) for row in rows)
    out = []
    for (collection, number), count in counted.most_common(top):
        name = next((b["name"] for b in books(collection) if b["number"] == number), "")
        if name:
            out.append(Chapter(collection, number, name, count))
    return out


def _term(folded: str, forms: bool = True) -> str:
    """One folded word as an index term: as written, or its dictionary form, or a number however written."""
    if words.is_number(folded):
        return "(" + " OR ".join(fts.quoted(*p) for p in words.number_phrases(folded) if p) + ")"
    alternatives = [fts.quoted(folded)]
    if forms and has_arabic(folded):
        # A final ه may be a ة typed plainly (بالنيه for بالنية); both readings are asked.
        readings = (folded, folded[:-1] + "ة") if folded.endswith("ه") else (folded,)
        for form in dict.fromkeys(filter(None, map(lemma, readings))):
            alternatives.append("lemma : " + fts.quoted(form))
    return "(" + " OR ".join(alternatives) + ")"

