"""The dictionary's web layer: what reaches a service, and what a failure says.

The services have their own tests. These pin what only the router decides: which
input is refused before anything is searched, and that a database failing
mid-read is reported as broken, never as a root no book holds.

Run: python -m pytest tests/test_dictionary_routes.py
"""
from __future__ import annotations

import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers import dictionary as router_module
from backend.services import lexicons
from tests.test_dictionary_hamza_search import took  # noqa: F401, the fixture
from tests.test_lexicons import shelf  # noqa: F401, the fixture


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router_module.router)
    return TestClient(app)


def _search(client, q, lang="ar"):
    return client.get("/api/dictionary/search", params={"q": q, "lang": lang})


@pytest.mark.usefixtures("took")
def test_a_root_typed_letter_by_letter_is_searched_joined(client):
    body = _search(client, "ا خ ذ").json()
    assert body["query"] == "اخذ"
    assert "أخذ" in [entry["arabic"] for entry in body["results"]]


@pytest.mark.usefixtures("took")
def test_a_slip_that_finds_nothing_is_looked_up_as_the_word_meant(client):
    """اخض is one letter off اخذ and inside no word: اخذ is looked up, and the answer says so."""
    body = _search(client, "اخض").json()
    assert body["query"] == "اخذ" and body["corrected"] == [{"typed": "اخض", "used": "اخذ"}]
    assert "أخذ" in [entry["arabic"] for entry in body["results"]]
    assert _search(client, "اخذ").json()["corrected"] == []


@pytest.mark.parametrize(("q", "lang", "status"), [
    ("كتب", "fr", 400),      # a language there is no index for
    ("   ", "ar", 400),      # nothing but spaces
    ("ك" * 201, "ar", 422),  # past the length limit
])
def test_a_question_that_cannot_be_asked_is_refused(client, q, lang, status):
    assert _search(client, q, lang).status_code == status


@pytest.mark.usefixtures("shelf")
def test_the_shelf_answers_a_root_with_each_books_credit(client):
    body = client.get("/api/dictionary/lexicons", params={"root": "امر"}).json()
    assert body["status"] == "ready"
    assert [entry["book"] for entry in body["entries"]] == ["lisan", "lane"]
    assert all(entry["source"]["key"] for entry in body["entries"])


def test_letters_that_are_not_arabic_never_reach_the_books(client):
    assert client.get("/api/dictionary/lexicons", params={"root": "ktb"}).status_code == 422


@pytest.mark.usefixtures("shelf")
def test_a_database_failing_mid_read_is_broken_not_an_empty_shelf(client, monkeypatch):
    """"None of these books has an entry" would be a false claim about the books."""
    class Failing:
        def execute(self, *args):
            if "FROM entry e JOIN" in args[0]:
                raise sqlite3.OperationalError("disk I/O error")
            return sqlite3.connect(":memory:").execute("SELECT 1")

    monkeypatch.setattr(lexicons, "_db", Failing)
    body = client.get("/api/dictionary/lexicons", params={"root": "امر"}).json()
    assert body["status"] == "broken"
    assert body["entries"] == []
