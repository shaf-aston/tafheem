"""The Tamreen library must be whole before the app serves it.

A question with no tag is unfindable, a picture question with no sentence is
unreadable, a part with no answer teaches nothing: each is caught at load.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import tamreen

TAGS = {"haal"}
PICTURES = {"haal-00.png"}


def test_every_shipped_exercise_loads_and_checks_out():
    exercises = tamreen.exercises()
    assert exercises, "no exercises found"
    # A form may be all pictures (munsarif has no statement questions), never empty.
    assert all(ex["rules"] or ex["examples"] for ex in exercises)


def test_ids_are_unique_across_every_exercise():
    ids = [q["id"] for ex in tamreen.exercises() for q in ex["rules"] + ex["examples"]]
    assert len(ids) == len(set(ids))


def test_every_used_tag_is_declared_and_every_declared_tag_is_used():
    counts = tamreen.coverage()
    unused = [tag for tag, n in counts.items() if n == 0]
    assert not unused, f"declared but unused: {unused}"


def test_filtering_by_tag_keeps_only_that_tag():
    tag = next(t for t, n in tamreen.coverage().items() if n)
    for ex in tamreen.exercises(tag):
        assert all(tag in q["tags"] for q in ex["rules"] + ex["examples"])


def test_a_question_with_no_tags_is_rejected():
    rule = {"id": "x", "question": "q", "options": ["a"], "answer": ["a"], "tags": []}
    assert tamreen._faults(rule, TAGS, PICTURES) == ["has no tags, so no search would find it"]


def test_an_undeclared_tag_is_rejected():
    rule = {"id": "x", "question": "q", "options": ["a"], "answer": ["a"], "tags": ["haal", "nope"]}
    assert "is tagged ['nope'], which tags.json does not declare" in tamreen._faults(rule, TAGS, PICTURES)


def test_an_example_missing_its_sentence_or_an_answer_is_rejected():
    example = {
        "id": "x", "picture": "haal-00.png", "tags": ["haal"],
        "parts": [{"letter": "a", "question": "q", "answer": None}],
    }
    said = tamreen._faults(example, TAGS, PICTURES)
    assert "has no sentence read off its picture" in said
    assert "part a has no answer" in said


def test_a_picture_that_is_not_on_disk_is_rejected():
    example = {"id": "x", "picture": "gone.png", "sentence": "س", "tags": ["haal"], "parts": []}
    assert tamreen._faults(example, TAGS, PICTURES) == [
        "names picture gone.png, which is not in images/"
    ]


def test_a_sound_example_has_no_faults():
    example = {
        "id": "x", "picture": "haal-00.png", "sentence": "س", "tags": ["haal"],
        "parts": [{"letter": "a", "question": "q", "answer": ["yes"]}],
    }
    assert tamreen._faults(example, TAGS, PICTURES) == []


def test_the_endpoint_serves_the_library_and_refuses_an_unknown_tag():
    client = TestClient(app)
    whole = client.get("/api/tamreen").json()
    assert whole["tags"] and whole["exercises"] and whole["coverage"]
    tag = next(t for t, n in whole["coverage"].items() if n)
    assert client.get("/api/tamreen", params={"tag": tag}).json()["exercises"]
    assert client.get("/api/tamreen", params={"tag": "not-a-tag"}).status_code == 404
