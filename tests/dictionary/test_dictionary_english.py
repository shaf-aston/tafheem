"""English into Arabic: a typed form finds its headword, a sentence gets a row per word, and the model only renders the whole.

The dictionary is four small entries and the model is stood in for, so this runs anywhere.

Run: python -m pytest tests/dictionary/test_dictionary_english.py
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.config import get_settings
from backend.routers import dictionary as router_module
from backend.services import ai
from backend.services.dictionary import service
from backend.services.learner import progress_store

ENTRIES = [
    {"arabic": "جرى", "root": "جري", "definitions": ["to flow, to run a course, to happen"]},
    {"arabic": "ركض", "root": "ركض", "definitions": ["to run"]},
    {"arabic": "كتاب", "root": "كتب", "definitions": ["book"]},
    {"arabic": "مكتبة", "root": "كتب", "definitions": ["a place with a book collection"]},
]


@pytest.fixture
def small(monkeypatch):
    arabic, english = service._build_indices(ENTRIES)
    monkeypatch.setattr(service, "_dictionary", ENTRIES)
    monkeypatch.setattr(service, "_arabic_index", arabic)
    monkeypatch.setattr(service, "_english_index", english)
    monkeypatch.setattr(service, "_loaded", True)
    service._english_matches.cache_clear()
    yield
    service._english_matches.cache_clear()


@pytest.fixture
def client(monkeypatch, tmp_path):
    # Answers are filed in a store of this test's own, not the real one.
    monkeypatch.setattr(progress_store, "data_path", lambda _name: tmp_path / "progress.db")
    progress_store.reset_connection()
    app = FastAPI()
    app.include_router(router_module.router)
    yield TestClient(app)
    progress_store.reset_connection()


def test_a_past_form_finds_the_headword_whose_definition_is_the_verb(small) -> None:
    assert [e["arabic"] for e in service.search_english("ran")][:2] == ["ركض", "جرى"]


def test_a_definition_that_is_the_word_beats_a_passing_mention(small) -> None:
    assert service.search_english("book")[0]["arabic"] == "كتاب"


def test_a_sentence_has_a_row_per_word_and_the_model_renders_the_whole(small, client, monkeypatch) -> None:
    asked = []
    monkeypatch.setattr(ai, "render_in_arabic", lambda text: asked.append(text) or {"arabic": "أَنَا أَقْرَأُ كِتَابًا"})
    body = client.get("/api/dictionary/sentence", params={"q": "We ran. The book!"}).json()
    # Filed on the first ask, so the same text reads the same next time without asking again.
    again = client.get("/api/dictionary/sentence", params={"q": "We ran. The book!"}).json()
    assert again["meaning"] == body["meaning"] and len(asked) == 1
    assert body["direction"] == "en" and body["kind"] == "sentence"
    assert body["meaning"] == "أَنَا أَقْرَأُ كِتَابًا" and body["source"]["label"].startswith("AI")
    assert [(w["english"], w["base"], w["arabic"]) for w in body["words"]] == [
        ("we", "we", ""), ("ran", "run", "ركض"), ("the", "the", ""), ("book", "book", "كتاب")]


def test_a_dead_model_leaves_the_words_without_a_meaning(small, client, monkeypatch) -> None:
    def down(text):
        raise RuntimeError("No AI backend available")

    monkeypatch.setattr(ai, "render_in_arabic", down)
    body = client.get("/api/dictionary/sentence", params={"q": "the book"}).json()
    assert body["meaning"] is None and body["source"] is None and body["words"][1]["arabic"] == "كتاب"


def test_a_sentence_longer_than_a_search_is_still_read(small, client, monkeypatch) -> None:
    """An ayah the chart draws (4:113 is about 290 letters) gets its English too: the sentence
    cap is the one /analyze has, not a search box's."""
    monkeypatch.setattr(ai, "render_in_arabic", lambda text: {"arabic": "كِتَابٌ"})
    q = " ".join(["the book"] * 30)
    assert get_settings().search_max_query_chars < len(q) < get_settings().max_sentence_chars
    assert client.get("/api/dictionary/sentence", params={"q": q}).status_code == 200
    assert client.get("/api/dictionary/sentence", params={"q": "a" * (get_settings().max_sentence_chars + 1)}).status_code == 422


@pytest.mark.parametrize("q", ["book", "hello <b>there</b>"])
def test_one_word_or_odd_characters_are_refused(client, q) -> None:
    assert client.get("/api/dictionary/sentence", params={"q": q}).status_code == 422


def test_a_contraction_stays_one_word(small) -> None:
    assert [row["english"] for row in service.english_words("don't go, it's late")] == ["don't", "go", "it's", "late"]
