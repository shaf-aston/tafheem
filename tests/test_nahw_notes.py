"""The Nahw notes load, and every way a note can be wrong is caught when it does."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import nahw_notes

ROLES = {"term", "ruling", "condition", "label", "example"}


def block(**over) -> dict:
    return {"id": "b1", "kind": "rule", "page": 0, "ar": "الحال منصوب", **over}


def faults(over: dict, pages: int = 1) -> list[str]:
    return nahw_notes._faults(block(**over), ROLES, pages)


def test_a_sound_block_has_no_faults():
    assert faults({"ar": "الحال {{term|منصوب}} أبدا"}) == []


def test_an_unknown_kind_is_caught():
    assert "not one of" in " ".join(faults({"kind": "diagram"}))


def test_a_page_the_topic_does_not_have_is_caught():
    assert "pictures" in " ".join(faults({"page": 3}, pages=2))
    assert faults({"page": 1}, pages=2) == []


def test_a_marker_naming_an_undeclared_role_is_caught():
    assert "roles.json does not declare" in " ".join(faults({"ar": "{{colour|أحمر}}"}))


def test_an_empty_marker_is_caught():
    assert "empty" in " ".join(faults({"ar": "{{term| }}"}))


def test_a_broken_marker_is_caught():
    assert "broken marker" in " ".join(faults({"ar": "الحال {{term|منصوب"}))


def test_a_table_row_that_does_not_fit_its_columns_is_caught():
    table = {"kind": "table", "columns": ["a", "b"], "rows": [["1", "2"], ["1"]], "ar": None}
    assert "do not fit" in " ".join(faults(table))


def test_a_table_answering_by_a_column_it_lacks_is_caught():
    table = {"kind": "table", "columns": ["a", "b"], "rows": [], "answer_col": 2, "ar": None}
    assert "which it does not have" in " ".join(faults(table))


def test_a_block_with_no_text_is_caught():
    assert "no text at all" in " ".join(faults({"ar": None}))


def test_a_marker_inside_a_word_label_is_caught():
    example = {"kind": "example", "labels": [{"word": "راكبا", "label": "{{label|حال}}"}]}
    assert "labels take no markers" in " ".join(faults(example))
    assert faults({"kind": "example", "labels": [{"word": "راكبا", "label": "حال"}]}) == []


def test_a_picture_with_no_caption_is_caught():
    assert "no caption" in " ".join(faults({"kind": "picture", "ar": None}))


def test_two_blocks_with_the_same_id_stop_the_load(tmp_path, monkeypatch):
    same = [block(), block()]
    topics = tmp_path / "topics"
    topics.mkdir()
    (topics / "x.json").write_text(json.dumps({"title": "X", "arabic": "س", "blocks": same}), encoding="utf-8")
    monkeypatch.setattr(nahw_notes, "TOPICS_DIR", topics)
    monkeypatch.setattr(nahw_notes, "IMAGES_DIR", tmp_path / "images")
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "x-00.png").write_bytes(b"")
    nahw_notes._topics.cache_clear()
    with pytest.raises(ValueError, match="shares its id"):
        nahw_notes._topics()
    nahw_notes._topics.cache_clear()


def test_a_topic_does_not_count_the_pages_of_a_topic_whose_id_starts_with_its_own(tmp_path, monkeypatch):
    for name in ("x-00.png", "x-01.png", "x-ws-00.png", "xy-00.png"):
        (tmp_path / name).write_bytes(b"")
    monkeypatch.setattr(nahw_notes, "IMAGES_DIR", tmp_path)
    assert nahw_notes._page_count("x") == 2


def test_the_real_notes_load_and_every_topic_has_pages():
    for topic in nahw_notes.topics():
        assert topic["blocks"], f"{topic['id']} has no blocks"
        assert topic["pages"] > 0, f"{topic['id']} has no page pictures"


def test_every_tamreen_link_names_a_real_exercise():
    keys = {p.stem for p in Path("backend/data/tamreen/exercises").glob("*.json")}
    for topic in nahw_notes.topics():
        unknown = [slug for slug in topic.get("tamreen", []) if slug not in keys]
        assert not unknown, f"{topic['id']} links to missing exercises {unknown}"


def test_the_library_endpoint_serves_the_topics_and_a_source():
    with TestClient(app) as client:
        body = client.get("/api/notes").json()
    assert body["source"]["confidence"] == "guessed"
    assert {role["key"] for role in body["roles"]} == ROLES
    assert any(t["id"] == "waw-haaliyah" for t in body["topics"])


def test_a_page_picture_is_served_and_a_missing_one_is_a_404():
    with TestClient(app) as client:
        assert client.get("/api/notes/waw-haaliyah/page/0.png").status_code == 200
        assert client.get("/api/notes/waw-haaliyah/page/99.png").status_code == 404
        assert client.get("/api/notes/no-such-topic/page/0.png").status_code == 404
