"""The passages that could match: everything the ranking will choose from.

Two indexes over the same folded text, because the trigram index cannot match
anything shorter than three characters, and it does not complain when asked
to, it simply returns nothing. Arabic is full of two-letter words, so a search
for أب would quietly find zero passages and look like an honest "not in the
book". Long terms go to the trigram `passage` table, short ones to the
whole-word `word` table, and only when both find nothing does the loose
"did you mean" path run, so it costs nothing on a query spelled correctly.
"""
from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

from backend.config import get_settings
from backend.services.text import fts

from backend.services.daleel.index.connection import has_table
from backend.services.daleel.index.row import COLUMNS, IndexedPassage
from backend.services.daleel.index.share import fairly
from backend.services.daleel.match.typos import trigrams
from backend.services.daleel.sources import registry

if TYPE_CHECKING:
    from backend.services.daleel.query.expand import Expansion

log = logging.getLogger(__name__)


def candidates(
    conn: sqlite3.Connection, expansion: Expansion, cap: int, books: tuple[str, ...] = ()
) -> list[IndexedPassage]:
    """Rows that could match, with every source getting a share of the places.

    Each source gets its own share rather than the best matches being taken as
    they come. Without that the Qur'an fills the limit every time, simply
    because it has by far the most passages, and the other books were in the
    index, matched the query, and never once reached the screen.
    """
    settings = get_settings()
    per_source = max(cap // max(len(registry.SOURCES), 1), settings.daleel_per_source_least)
    found: dict[tuple[str, str], IndexedPassage] = {}

    # Capped, and the strongest terms come first, so what is dropped is always
    # the weakest end: the typed words survive, then the synonyms, then the
    # roots. A long question still fans out, but not without limit.
    # Deduplicated before the cap: a translation is often its own root (صبر),
    # and each repeat spent one of the twelve places on nothing.
    long_terms = list(dict.fromkeys(t for t in (*expansion.phrase_terms, *expansion.all_terms, *expansion.roots)
                                    if len(t) >= fts.TRIGRAM_MIN))[:settings.daleel_max_terms]

    # The words the trigram index cannot see. They go to the `word` index,
    # which holds the same folded text cut into whole words. This used to be a
    # LIKE with a leading wildcard, which no index can help, so every
    # two-letter word cost a full scan of every book and a search took fifteen
    # and a half seconds.
    short_terms = [t for t in expansion.all_terms
                   if len(t) < fts.TRIGRAM_MIN and is_a_word(t)][:settings.daleel_max_short_terms]

    # An index built before the word table existed still opens and still
    # answers every long word, so it must not turn a short one into a 500.
    # Said out loud with the command that mends it, because the quiet version
    # of this is a two-letter word reading as "no book says this".
    if short_terms and not has_table(conn, "word"):
        log.warning("this index has no word table, so %d short term(s) cannot be "
                    "searched; run: python backend/scripts/daleel/build_daleel_index.py --words",
                    len(short_terms))
        short_terms = []

    # A root is looked for in the roots column alone. In the text it is only
    # three letters in a row: رحم sits inside 2,756 passages of the books, and
    # none of them can rank as a root match, since only the Qur'an and the
    # dictionaries say which roots a passage holds. They came back as loose
    # guesses, were mostly thrown away, and had first taken the share of the
    # passages that did answer: fasting in القدوري found nothing at all.
    words = set(expansion.phrase_terms) | set(expansion.all_terms)
    if long_terms:
        match = " OR ".join(fts.quoted(term) if term in words else f"roots:{fts.quoted(term)}"
                            for term in long_terms)
        for row in fairly(conn, match, per_source, books):
            found[row.key] = row

    # Matched as whole words, which is what the word index holds, so a
    # two-letter query does not match the inside of every longer one.
    #
    # Asked a source at a time, unlike the long terms above, because here the
    # narrowing is free: source and book are indexed columns of the word table,
    # so it is part of the same lookup rather than a filter over its answers.
    for source in registry.SOURCES:
        for term in short_terms:
            for row in map(IndexedPassage._make, conn.execute(
                f"SELECT {COLUMNS} FROM word JOIN passage p ON p.rowid = word.rowid "
                f"WHERE word MATCH ? LIMIT ?",
                (word_match(term, source.id, books), per_source),
            )):
                found.setdefault(row.key, row)

    # Only now, and only if nothing was found spelled the way it was typed.
    if not found:
        for row in loosely(conn, expansion, per_source, books):
            found.setdefault(row.key, row)

    return list(found.values())


def loosely(
    conn: sqlite3.Connection, expansion: Expansion, per_source: int, books: tuple[str, ...] = (),
) -> list[IndexedPassage]:
    """Passages sharing most of a term's three-letter runs. The "did you mean".

    A misspelling keeps nearly all of the runs of the word intended: الرحييم
    and الرحيم share four of five. Matching on the runs rather than on the word
    is what turns SQLite's index into typo tolerance without any model.
    """
    runs = {run for term in expansion.loose for run in trigrams(term)}
    if not runs:
        return []

    match = " OR ".join(fts.quoted(run) for run in sorted(runs))
    return fairly(conn, match, per_source, books)


def is_a_word(term: str) -> bool:
    """Whether the word index would make a word of this at all.

    A single % is not a word, and asking for it is not asking for nothing: the
    tokenizer drops it, the query left behind is the source filter on its own,
    and that matches every passage in the book. One typed % came back as twelve
    quotations picked at random, each labelled a clean match.
    """
    return any(letter.isalnum() for letter in term)


def word_match(term: str, source: str, books: tuple[str, ...]) -> str:
    """One FTS5 query for the word index: this word, in this source, in these books.

    Written as column filters rather than as a WHERE on the joined passage,
    because a WHERE only runs once the index has already found every passage
    holding the word and fetched each one to look at. Each piece is quoted, so
    a term FTS5 would otherwise read as an operator is read as the word it is.
    """
    query = f"source:{fts.quoted(source)} fold:{fts.quoted(term)}"
    if books:
        inside = " OR ".join(map(fts.quoted, books))
        query += f" AND book:({inside})"
    return query
