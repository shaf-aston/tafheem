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
from backend.scripts.build_hadith_index import _SCHEMA, index_text  # noqa: E402
from backend.scripts import build_hadith_meaning  # noqa: E402
from backend.services.hadith import loader, meaning, repair, search, words  # noqa: E402

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
    index_text(conn)
    conn.execute("""UPDATE hadith SET grades = '[{"by": "Al-Albani", "grade": "Sahih"}]' WHERE number = 3""")
    conn.commit()
    conn.close()

    monkeypatch.setattr(loader, "data_path", lambda _key: path)
    monkeypatch.setattr(search, "data_path", lambda _key: path)
    # No meaning index unless a test builds one, so a real one on disk never leaks in.
    monkeypatch.setattr(meaning, "data_path", lambda _key: tmp_path / "hadith_meaning.db")
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
    assert search.search("النور").hits == []


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
    hits = search.search("نُورٌ", 10).hits
    assert [h.number for h in hits] == [3]

    hits = search.search("light proof", 10).hits
    assert [h.number for h in hits] == [3]


def test_search_takes_plain_arabic_and_loose_words(db):
    """Unpointed Arabic finds pointed text; a word-order-free sentence with
    words the hadith never uses still lands on it via the any-word fallback."""
    assert [h.number for h in search.search("نور", 10).hits] == [3]
    assert search.search("intention", 10).hits
    found = search.search("light nonexistentword", 10)
    assert [h.number for h in found.hits] == [3]
    assert found.unmatched == ["nonexistentword"]
    assert found.partial is False
    # Two real words no single hadith holds: the fallback says so.
    found = search.search("light revelation", 10)
    assert len(found.hits) == 2 and found.partial is True
    assert search.search("qqqq zzzz", 10).hits == []


def test_search_narrows_to_named_collections(db):
    assert search.search("intentions", 10, ("bukhari",)).hits
    assert search.search("intentions", 10, ("muslim",)).hits == []


def test_a_query_fts5_cannot_parse_finds_nothing_rather_than_500(db):
    assert search.search('"', 10).hits == []


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
    assert resp.json() == {"query": "", "collections": [], "hits": [], "corrected": [], "unmatched": [],
                            "partial": False, "chapters": [], "ready": True, "source": resp.json()["source"]}


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
    assert search.search("Prayer light").hits[0].grades == [{"by": "Al-Albani", "grade": "Sahih"}]


def test_a_misspelt_word_is_swapped_for_the_word_meant_and_said_so(db):
    """chairty is a slip no hadith holds; it still finds charity, and says so."""
    found = search.search("chairty", 10)
    assert [h.number for h in found.hits] == [3]
    assert found.corrected == [("chairty", "charity")]


def test_a_word_nothing_is_near_is_reported_not_guessed(db):
    found = search.search("xqzvw", 10)
    assert found.hits == [] and found.corrected == [] and found.unmatched == ["xqzvw"]


def test_front_particles_do_not_hide_a_word(db):
    """The fixture spells it بِالنِّيَّاتِ; typing النيات or نيات must reach it."""
    assert [h.number for h in search.search("النيات", 10).hits] == [1]
    assert [h.number for h in search.search("نيات", 10).hits] == [1]


def test_noise_words_are_not_required(db):
    """'hadith about prayer' asks about prayer; the other two words are in no fixture row and must not block it."""
    found = search.search("hadith about prayer", 10)
    assert [h.number for h in found.hits] == [3]
    assert found.unmatched == []


def test_hits_come_with_the_chapters_they_fall_in(db):
    found = search.search("light revelation", 10)
    assert sorted((c.number, c.name, c.count) for c in found.chapters) == [(1, "Revelation", 1), (2, "Faith", 1)]
    assert found.chapters[0].collection == "bukhari"


def test_words_read_numbers_as_written_out():
    assert words.tokens("Prophet said: 99 patience!") == [("Prophet", "prophet"), ("said:", "said"), ("99", "99"), ("patience!", "patience")]
    assert words.number_phrases("99")[:2] == [["99"], ["ninety", "nine"]]


