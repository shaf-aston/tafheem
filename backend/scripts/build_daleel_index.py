"""Build the Daleel search index from every book the app already holds.

    python backend/scripts/build_daleel_index.py
    python backend/scripts/build_daleel_index.py --only corpus

Reads each registered source, writes every passage into one FTS5 table, and
prints how many came from each book so the count can be checked against what
that book is known to hold.

The index is built here and only here. Nothing is indexed while serving a
request: a search is a read of a finished file, which is what makes it quick.

Rebuilding is safe at any time. It writes a fresh file beside the old one and
moves it into place at the end, so a run that fails leaves the working index
untouched rather than half-written.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services import provenance  # noqa: E402, needs the path above
from backend.services.daleel import registry  # noqa: E402
from backend.services.arabic_text import bare_letters  # noqa: E402

# `book` is carried, not searched: it is what the book filter matches on, and
# a reader typing a question is asking about the text, not about titles. A
# source covering one book leaves it blank and gets its own label, so a book
# name is written down in exactly one place.
# Two columns are searched and two are carried. `fold` is the passage with its
# diacritics and spelling variants flattened, which is what a typed query is
# compared against; `arabic` keeps the book's own spelling for display.
#
# The catalogue is written out as its own small table rather than being asked
# for with SELECT DISTINCT book. FTS5 keeps its columns packed in blocks, so
# reading one column means unpacking all seven of every row: forty-seven names
# cost a fifteen-second scan of a hundred and seventy thousand passages, every
# time the picker opened. The names are known as the passages go by, so they
# are collected then and cost nothing.
# Created by both callers below, so the table is described in exactly one place.
_WORD_SCHEMA = """
-- The same folded text again, cut into whole words instead of three-letter
-- runs. Both are needed and neither replaces the other: trigrams match the
-- inside of a word, which is what makes a misspelling findable, and cannot
-- match anything shorter than three characters at all. Arabic is full of
-- two-letter words, and each one used to cost a full scan of every book:
-- fifteen seconds to answer a search for في. A word index answers the same
-- question in about two milliseconds, because that is what an index is for.
--
-- contentless (content='') because the text is already in `passage` and a
-- second copy of two hundred thousand passages is a hundred megabytes for
-- nothing. The rowid is the passage's own, so a hit is a rowid lookup away
-- from its row.
--
-- `source` and `book` are in here too, and they have to be. Left to `passage`
-- they are UNINDEXED there, so narrowing to one book meant walking every
-- passage the word appears in and fetching each one to look at its source:
-- twelve of those, one per source, took nine and a half seconds for a word as
-- common as في. In here the narrowing is part of the same indexed lookup and
-- the whole search takes milliseconds.
DROP TABLE IF EXISTS word;
CREATE VIRTUAL TABLE word USING fts5(
    source,
    book,
    fold,
    content = '',
    tokenize = 'unicode61'
);
"""

# Which source and book each passage belongs to, as an ordinary table.
# Created by both callers below, so the table is described in exactly one place.
_META_SCHEMA = """
-- The source and book of every passage, out where an index can be put on them.
-- In `passage` they are UNINDEXED, so `WHERE passage MATCH ? AND source = ?`
-- could only be answered by fetching every matching passage in full and
-- looking at it, once per source: a search asking about several words took
-- nineteen seconds, almost all of it spent unpacking passages belonging to a
-- different book than the one being asked for.
--
-- Nine megabytes of rowid, source and book answers the same question from the
-- index alone, and the search takes a third of a second. The index on
-- (source, id) is what lets each source's share be read in order rather than
-- sorted, which is most of the rest.
DROP TABLE IF EXISTS passage_meta;
CREATE TABLE passage_meta (
    id     INTEGER PRIMARY KEY,   -- the passage's own rowid
    source TEXT NOT NULL,
    book   TEXT NOT NULL
);
CREATE INDEX passage_meta_source ON passage_meta (source, id);
"""

_SCHEMA = """
CREATE VIRTUAL TABLE passage USING fts5(
    source UNINDEXED,
    book UNINDEXED,
    locator UNINDEXED,
    arabic UNINDEXED,
    english,
    roots,
    fold,
    tokenize = 'trigram'
);

