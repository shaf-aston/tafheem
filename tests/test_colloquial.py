"""A colloquial unit must be whole before the app serves it.

Each rule in services/colloquial gets one broken unit beside a sound control, so
a rule that stops catching its fault fails here by name. The real units are then
loaded as they are, which is the only check that the content on disk is sound.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import copy

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.colloquial import loader
from backend.services.colloquial.exercises import registry


def phrase(word="مرحبا"):
    return {"arabic": word, "transliteration": "mar7aba", "english": "Hello."}


def exercise(id, type="reply", **more):
    one = {"id": id, "type": type, "prompt": "p", "answer": "شو اسمك", "accepted": ["شو اسمك"],
           "tip": "t", **more}
    if type == "choose":
        one.setdefault("options", ["شو اسمك", "وينك", "كيفك"])
    return one


SOUND = {
    "unit": "unit-01", "title": "First Conversations", "dialect": "Damascene Arabic",
    "transliteration_key": {"3": "ع"},
    "lessons": [{
        "lesson": "lesson-01", "title": "Greetings",
        "phrases": [{**phrase(), "reply": phrase("أهلا")}],
        "dialogue": [{"speaker": "Samer", **phrase()}],
        "de_book": [{"pair": phrase(), "response": phrase("أهلا")}],
        "culture": "Greetings are repeated warmly.",
        "exercises": [exercise("a.1"), exercise("a.2", "choose"), exercise("a.3", "reorder")],
    }],
    "challenge": {"title": "c", "instructions": "write it", "required_elements": ["a greeting"],
                  "model": {"dialogue": [{"speaker": "Samer", **phrase()}]}},
}


def faults(**changes):
    """The faults of the sound unit with one thing changed."""
    unit = copy.deepcopy(SOUND)
    for path, value in changes.items():
        unit["lessons"][0][path] = value
    return loader._unit_faults(unit)


def test_the_sound_unit_has_no_faults():
    assert loader._unit_faults(copy.deepcopy(SOUND)) == []


def test_a_repeated_exercise_id_is_caught():
    said = faults(exercises=[exercise("same"), exercise("same")])
    assert any("uses the id 'same' again" in why for why in said)


def test_an_unknown_exercise_type_is_caught():
    said = faults(exercises=[exercise("a.1", "speak_it")])
    assert any("'speak_it'" in why for why in said)


def test_a_missing_accepted_list_is_caught():
    one = exercise("a.1")
    del one["accepted"]
    assert any("no accepted answers" in why for why in faults(exercises=[one]))


def test_an_answer_outside_the_accepted_list_is_caught():
    said = faults(exercises=[exercise("a.1", accepted=["something else"])])
    assert any("does not list its own answer" in why for why in said)


def test_too_few_options_is_caught():
    said = faults(exercises=[exercise("a.1", "choose", options=["one", "two"])])
    assert any("fewer than" in why for why in said)


def test_an_answer_that_is_not_an_option_is_caught():
    said = faults(exercises=[exercise("a.1", "choose", options=["one", "two", "three"])])
    assert any("not one of its options" in why for why in said)


def test_a_repeated_option_is_caught():
    said = faults(exercises=[exercise("a.1", "choose", options=["شو اسمك", "وينك", "وينك"])])
    assert any("twice" in why for why in said)


def test_a_word_bank_tile_outside_the_answer_is_caught():
    said = faults(exercises=[exercise("a.1", "reorder", words=["شو", "كيفك"])])
    assert any("not in its answer" in why for why in said)


def test_a_one_word_reorder_with_no_bank_is_caught():
    said = faults(exercises=[exercise("a.1", "reorder", answer="كيفك", accepted=["كيفك"])])
    assert any("nothing to arrange" in why for why in said)


def test_an_empty_phrase_field_is_caught():
    said = faults(phrases=[{"arabic": "", "transliteration": "t", "english": "e"}])
    assert any("phrase 1 has no arabic" in why for why in said)


def test_a_reply_is_checked_like_a_phrase():
    said = faults(phrases=[{**phrase(), "reply": {"arabic": "أهلا", "transliteration": "", "english": "Hi"}}])
    assert any("reply has no transliteration" in why for why in said)


def test_a_missing_culture_note_is_caught():
    assert any("no culture note" in why for why in faults(culture=" "))


def test_every_fault_is_named_at_once_rather_than_the_first():
    said = faults(culture="", phrases=[], dialogue=[])
    assert len(said) >= 3


def test_two_lessons_with_one_number_are_caught():
    unit = copy.deepcopy(SOUND)
    unit["lessons"].append(copy.deepcopy(unit["lessons"][0]))
    assert any("two lessons numbered" in why for why in loader._unit_faults(unit))


def test_the_registry_owns_the_five_types_the_content_uses():
    assert registry.TYPES == {"reply", "fill_blank", "translate_to_arabic", "choose", "reorder"}


def test_the_real_units_on_disk_load_and_are_served():
    loader._content.cache_clear()
    client = TestClient(app)
    catalogue = client.get("/api/colloquial").json()
    dialect = catalogue["dialects"][0]
    assert dialect["key"] == "damascene" and dialect["units"]

    got = client.get(f"/api/colloquial/damascene/{dialect['units'][0]['unit']}")
    assert got.status_code == 200
    unit = got.json()
    assert unit["lessons"] and all(lesson["exercises"] for lesson in unit["lessons"])
    # Every exercise kept its own type's shape through the union, not a bare dict.
    assert {e["type"] for lesson in unit["lessons"] for e in lesson["exercises"]} <= registry.TYPES
    assert unit["source"]["confidence"] == "guessed"


@pytest.mark.parametrize("path", ["/api/colloquial/klingon/unit-01", "/api/colloquial/damascene/unit-99"])
def test_an_unknown_dialect_or_unit_is_a_404(path):
    assert TestClient(app).get(path).status_code == 404


def test_a_picture_is_served_and_cannot_be_climbed_out_to():
    from backend.config import data_path
    folder = data_path("colloquial_dir") / "images" / "_probe"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "x.jpg").write_bytes(b"jpg")
    try:
        client = TestClient(app)
        assert client.get("/api/colloquial/image/_probe/x.jpg").content == b"jpg"
        assert client.get("/api/colloquial/image/_probe/none.jpg").status_code == 404
        assert client.get("/api/colloquial/image/../dialects.json").status_code == 404
        assert client.get("/api/colloquial/image/%2e%2e/dialects.json").status_code == 404
    finally:
        (folder / "x.jpg").unlink()
        folder.rmdir()


def test_a_phrase_naming_a_missing_picture_is_caught():
    unit = copy.deepcopy(SOUND)
    unit["lessons"][0]["phrases"][0]["image"] = "damascene/unit-01/nothing.jpg"
    assert any("not on disk" in line for line in loader._unit_faults(unit))


def test_a_picture_with_no_credit_is_caught_and_a_real_one_carries_its_credit():
    unit = copy.deepcopy(SOUND)
    unit["lessons"][0]["phrases"][0]["image"] = "damascene/unit-01/l03-p01-number-one.jpg"
    assert any("attribution.json" in line for line in loader._unit_faults(unit))
    served = loader.unit("damascene", "unit-01")
    shown = [p for lesson in served["lessons"] for p in lesson["phrases"] if p.get("image")]
    assert shown and all(p["credit"] and p["credit_url"].startswith("https://") for p in shown)


def test_pictures_are_proposed_then_approved_by_a_person(tmp_path, monkeypatch):
    import json

    import httpx

    from backend.scripts import fetch_colloquial_images as fetch

    unit = copy.deepcopy(SOUND)
    unit["lessons"][0]["phrases"] = [
        {**phrase(), "search_term": "waving hand"},
        {**phrase("شكرا"), "search_term": ""},
    ]
    (tmp_path / "unit-01.json").write_text(json.dumps(unit, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(fetch, "paths", lambda d, u: (tmp_path / "unit-01.json", tmp_path / "review.json", tmp_path / "pics"))

    def serve(request):
        if request.url.path.endswith("/thumb/"):
            return httpx.Response(200, content=b"jpgbytes")
        return httpx.Response(200, json={"results": [{
            "id": "abc", "title": "Hand", "creator": "Sam", "license": "by", "license_version": "4.0",
            "license_url": "https://cc", "foreign_landing_url": "https://src",
            "thumbnail": "https://api.openverse.org/v1/images/abc/thumb/"}]})

    client = httpx.Client(transport=httpx.MockTransport(serve))
    review = fetch.propose("damascene", "unit-01", None, client)
    assert [e["search_term"] for e in review["found"]] == ["waving hand"]
    assert [m["phrase"] for m in review["needs_search_term"]] == [2]
    assert "image" not in json.loads((tmp_path / "unit-01.json").read_text(encoding="utf-8"))["lessons"][0]["phrases"][0]

    saved = fetch.approve("damascene", "unit-01", 1, 1, 1, client)
    assert (tmp_path / "pics" / saved.split("/")[-1]).read_bytes() == b"jpgbytes"
    credits = json.loads((tmp_path / "pics" / "attribution.json").read_text(encoding="utf-8"))
    assert credits[saved.split("/")[-1]]["creator"] == "Sam"
    assert json.loads((tmp_path / "unit-01.json").read_text(encoding="utf-8"))["lessons"][0]["phrases"][0]["image"] == saved
