"""The word index: short Arabic words, found by an index instead of a scan.

What is proved here is that the short path is indexed and narrows the way the
long one does. How fast it is belongs to a stopwatch, not a test suite: it was
15.5 seconds for في and is now 0.03, measured against the real index.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
from __future__ import annotations

import logging
import sqlite3

import pytest

from backend.config import data_path
from backend.services.daleel import search
from backend.services.daleel.expand import Expansion

FI = "\u0641\u064a"          # two letters, so the trigram index cannot see it
ALLAH = "\u0627\u0644\u0644\u0647"


@pytest.fixture(scope="module")
def index():
    """The real index, read-only. Skipped where it has not been built."""
    path = data_path("daleel_index_path")
    if not path.exists():
        pytest.skip("the Daleel index is not built here")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        conn.execute("SELECT 1 FROM word LIMIT 1")
    except sqlite3.OperationalError:
        pytest.skip("this index predates the word table; run build_daleel_index.py --words")
    yield conn
    conn.close()


def test_a_two_letter_word_is_found_at_all(index):
    """The whole reason the table exists: the trigram tokenizer returns nothing
    for anything under three characters, and does not say so."""
    assert index.execute("SELECT count(*) FROM passage WHERE passage MATCH ?", (f'"{FI}"',)).fetchone()[0] == 0
    assert index.execute("SELECT count(*) FROM word WHERE word MATCH ?", (f'fold:"{FI}"',)).fetchone()[0] > 0


def test_it_matches_whole_words_and_not_the_inside_of_longer_ones(index):
    """A two-letter query must not match every word that contains those two
    letters, which is what a LIKE with wildcards at both ends would do."""
    # Read back from `passage`, because the word table is contentless: it
    # holds the index and not a second copy of the text.
    rows = index.execute(
        "SELECT p.fold FROM word JOIN passage p ON p.rowid = word.rowid "
        "WHERE word MATCH ? LIMIT 50", (f'fold:"{FI}"',),
    ).fetchall()
    assert rows
    assert all(FI in text.split() for (text,) in rows)


def test_narrowing_to_a_source_is_part_of_the_lookup(index):
    """Not a filter applied afterwards: as a WHERE on the joined passage it took
    nine and a half seconds, because every passage holding the word had to be
    fetched before it could be ruled out."""
    plan = [row[-1] for row in index.execute(
        "EXPLAIN QUERY PLAN SELECT p.locator FROM word JOIN passage p ON p.rowid = word.rowid "
        "WHERE word MATCH ? LIMIT 10", (search._word_match(FI, "corpus", ()),),
    )]
    assert any("word" in line for line in plan)
    for (source,) in index.execute(
        "SELECT p.source FROM word JOIN passage p ON p.rowid = word.rowid "
        "WHERE word MATCH ? LIMIT 20", (search._word_match(FI, "corpus", ()),),
    ):
        assert source == "corpus"


def test_a_book_filter_narrows_the_same_lookup(index):
    name = index.execute("SELECT name FROM book LIMIT 1").fetchone()[0]
    source = index.execute("SELECT source FROM book WHERE name = ?", (name,)).fetchone()[0]
    for (book,) in index.execute(
        "SELECT p.book FROM word JOIN passage p ON p.rowid = word.rowid "
        "WHERE word MATCH ? LIMIT 20",
        (search._word_match(FI, source, (name,)),),
    ):
        assert book == name


def test_a_long_word_still_goes_to_the_trigram_index(index):
    """The two are not swapped for each other. Trigrams are what make a
    misspelling findable, and only they match the inside of a word."""
    assert index.execute(
        "SELECT count(*) FROM passage WHERE passage MATCH ?", (f'"{ALLAH}"',),
    ).fetchone()[0] > 0


def test_a_word_the_books_do_not_hold_is_answered_with_nothing(index):
    """Nothing found must stay nothing found. A word index that quietly fell
    back to matching pieces would turn "no book says this" into a page of near
    misses with nothing to tell them apart by."""
    nonsense = "\u0632\u0642\u0646\u0642\u0646\u0632"
    assert index.execute(
        "SELECT count(*) FROM word WHERE word MATCH ?", (f'fold:"{nonsense}"',),
    ).fetchone()[0] == 0


def test_an_index_from_before_this_table_answers_instead_of_failing(caplog):
    """An index built before the word table still opens, still holds every
    passage, and still answers every long word. A two-letter word must find
    nothing in it, not break the search: it was an unguarded query and SQLite
    says "no such table", which reached the reader as a 500 on the whole page.
    """
    old = sqlite3.connect(":memory:")
    old.executescript(
        "CREATE VIRTUAL TABLE passage USING fts5("
        "source UNINDEXED, book UNINDEXED, locator UNINDEXED, arabic UNINDEXED,"
        " english, roots, fold, tokenize = 'trigram');"
    )
    expansion = Expansion(typed=(FI,), related=(), roots=(), loose=())

    with caplog.at_level(logging.WARNING):
        assert search._candidates(old, expansion, 20) == []

    assert "--words" in caplog.text, "the log must name the command that mends it"
    old.close()


def test_a_passage_both_indexes_find_is_shown_once(index):
    """The two indexes overlap on purpose, and a question with a short word and
    a long one puts the same passage in reach of both. It must be one result.
    The two queries select their columns through different names, so the guard
    against a double is that both tuples carry source and locator in the same
    place; nothing else would notice if one of them moved.
    """
    both = f"{FI} {ALLAH}"
    hits = search.search(both)
    assert hits, "a query this common must find something, or this proves nothing"
    seen = [(hit.source, hit.locator) for hit in hits]
    assert len(set(seen)) == len(seen)