CREATE TABLE book (
    name   TEXT NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (name, source)
);
""" + _WORD_SCHEMA + _META_SCHEMA


def build(only: str | None = None) -> dict[str, int]:
    # The same checked path the search reads, never a second way of working it
    # out: this function overwrites whatever it names.
    target = data_path("daleel_index_path")
    target.parent.mkdir(parents=True, exist_ok=True)
    scratch = target.with_suffix(".building")

    if scratch.exists():
        scratch.unlink()

    conn = sqlite3.connect(scratch)
    counts: dict[str, int] = {}
    catalogue: set[tuple[str, str]] = set()
    try:
        conn.executescript(_SCHEMA)

        for source in registry.SOURCES:
            if only and source.id != only:
                continue

            started = time.time()
            written = 0
            batch: list[tuple[str, str, str, str, str, str, str]] = []
            one_book = provenance.of(source.id)["label"]

            for passage in source.passages():
                name = passage.book or one_book
                catalogue.add((name, passage.source))
                batch.append((
                    passage.source,
                    name,
                    passage.locator,
                    passage.arabic,
                    passage.english,
                    passage.roots,
                    bare_letters(passage.arabic),
                ))
                if len(batch) >= 1000:
                    _flush(conn, batch)
                    written += len(batch)
                    batch = []

            if batch:
                _flush(conn, batch)
                written += len(batch)

            conn.commit()
            counts[source.id] = written
            print(f"  {source.id:<12} {written:>7,} passages  ({time.time() - started:.1f}s)")

        conn.executemany("INSERT INTO book (name, source) VALUES (?, ?)", sorted(catalogue))
        conn.commit()
        print(f"  {'catalogue':<12} {len(catalogue):>7,} books")
        print(f"  {'words':<12} {fill_words(conn):>7,} passages indexed by word")
        print(f"  {'meta':<12} {fill_meta(conn):>7,} passages filed by source")

        conn.close()
    except Exception:
        conn.close()
        scratch.unlink(missing_ok=True)
        raise

    # One operation, not delete-then-rename: the working index is never gone
    # before its replacement is there.
    scratch.replace(target)
    return counts


def _flush(conn: sqlite3.Connection, batch: list[tuple[str, str, str, str, str, str, str]]) -> None:
    conn.executemany(
        "INSERT INTO passage (source, book, locator, arabic, english, roots, fold) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        batch,
    )


def fill_words(conn: sqlite3.Connection) -> int:
    """Put every passage's whole words into the word index. Returns how many.

    One pass over the finished passages rather than a little of it beside each
    batch: the word index is made only from what is already in `passage`, so
    there is one right moment to make it and it is after they are all in.
    That is also what lets --words upgrade an index built before this existed,
    without reading all forty-seven books again.
    """
    done = 0
    while batch := conn.execute(
        "SELECT rowid, source, book, fold FROM passage WHERE rowid > ? ORDER BY rowid LIMIT 5000",
        (done,),
    ).fetchall():
        conn.executemany("INSERT INTO word (rowid, source, book, fold) VALUES (?, ?, ?, ?)", batch)
        done = batch[-1][0]
    conn.commit()
    return conn.execute("SELECT count(*) FROM word").fetchone()[0]


def fill_meta(conn: sqlite3.Connection) -> int:
    """Copy each passage's source and book into the plain table. Returns how many.

    One statement, because it is a copy of two columns that are already there.
    """
    conn.execute("INSERT INTO passage_meta (id, source, book) "
                 "SELECT rowid, source, book FROM passage")
    conn.commit()
    return conn.execute("SELECT count(*) FROM passage_meta").fetchone()[0]


def add_meta() -> int:
    """Give a finished index its meta table, in place. Returns how many rows.

    Half a minute, against hours to read all forty-seven books again for two
    columns the index already holds.
    """
    conn = sqlite3.connect(data_path("daleel_index_path"))
    try:
        conn.executescript(_META_SCHEMA)
        return fill_meta(conn)
    finally:
        conn.close()


def add_words() -> int:
    """Give a finished index its word table, in place. Returns how many rows.

    Cheap on purpose: rebuilding from the books reaches the same index and
    takes far longer, because the passages do not change.
    """
    conn = sqlite3.connect(data_path("daleel_index_path"))
    try:
        conn.executescript(_WORD_SCHEMA)
        return fill_words(conn)
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Build just this one source id")
    parser.add_argument(
        "--words", action="store_true",
        help="Only add the word table to the index that is already there, in place",
    )
    parser.add_argument(
        "--meta", action="store_true",
        help="Only add the source/book table to the index that is already there, in place",
    )
    args = parser.parse_args()

    if args.meta:
        print("Adding the source and book table")
        print(f"Total: {add_meta():,} passages filed by source")
        return 0

    if args.words:
        print("Adding the word index")
        print(f"Total: {add_words():,} passages indexed by word")
        return 0

    known = {s.id for s in registry.SOURCES}
    if args.only and args.only not in known:
        print(f"No source called {args.only!r}. Known: {', '.join(sorted(known))}")
        return 1

    print("Building Daleel index")
    counts = build(args.only)
    print(f"\nTotal: {sum(counts.values()):,} passages from {len(counts)} book(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
