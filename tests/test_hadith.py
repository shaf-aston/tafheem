"""The Hadith module: browsing a collection by book, and searching its text.

Built against a hand-made database of three hadiths rather than the app's real
one, the way test_daleel_books.py tests Daleel's index: the tests say what
they mean and do not change answer when a collection is fetched.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.main import app  # noqa: E402
from backend.scripts.build_hadith_index import _SCHEMA  # noqa: E402
from backend.services.arabic_text import bare_letters  # noqa: E402
from backend.services.hadith import loader, search  # noqa: E402

_ROWS = [
    # collection_id, book_number, number, part, arabic, english
    ("bukhari", 1, 1, "", "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ", "Actions are judged by intentions"),
    ("bukhari", 1, 2, "", "كَيْفَ كَانَ بَدْءُ الْوَحْيِ", "How the revelation began"),
    ("bukhari", 2, 3, "", "الصَّلَاةُ نُورٌ وَالصَّدَقَةُ بُرْهَانٌ", "Prayer is light and charity is proof"),
]
_BOOKS = [("bukhari", 1, "Revelation"), ("bukhari", 2, "Faith")]
_COLLECTIONS = [("bukhari", "Sahih al-Bukhari", "https://sunnah.com/bukhari:{number}")]


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """A tiny two-book database, put where loader and search look for the real one."""
    path = tmp_path / "hadith.db"
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    conn.executemany("INSERT INTO collection (id, name, cite) VALUES (?, ?, ?)", _COLLECTIONS)
    conn.executemany("INSERT INTO book (collection_id, number, name) VALUES (?, ?, ?)", _BOOKS)
    conn.executemany(
        "INSERT INTO hadith (collection_id, book_number, number, part, arabic, english) VALUES (?, ?, ?, ?, ?, ?)",
        _ROWS,
    )
    conn.executemany(
        "INSERT INTO hadith_fts (rowid, arabic, english) VALUES (?, ?, ?)",
        [(r, bare_letters(a), e) for r, a, e in conn.execute("SELECT rowid, arabic, english FROM hadith").fetchall()],
    )
    conn.execute("""UPDATE hadith SET grades = '[{"by": "Al-Albani", "grade": "Sahih"}]' WHERE number = 3""")
    conn.commit()
    conn.close()

    monkeypatch.setattr(loader, "data_path", lambda _key: path)
    monkeypatch.setattr(search, "data_path", lambda _key: path)
    # lru_cache is module-level and would otherwise carry a previous test's
    # (or a previous run's real) database into this one.
    loader.collections.cache_clear()
    loader.collection_name.cache_clear()
    loader.cite_of.cache_clear()
    loader.books.cache_clear()
    return path


def test_no_database_means_not_built(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "data_path", lambda _key: tmp_path / "nothing.db")
    loader.collections.cache_clear()
    assert loader.is_built() is False
    assert loader.collections() == []
    assert search.search("النور") == []


def test_collections_and_books_are_listed(db):
    assert loader.collections() == [("bukhari", "Sahih al-Bukhari", "", False)]
    assert loader.books("bukhari") == [
        {"number": 1, "name": "Revelation", "count": 2},
        {"number": 2, "name": "Faith", "count": 1},
    ]


def test_hadiths_of_a_book_carry_their_cite_link(db):
    found = loader.hadiths("bukhari", 1)
    assert [h["number"] for h in found] == [1, 2]
    assert found[0]["cite"] == "https://sunnah.com/bukhari:1"
    assert found[0]["arabic"].startswith("إِنَّمَا")


def test_an_unknown_book_is_empty_not_an_error(db):
    assert loader.hadiths("bukhari", 99) == []


def test_search_finds_every_word_typed(db):
    # The exact word as the fixture spells it, diacritics and all: FTS5's
    # tokenizer is not asked here to normalise Arabic, only to find it.
    hits = search.search("نُورٌ", 10)
    assert [h.number for h in hits] == [3]

    hits = search.search("light proof", 10)
    assert [h.number for h in hits] == [3]


def test_search_takes_plain_arabic_and_loose_words(db):
    """Unpointed Arabic finds pointed text; a word-order-free sentence with
    words the hadith never uses still lands on it via the any-word fallback."""
    assert [h.number for h in search.search("نور", 10)] == [3]
    assert search.search("intention", 10)
    assert [h.number for h in search.search("light nonexistentword", 10)] == [3]
    assert search.search("qqqq zzzz", 10) == []


def test_search_narrows_to_named_collections(db):
    assert search.search("intentions", 10, ("bukhari",))
    assert search.search("intentions", 10, ("muslim",)) == []


def test_a_query_fts5_cannot_parse_finds_nothing_rather_than_500(db):
    assert search.search('"', 10) == []


@pytest.fixture()
def client():
    return TestClient(app)


def test_router_lists_collections(db, client):
    resp = client.get("/api/hadith/collections")
    assert resp.status_code == 200
    assert resp.json() == [{"id": "bukhari", "name": "Sahih al-Bukhari", "short": "", "sahih": False}]


def test_router_lists_books_of_a_collection(db, client):
    resp = client.get("/api/hadith/bukhari/books")
    assert resp.status_code == 200
    assert [b["number"] for b in resp.json()] == [1, 2]


def test_router_404s_an_unknown_collection(db, client):
    assert client.get("/api/hadith/muslim/books").status_code == 404
    assert client.get("/api/hadith/muslim/books/1").status_code == 404


def test_router_404s_a_book_a_collection_does_not_have(db, client):
    assert client.get("/api/hadith/bukhari/books/99").status_code == 404


def test_router_returns_a_books_hadiths(db, client):
    resp = client.get("/api/hadith/bukhari/books/2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["book"] == {"number": 2, "name": "Faith", "count": 1}
    assert body["hadiths"][0]["arabic"].startswith("الصَّلَاةُ")


def test_router_search(db, client):
    resp = client.get("/api/hadith/search", params={"q": "light"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True
    assert [h["number"] for h in body["hits"]] == [3]


def test_router_search_with_no_query_says_ready_without_searching(db, client):
    resp = client.get("/api/hadith/search")
    assert resp.json() == {"query": "", "collections": [], "hits": [], "ready": True,
                            "source": resp.json()["source"]}


def test_router_search_before_the_database_is_built(tmp_path, monkeypatch, client):
    monkeypatch.setattr(loader, "data_path", lambda _key: tmp_path / "nothing.db")
    monkeypatch.setattr(search, "data_path", lambda _key: tmp_path / "nothing.db")
    loader.collections.cache_clear()
    resp = client.get("/api/hadith/search", params={"q": "light"})
    assert resp.json()["ready"] is False


def test_grades_and_lettered_cite_reach_the_reader(db):
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO hadith (collection_id, book_number, number, part, arabic) VALUES ('bukhari', 2, 3, 'c', 'نص')")
    conn.commit()
    conn.close()
    found = {(h["number"], h["part"]): h for h in loader.hadiths("bukhari", 2)}
    assert found[(3, "")]["grades"] == [{"by": "Al-Albani", "grade": "Sahih"}]
    assert found[(3, "c")]["grades"] == []
    assert found[(3, "c")]["cite"] == "https://sunnah.com/bukhari:3c"
    assert search.search("Prayer light")[0].grades == [{"by": "Al-Albani", "grade": "Sahih"}]
