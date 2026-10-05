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
    dialect = next(d for d in catalogue["dialects"] if d["key"] == "damascene")
    assert dialect["units"]

    got = client.get(f"/api/colloquial/damascene/{dialect['units'][0]['unit']}")
    assert got.status_code == 200
    # Topics the spine adds before this dialect writes them come back as "written": false.
    written = [lesson for lesson in got.json()["lessons"] if lesson.get("written", True)]
    unit = got.json()
    assert written and all(lesson["exercises"] for lesson in written)
    # Every exercise kept its own type's shape through the union, not a bare dict.
    assert {e["type"] for lesson in written for e in lesson["exercises"]} <= registry.TYPES
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
    unit["lessons"][0]["phrases"][0]["image"] = "unit-01/nothing.jpg"
    assert any("not on disk" in line for line in loader._unit_faults(unit))


def test_pictures_are_proposed_then_approved_by_a_person(tmp_path, monkeypatch):
    import json

    import httpx

    from backend.scripts import fetch_colloquial_images as fetch

    spine = {"units": [{"unit": "unit-01", "title": "t", "lessons": [{"lesson": "lesson-01", "title": "t", "phrases": [
        {"slot": "hello", "english": "Hello.", "search_term": "waving hand"},
        {"slot": "thanks", "english": "Thanks."},
    ]}]}]}
    (tmp_path / "spine.json").write_text(json.dumps(spine, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(fetch, "paths", lambda u: (tmp_path / "spine.json", tmp_path / "review.json", tmp_path / "pics"))
    first = lambda: json.loads((tmp_path / "spine.json").read_text(encoding="utf-8"))["units"][0]["lessons"][0]["phrases"][0]

    def serve(request):
        if request.url.path.endswith("/thumb/"):
            return httpx.Response(200, content=b"jpgbytes")
        return httpx.Response(200, json={"results": [{
            "id": "abc", "title": "Hand", "creator": "Sam", "license": "by", "license_version": "4.0",
            "license_url": "https://cc", "foreign_landing_url": "https://src",
            "thumbnail": "https://api.openverse.org/v1/images/abc/thumb/"}]})

    client = httpx.Client(transport=httpx.MockTransport(serve))
    review = fetch.propose("unit-01", None, client)
    assert [e["search_term"] for e in review["found"]] == ["waving hand"]
    assert [m["phrase"] for m in review["needs_search_term"]] == [2]
    assert "image" not in first()

    saved = fetch.approve("unit-01", 1, 1, 1, client)
    assert (tmp_path / "pics" / saved.split("/")[-1]).read_bytes() == b"jpgbytes"
    credits = json.loads((tmp_path / "pics" / "attribution.json").read_text(encoding="utf-8"))
    assert credits[saved.split("/")[-1]]["creator"] == "Sam"
    assert first()["image"] == saved


OUTLINE = {"unit": "unit-01", "title": "First Conversations", "lessons": [
    {"lesson": "lesson-01", "title": "Greetings", "phrases": [
        {"slot": "hello", "english": "Hello.", "search_term": "waving hand"},
        {"slot": "thanks", "english": "Thanks."}]}]}
WRITTEN = {"unit": "unit-01", "dialect": "Egyptian Arabic", "lessons": [
    {"lesson": "lesson-01", "phrases": [
        {"slot": "thanks", "arabic": "شكرا", "transliteration": "shukran"},
        {"slot": "hello", "arabic": "أهلا", "transliteration": "ahlan"}]}]}


def test_a_dialect_is_laid_onto_the_spine_in_its_order_with_its_english():
    unit, said = loader._fill(OUTLINE, copy.deepcopy(WRITTEN))
    assert said == []
    assert unit["title"] == "First Conversations" and unit["lessons"][0]["title"] == "Greetings"
    hello, thanks = unit["lessons"][0]["phrases"]
    assert (hello["arabic"], hello["english"], hello["search_term"]) == ("أهلا", "Hello.", "waving hand")
    assert thanks["english"] == "Thanks."


def test_a_slot_the_dialect_skipped_is_caught():
    written = copy.deepcopy(WRITTEN)
    written["lessons"][0]["phrases"].pop()
    assert any("no words for 'hello'" in why for why in loader._fill(OUTLINE, written)[1])


def test_a_slot_or_lesson_the_spine_lacks_is_caught():
    written = copy.deepcopy(WRITTEN)
    written["lessons"][0]["phrases"].append({"slot": "bye", "arabic": "باي", "transliteration": "bye"})
    written["lessons"].append({"lesson": "lesson-09", "phrases": []})
    said = loader._fill(OUTLINE, written)[1]
    assert any("'bye', which spine.json does not have" in why for why in said)
    assert any("'lesson-09' is not in spine.json" in why for why in said)


def test_a_spine_lesson_the_dialect_never_wrote_is_coming_not_a_fault():
    outline = copy.deepcopy(OUTLINE)
    outline["lessons"].append({"lesson": "lesson-02", "title": "More", "phrases": []})
    unit, said = loader._fill(outline, copy.deepcopy(WRITTEN))
    alone, _ = loader._fill(OUTLINE, copy.deepcopy(WRITTEN))
    assert said == [] and loader._unit_faults(unit) == loader._unit_faults(alone)
    assert unit["lessons"][1] == {"lesson": "lesson-02", "title": "More", "section": None, "written": False}
    assert unit["lessons"][0]["written"] is True


def test_a_spine_section_reaches_written_and_coming_lessons_alike():
    outline = copy.deepcopy(OUTLINE)
    outline["lessons"][0]["section"] = "Happy occasions"
    outline["lessons"].append({"lesson": "lesson-02", "title": "More", "section": "Hard times", "phrases": []})
    unit, _ = loader._fill(outline, copy.deepcopy(WRITTEN))
    assert [lesson["section"] for lesson in unit["lessons"]] == ["Happy occasions", "Hard times"]
    plain, _ = loader._fill(OUTLINE, copy.deepcopy(WRITTEN))
    assert plain["lessons"][0]["section"] is None


def test_the_catalogue_carries_each_topic_section_so_the_unit_page_can_head_it():
    cards = [lesson for dialect in loader.catalogue()["dialects"] for unit in dialect["units"]
             for lesson in unit["lessons"]]
    assert cards and all("section" in lesson for lesson in cards)


def test_a_repeated_slot_in_one_lesson_is_caught():
    written = copy.deepcopy(WRITTEN)
    written["lessons"][0]["phrases"].append({"slot": "hello", "arabic": "هاي", "transliteration": "hi"})
    assert any("'hello' twice" in why for why in loader._fill(OUTLINE, written)[1])


def test_an_unwritten_unit_is_listed_as_coming_and_cannot_be_opened(tmp_path, monkeypatch):
    import json
    import shutil

    from backend.config import data_path
    real = data_path("colloquial_dir")
    shutil.copy(real / "spine.json", tmp_path / "spine.json")
    (tmp_path / "dialects.json").write_text(json.dumps({"dialects": [
        {"key": "damascene", "folder": "damascene", "label": "D", "arabic": "د", "where": "w", "order": 1}]}), encoding="utf-8")
    (tmp_path / "damascene").mkdir()
    shutil.copy(real / "damascene" / "unit-01.json", tmp_path / "damascene" / "unit-01.json")
    shutil.copytree(real / "images" / "unit-01", tmp_path / "images" / "unit-01")
    monkeypatch.setattr(loader, "data_path", lambda key: tmp_path if key == "colloquial_dir" else data_path(key))
    loader._content.cache_clear()
    try:
        units = loader.catalogue()["dialects"][0]["units"]
        assert [u["written"] for u in units[:2]] == [True, False]
        assert len(units) == len(json.loads((real / "spine.json").read_text(encoding="utf-8"))["units"])
        with pytest.raises(KeyError):
            loader.unit("damascene", "unit-02")
    finally:
        loader._content.cache_clear()


def test_a_lesson_is_compared_across_every_dialect_slot_by_slot():
    client = TestClient(app)
    got = client.get("/api/colloquial/compare/unit-03/lesson-01").json()
    keys = [d["key"] for d in client.get("/api/colloquial").json()["dialects"]]
    assert [d["key"] for d in got["dialects"]] == keys
    slots = [[p["slot"] for p in d["phrases"]] for d in got["dialects"] if d["phrases"] is not None]
    assert slots and all(s == slots[0] for s in slots)
    unit = client.get("/api/colloquial/damascene/unit-03").json()
    assert [p["slot"] for p in unit["lessons"][0]["phrases"]] == slots[0]


def test_an_unwritten_unit_compares_as_none_and_an_unknown_lesson_404s(monkeypatch):
    content = copy.deepcopy(loader._content())
    content["dialects"][1]["units"][2]["written"] = False
    monkeypatch.setattr(loader, "_content", lambda: content)
    got = loader.compare("unit-03", "lesson-01")
    assert got["dialects"][1]["phrases"] is None and got["dialects"][0]["phrases"]
    assert TestClient(app).get("/api/colloquial/compare/unit-03/lesson-99").status_code == 404
    assert TestClient(app).get("/api/colloquial/compare/unit-99/lesson-01").status_code == 404