def test_one_edit_covers_every_kind_of_slip():
    """Missing, added, replaced and swapped letters each count as one."""
    assert repair.edits("chairty", "charity") == 1
    assert repair.edits("رمظان", "رمضان") == 1
    assert repair.edits("siwaak", "siwak") == 1
    assert repair.edits("ستكجاري", "تجاري") == 2


def test_a_name_is_not_the_word_it_spells(db):
    """صَبْرَة the narrator's name is not الصبر patience; the dictionary form keeps them apart."""
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO hadith (collection_id, book_number, number, part, arabic, english) "
                 "VALUES ('bukhari', 2, 4, '', 'حَدَّثَنَا لَقِيطُ بْنُ صَبْرَةَ', 'Laqit bin Sabira narrated')")
    conn.execute("INSERT INTO hadith (collection_id, book_number, number, part, arabic, english) "
                 "VALUES ('bukhari', 2, 5, '', 'وَمَا أُعْطِيَ أَحَدٌ عَطَاءً خَيْرًا مِنَ الصَّبْرِ', 'No gift is better than patience')")
    conn.execute("DELETE FROM hadith_fts"); conn.execute("DELETE FROM word"); conn.execute("DELETE FROM deletion")
    index_text(conn)
    conn.commit()
    conn.close()
    assert [h.number for h in search.search("الصبر", 10).hits] == [5]
    assert [h.number for h in search.search("بالصبر", 10).hits] == [5]


def test_router_search_reports_corrections_and_chapters(db, client):
    body = client.get("/api/hadith/search", params={"q": "chairty"}).json()
    assert body["corrected"] == [{"typed": "chairty", "used": "charity"}]
    assert body["chapters"] == [{"collection": "bukhari", "number": 2, "name": "Faith", "count": 1}]


def test_ta_marbuta_typed_as_ha_is_the_same_word(db):
    """الصلاه and الصلاة find the same hadith, with nothing called a correction."""
    for typed in ("الصلاه", "الصلاة"):
        found = search.search(typed, 10)
        assert [h.number for h in found.hits] == [3] and found.corrected == []


def test_a_distant_word_is_not_passed_off_as_a_repair(db):
    """Sharing a few letters is not enough: ستكجاري is near nothing in the fixture."""
    found = search.search("ستكجاري", 10)
    assert found.corrected == [] and found.unmatched == ["ستكجاري"]


class _Meanings:
    """Stands in for the sentence model: "light" and the intentions hadith mean the same; all else differs."""

    def encode(self, texts):
        import numpy as np
        return np.array([[1.0, 0.0] if ("light" == t or "intentions" in t) else [0.0, 1.0] for t in texts])


@pytest.fixture()
def meanings(db, tmp_path, monkeypatch):
    paths = {"hadith_index_path": db, "hadith_meaning_path": tmp_path / "hadith_meaning.db"}
    monkeypatch.setattr(meaning, "encoder", _Meanings)
    monkeypatch.setattr(build_hadith_meaning, "data_path", paths.__getitem__)
    build_hadith_meaning.main()


def test_a_hadith_close_in_meaning_is_found_without_its_words(meanings):
    """Only hadith 3 says "light"; hadith 1 shares no word but means the same, so it ranks next, above unrelated 2."""
    assert [h.number for h in search.search("light", 10).hits] == [3, 1, 2]


def test_meaning_never_answers_a_question_whose_words_are_all_unknown(meanings):
    found = search.search("ستكجاري", 10)
    assert found.hits == [] and found.unmatched == ["ستكجاري"]


def test_a_rebuild_encodes_only_changed_hadith(meanings, db, monkeypatch):
    calls = []
    monkeypatch.setattr(meaning, "encoder", lambda: type("Spy", (), {"encode": lambda _s, t: calls.append(t) or _Meanings().encode(t)})())
    build_hadith_meaning.main()
    assert calls == []
