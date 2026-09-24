"""The classical dictionaries reaching Daleel, and doing it without being named.

The point of this adapter is that nothing lists which dictionaries exist: the
books say which credit they carry and the registry grows a source for each. So
what is worth pinning down is exactly that, a book nobody has ever heard of
appearing in the search simply because it was built into data/lexicons.db.

Written against a two-book database of our own rather than the 66-million
character real one, so the test says what it means and runs in a moment.

Run: python -m pytest tests/test_daleel_lexicons.py
"""
from __future__ import annotations

import sqlite3
import sys
import zlib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.scripts import build_lexicons as builder  # noqa: E402
from backend.services import lexicons  # noqa: E402
from backend.services.daleel.sources.lexicons import LexiconsSource, credits  # noqa: E402


@pytest.fixture
def shelf(tmp_path, monkeypatch):
    """Two dictionaries under one credit, and a third under its own."""
    path = tmp_path / "lexicons.db"
    db = sqlite3.connect(path)
    db.executescript(builder.Shelf.SCHEMA)
    db.executemany(
        "INSERT INTO book VALUES (?,?,?,?,?,?,?,?)",
        [
            ("lisan", "لسان العرب", "The Tongue", "ابن منظور", 711, "ar", "openiti-lexicons", 0),
            ("taj", "تاج العروس", "The Crown", "الزبيدي", 1205, "ar", "openiti-lexicons", 1),
            ("lane", "Lane", "In English", "Lane", 1876, "en", "lane", 2),
        ],
    )
    db.executemany(
        "INSERT INTO entry VALUES (?,?,?,?,?)",
        [
            (book, root, root, root, zlib.compress(said.encode()))
            for book, root, said in [
                ("lisan", "كتب", "ما قاله ابن منظور في كتب"),
                ("taj", "كتب", "ما قاله الزبيدي في كتب"),
                ("lane", "كتب", "what Lane says about كتب"),
                # An entry with nothing in it is not a quotation.
                ("lisan", "زقزق", ""),
            ]
        ],
    )
    db.commit()
    db.close()

    monkeypatch.setattr(lexicons, "DATABASE", path)
    return path


def test_a_dictionary_reaches_daleel_without_anything_naming_it(shelf):
    """Two credits in the file, two sources for the registry to grow."""
    assert credits() == ["openiti-lexicons", "lane"]


def test_books_sharing_a_credit_share_one_source(shelf):
    """Two dictionaries, one badge, and the citation says which is which.

    Grouped so three dictionaries cannot take three of the nine places on a
    page before anything is judged on merit, which is the same reason the
    thirty-four classical books share theirs.
    """
    found = list(LexiconsSource("openiti-lexicons").passages())
    assert {p.book for p in found} == {"لسان العرب", "تاج العروس"}
    assert {p.locator for p in found} == {"لسان العرب · كتب", "تاج العروس · كتب"}
    assert all(p.source == "openiti-lexicons" for p in found)


def test_the_root_is_carried_so_a_root_search_is_an_index_hit(shelf):
    lane = list(LexiconsSource("lane").passages())
    assert [p.roots for p in lane] == ["كتب"]
    assert lane[0].arabic == "what Lane says about كتب"


def test_an_empty_entry_is_not_quoted(shelf):
    """The nearest case nobody asks for: a book with a root but nothing to say.

    A passage with no words is a citation to a blank page.
    """
    assert all(p.arabic for p in LexiconsSource("openiti-lexicons").passages())


def test_no_dictionaries_installed_is_no_sources_rather_than_a_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(lexicons, "DATABASE", tmp_path / "never-built.db")
    assert credits() == []
    assert not list(LexiconsSource("lane").passages())
