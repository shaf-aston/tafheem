"""Narrowing a Daleel search to a named book.

Fourteen classical works share one badge, so the badge cannot say which book a
quotation is from and the reader cannot ask one book a question. These tests
cover the field that fixed that: a book name on every row of the index, and a
filter that honours it on every path into the index.

Built against a hand-made index of four rows rather than the app's real one, so
the tests say what they mean and do not change answer when a book is imported.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.scripts.daleel.build_daleel_index import (  # noqa: E402
    _META_SCHEMA,
    fill_meta,
)
from backend.services.daleel import catalogue, search  # noqa: E402
from backend.services.daleel.index import connection, share  # noqa: E402

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
""" + _META_SCHEMA

# The word every row of the fixture holds, so a search for it reaches all three.
_ARABIC_PRAYER = "\u0635\u0644\u0627\u0629"

# Two books under one badge, which is the case the filter exists for, plus one
# book under a badge of its own so the listing has to cope with both.
_ROWS = [
    ("fiqh-books", "مختصر القدوري", "باب النوافل", "صلاة النافلة", "", "صلي", "صلاة النافلة"),
    ("fiqh-books", "بداية المبتدي", "كتاب الصلاة", "وصلاة النافلة جائزة", "", "صلي", "وصلاة النافلة جائزة"),
    ("corpus", "Quranic Arabic Corpus", "2:43", "وأقيموا الصلاة", "", "صلي", "وأقيموا الصلاة"),
]


@pytest.fixture()
def index(tmp_path, monkeypatch):
    """A three-row index, put where the search looks for the real one."""
    path = tmp_path / "daleel.db"
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    conn.executemany("INSERT INTO passage VALUES (?, ?, ?, ?, ?, ?, ?)", _ROWS)
    # The catalogue the build writes beside the passages: books() reads this,
    # not the passages, so the fixture writes both the way the build does.
    conn.executemany(
        "INSERT INTO book (name, source) VALUES (?, ?)",
        sorted({(row[1], row[0]) for row in _ROWS}),
    )
    # Which source each passage belongs to, filled the way the build fills it
    # rather than by hand: the search reads this table on every path into the
    # index, so a fixture that made its own would be testing a different file.
    fill_meta(conn)
    conn.commit()
    conn.close()
    monkeypatch.setattr(connection, "data_path", lambda _key: path)
    return path


def test_every_book_is_listed_with_its_source(index):
    assert catalogue.books() == [
        ("Quranic Arabic Corpus", "corpus"),
        ("بداية المبتدي", "fiqh-books"),
        ("مختصر القدوري", "fiqh-books"),
    ]


def test_no_index_lists_no_books(tmp_path, monkeypatch):
    monkeypatch.setattr(connection, "data_path", lambda _key: tmp_path / "nothing.db")
    assert catalogue.books() == []


def test_naming_a_book_searches_only_that_book(index):
    hits = search.search("النافلة", 9, ("مختصر القدوري",))
    assert hits, "the book does hold this word"
    assert {hit.book for hit in hits} == {"مختصر القدوري"}


def test_naming_nothing_searches_everything(index):
    hits = search.search("النافلة", 9)
    assert {hit.book for hit in hits} == {"مختصر القدوري", "بداية المبتدي"}


def test_two_books_of_one_badge_can_be_told_apart(index):
    """The whole point: one badge, and each hit still says which book it is."""
    hits = search.search("النافلة", 9)
    assert {hit.source for hit in hits} == {"fiqh-books"}
    assert len({hit.book for hit in hits}) == 2


def test_a_book_no_one_has_finds_nothing_rather_than_everything(index):
    """A filter that quietly fell back to every book would be worse than an
    error: the reader would read another book's answer as this one's."""
    assert search.search("النافلة", 9, ("كتاب لا وجود له",)) == []


def test_the_filter_reaches_the_loose_path_too(index):
    """A misspelling takes a different route into the index. A filter honoured
    on the ordinary path and forgotten on this one would hand back the books
    the reader had just excluded, at the moment they are least expecting it."""
    misspelt = "النافللة"
    assert search.search(misspelt, 9), "the loose path finds it at all"
    hits = search.search(misspelt, 9, ("مختصر القدوري",))
    assert {hit.book for hit in hits} == {"مختصر القدوري"}


def test_a_book_name_with_a_quote_in_it_is_not_sql(index):
    """Book names arrive as typed text. Nothing here builds SQL out of one."""
    assert search.search("النافلة", 9, ("' OR 1=1 --",)) == []


def test_every_source_gets_its_share_of_the_places(index):
    """The fairness the per-source share exists for, on an index where one
    source has more matching passages than the whole limit allows.

    Asked for two places in all, with two fiqh passages and one of the Qur'an
    matching: the Qur'an has to keep one of them. It is the case the old
    per-source loop was written for, and the one a single ranked query lost.
    """
    conn = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    try:
        rows = share.fairly(conn, [f'"{_ARABIC_PRAYER}"'], 1)
    finally:
        conn.close()

    assert {row[0] for row in rows} == {"fiqh-books", "corpus"}


def test_a_share_of_one_book_is_still_only_that_book(index):
    """The narrowing runs before the share is handed out, not after it: a book
    filter that ran afterwards would spend the Qur'an's place on a passage the
    reader had just excluded and show one hit instead of two."""
    conn = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    try:
        rows = share.fairly(conn, [f'"{_ARABIC_PRAYER}"'], 8, ("\u0645\u062e\u062a\u0635\u0631 \u0627\u0644\u0642\u062f\u0648\u0631\u064a",))
    finally:
        conn.close()

    assert [row[1] for row in rows] == ["\u0645\u062e\u062a\u0635\u0631 \u0627\u0644\u0642\u062f\u0648\u0631\u064a"]


def test_a_share_holds_the_better_passage_not_the_earlier_one(index):
    """One place for the fiqh badge, and two of its passages match. The later
    one holds both words asked for, the earlier only one: the place goes to the
    later. Cut by passage order, it went to whichever came first in the file."""
    conn = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    try:
        rows = share.fairly(conn, ['"النافلة"', '"جائزة"'], 1)
    finally:
        conn.close()

    assert [row[1] for row in rows] == ["بداية المبتدي"]


def test_the_command_line_runs_the_same_search(index, capsys):
    """`python -m backend.services.daleel` is how a person or an agent asks
    without the web server; it must answer as the API does."""
    import json

    from backend.services.daleel.__main__ import main

    assert main(["النافلة", "--book", "مختصر القدوري", "--json"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert [hit["book"] for hit in printed] == ["مختصر القدوري"]

    assert main(["النافلة", "--explain"]) == 0
    out = capsys.readouterr().out
    assert "candidates" in out and "[exact]" in out


def test_context_stays_inside_its_own_book(index):
    """Opening a passage in context shows its book's neighbours in order and
    never the next book's text, which would read as part of the quotation."""
    first = search.search("النافلة", 9, ("مختصر القدوري",))[0]
    shown = search.around(first.id)
    assert [hit.book for hit in shown] == ["مختصر القدوري"]
    assert shown[0].id == first.id


def test_unknown_passage_has_no_context(index):
    assert search.around(999) == []


def test_every_quote_is_the_book_word_for_word(index):
    """The trust rule: what the screen quotes is exactly what the index holds."""
    stored = {(r[1], r[2]): r[3] for r in _ROWS}
    hits = search.search("النافلة", 9)
    assert hits
    for hit in hits:
        assert hit.arabic == stored[(hit.book, hit.locator)]


def test_a_question_the_books_do_not_cover_finds_nothing(index):
    assert search.search("cryptocurrency mining", 9) == []


def test_a_question_of_several_words_needs_a_book_not_only_a_dictionary(index, monkeypatch):
    """Dictionaries hold nearly every word, so they alone never answer a
    question of several words; a book holding the words does."""
    monkeypatch.setattr(search.provenance, "category_of", lambda key: "Dictionary")
    assert not any(hit.answers for hit in search.search("صلاة النافلة", 9))
    monkeypatch.setattr(search.provenance, "category_of", lambda key: "Fiqh")
    assert any(hit.answers for hit in search.search("صلاة النافلة", 9))
