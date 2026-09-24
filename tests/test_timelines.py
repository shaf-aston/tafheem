"""The timelines must be whole and in order before the app serves them.

Each rule in services/timelines._faults gets one broken section beside a sound
control, so a rule that stops catching its fault fails here by name.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import copy

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import timelines

LIBRARY = {
    "sciences": [{"key": "seerah", "name": "Seerah", "arabic": "السيرة"}],
    "paths": {"believer": "The believer", "disbeliever": "The disbeliever"},
    "flags": {"disputed": "Scholars differ on order"},
    "collections": {"bukhari": {"kind": "hadith", "name": "Bukhari", "cite": "https://sunnah.com/bukhari:{number}"},
                    "ahmad": {"kind": "hadith", "name": "Ahmad"},
                    "raheeq": {"kind": "book", "name": "Raheeq"}},
    "places": {"makkah": {"name": "Makkah", "lon": 39.8, "lat": 21.4}},
    "map": {"land": [], "views": {"hijaz": {"west": 32, "north": 31, "east": 47, "south": 13}}},
}
AYAHS = {n: 7 for n in range(1, 115)} | {2: 286, 9: 129}


def event(id, at, **more):
    return {"id": id, "title": id, "arabic": "ع", "when": "then", "at": at, "summary": "s",
            "flags": [], "refs": [{"quran": "2:30-37"}], **more}


SOUND = {
    "id": "seerah", "order": 1, "name": "Seerah", "arabic": "السيرة", "science": "seerah",
    "kind": "dated", "sub": "", "map": "hijaz",
    "events": [
        event("birth", 570, place="makkah", refs=[{"book": "raheeq"}]),
        event("hira", 610, until="death", refs=[{"hadith": "bukhari", "number": 3}]),
        event("hijrah", 622, flags=["disputed"], refs=[{"quran": "9:40"}]),
        event("badr", 622, refs=[{"quran": "3"}]),
        event("death", 632),
    ],
}


def broken(change):
    section = copy.deepcopy(SOUND)
    change(section)
    return timelines._faults(section, LIBRARY, AYAHS)


def test_the_control_section_is_sound():
    assert timelines._faults(SOUND, LIBRARY, AYAHS) == []


@pytest.mark.parametrize("name, change, said", [
    ("duplicate id", lambda s: s["events"].append(copy.deepcopy(s["events"][-1])), "used more than once"),
    ("unknown place", lambda s: s["events"][0].update(place="rome"), "place 'rome'"),
    ("unknown science", lambda s: s.update(science="fiqh"), "science 'fiqh'"),
    ("unknown flag", lambda s: s["events"][0].update(flags=["maybe"]), "flag 'maybe'"),
    ("unknown map view", lambda s: s.update(map="moon"), "map view 'moon'"),
    ("ayah past the surah", lambda s: s["events"][0].update(refs=[{"quran": "2:280-290"}]), "passes the end"),
    ("surah that does not exist", lambda s: s["events"][0].update(refs=[{"quran": "115"}]), "does not exist"),
    ("range backwards", lambda s: s["events"][0].update(refs=[{"quran": "2:9-3"}]), "backwards"),
    ("malformed reference", lambda s: s["events"][0].update(refs=[{"quran": "2.30"}]), "is not S"),
    ("two kinds in one reference", lambda s: s["events"][0].update(refs=[{"quran": "2:1", "book": "raheeq"}]), "exactly one"),
    ("hadith without a number", lambda s: s["events"][0].update(refs=[{"hadith": "bukhari"}]), "no number"),
    ("book named as a hadith", lambda s: s["events"][0].update(refs=[{"hadith": "raheeq", "number": 1}]), "does not declare"),
    ("a part that is not one letter", lambda s: s["events"][0].update(refs=[{"hadith": "bukhari", "number": 3, "part": "c1"}]), "single letter"),
    ("the same reference twice", lambda s: s["events"][0].update(refs=[{"quran": "2:30"}, {"quran": "2:30"}]), "given twice"),
    ("no references", lambda s: s["events"][0].update(refs=[]), "no references"),
    ("checked against a collection with no link",
     lambda s: s["events"][0].update(refs=[{"hadith": "ahmad", "number": 1, "checked": "sunnah.com"}]),
     "no cite link"),
    ("event out of order", lambda s: s["events"][2].update(at=500), "comes before"),
    ("until pointing nowhere", lambda s: s["events"][1].update(until="tabuk"), "not an event"),
    ("until pointing backwards", lambda s: s["events"][1].update(until="birth"), "does not come after"),
    ("until pointing at itself", lambda s: s["events"][1].update(until="hira"), "does not come after"),
    ("until ending where it starts", lambda s: s["events"][2].update(until="badr"), "does not come after"),
    ("until pointing at an event with no at", lambda s: (s["events"][4].pop("at"), s["events"][1].update(until="death")), "not an event in this section"),
    ("two events claiming one stretch", lambda s: [e.update(period="makkan") for e in s["events"][:2]], "would be shown twice"),
    ("a period nobody declared", lambda s: s["events"][0].update(period="meccan"), "not one of"),
    ("an empty word in names", lambda s: s["events"][0].update(names=["بدر", " "]), "empty word"),
    ("hijri year in the wrong shape", lambda s: s["events"][0].update(hijri="AH 5"), "not like '5 AH'"),
    ("hijri year zero", lambda s: s["events"][0].update(hijri="0 AH"), "not like '5 AH'"),
    ("missing summary", lambda s: s["events"][0].update(summary=" "), "no summary"),
    ("no events", lambda s: s.update(events=[]), "no events"),
])
def test_each_fault_is_caught_by_name(name, change, said):
    faults = broken(change)
    assert any(said in f for f in faults), f"{name}: {faults}"


def step(id, **more):
    return {"id": id, "title": id, "summary": "s", **more}


WITH_STEPS = [
    step("plot", refs=[{"quran": "9:40"}]),
    step("cave", when="three nights", steps=[step("grieve"), step("food", flags=["disputed"])]),
]


def test_steps_are_optional_and_a_sound_run_passes():
    section = copy.deepcopy(SOUND)
    section["events"][2]["steps"] = copy.deepcopy(WITH_STEPS)
    section["events"][2]["steps"][0]["aside"] = True
    section["events"][2]["steps"][0]["path"] = "believer"
    section["events"][2]["steps"][1]["path"] = "disbeliever"
    assert timelines._faults(section, LIBRARY, AYAHS) == []


def with_steps(change):
    """The control section with a run of steps on one event, then broken."""
    steps = copy.deepcopy(WITH_STEPS)
    change(steps)
    section = copy.deepcopy(SOUND)
    section["events"][2]["steps"] = steps
    return timelines._faults(section, LIBRARY, AYAHS)


@pytest.mark.parametrize("name, change, said", [
    ("step with no title", lambda s: s[0].update(title=" "), "has no title"),
    ("step with no summary", lambda s: s[0].update(summary=""), "has no summary"),
    ("two steps sharing an id", lambda s: s[1]["steps"][0].update(id="plot"), "already used in this event"),
    ("moment with an unknown place", lambda s: s[1]["steps"][0].update(place="rome"), "place 'rome'"),
    ("moment with an unknown flag", lambda s: s[1]["steps"][1].update(flags=["maybe"]), "flag 'maybe'"),
    ("step citing an ayah past the surah", lambda s: s[0].update(refs=[{"quran": "2:280-290"}]), "passes the end"),
    ("hadith in a step with no number", lambda s: s[0].update(refs=[{"hadith": "bukhari"}]), "no number"),
    ("a step citing one hadith twice", lambda s: s[0].update(refs=[{"hadith": "bukhari", "number": 3}] * 2), "given twice"),
    ("step on an undeclared path", lambda s: s[0].update(path="hypocrite"), "path 'hypocrite'"),
    ("a side-by-side run on one path", lambda s: s[0].update(path="believer"), "only the 'believer' path"),
    ("aside written as a word", lambda s: s[0].update(aside="yes"), "aside must be true or false"),
    ("nested one level too deep", lambda s: s[1]["steps"][0].update(steps=[step("deeper")]), "past the 2 levels"),
])
def test_each_step_fault_is_caught_by_name(name, change, said):
    faults = with_steps(change)
    assert any(said in f for f in faults), f"{name}: {faults}"


def test_the_shipped_hijrah_is_broken_into_steps_that_reach_the_tab():
    """The one event written out in full, end to end, ids unique inside it."""
    seerah = next(s for s in timelines.library()["sections"] if s["id"] == "seerah")
    hijrah = next(e for e in seerah["events"] if e["id"] == "hijrah")
    assert len(hijrah["steps"]) >= 5
    ids = []

    def walk(steps):
        for one in steps:
            ids.append(one["id"])
            walk(one.get("steps") or [])

    walk(hijrah["steps"])
    assert len(ids) == len(set(ids))
    assert any(one.get("steps") for one in hijrah["steps"]), "no step holds moments, so nothing can be folded"
    body = TestClient(app).get("/api/timelines").json()
    served = next(e for s in body["sections"] if s["id"] == "seerah"
                  for e in s["events"] if e["id"] == "hijrah")
    assert [one["id"] for one in served["steps"]] == [one["id"] for one in hijrah["steps"]]
    assert served["steps"][1]["steps"], "the moments inside a step were dropped on the way out"


def test_side_by_side_paths_reach_the_tab_with_their_names():
    """A step's path and the path names both survive the response shape."""
    body = TestClient(app).get("/api/timelines").json()
    assert body["paths"]["believer"]
    served = {one.get("path") for s in body["sections"] for e in s["events"] for one in e["steps"]}
    assert {"believer", "disbeliever"} <= served


def test_every_shipped_hadith_number_says_where_it_was_checked():
    """The amber "number not checked" is gone, so nothing may still need it."""
    library = timelines.library()
    unchecked = []

    def walk(events, where):
        for event in events:
            for ref in event.get("refs") or []:
                if ref.get("hadith") and not ref.get("checked"):
                    unchecked.append(f"{where}/{event['id']}: {ref['hadith']} {ref['number']}")
            walk(event.get("steps") or [], f"{where}/{event['id']}")

    for section in library["sections"]:
        walk(section["events"], section["id"])
    assert unchecked == []
    for key, collection in library["collections"].items():
        if collection["kind"] == "hadith":
            assert "{number}" in collection.get("cite", ""), key


def test_ranges_are_left_unchecked_when_ayah_counts_are_unknown():
    section = copy.deepcopy(SOUND)
    section["events"][0]["refs"] = [{"quran": "2:280-290"}]
    assert timelines._faults(section, LIBRARY, {}) == []


def test_the_shipped_library_loads_in_order_with_unique_ids():
    library = timelines.library()
    orders = [s["order"] for s in library["sections"]]
    assert orders == sorted(orders) and len(orders) >= 5
    for section in library["sections"]:
        ids = [e["id"] for e in section["events"]]
        assert len(ids) == len(set(ids)), section["id"]


def test_asbab_reports_are_named_on_their_event_or_left_to_the_stretch():
    """The two ways a report reaches an event, on the shipped data.

    Skipped rather than failed where the books are not imported: a checkout with
    no library.db is a valid state, and the tab shows no reports in it.
    """
    if not timelines._asbab():
        pytest.skip("the asbab books are not imported here")
    badr = timelines.asbab("seerah", "badr")
    assert badr["reports"] and all(row["how"] == "named" for row in badr["reports"])
    assert badr["source"]["key"] == "lubab"
    refs = [row["ref"] for row in badr["reports"]]
    assert refs == sorted(refs, key=lambda ref: [int(n) for n in ref.split(":")])

    madinan = timelines.asbab("seerah", "madinan-revelation")
    assert all(row["how"] == "period" for row in madinan["reports"])
    # A report shown on Badr must not be buried in the stretch as well.
    assert not {row["ref"] for row in madinan["reports"]} & set(refs)


def test_an_event_that_does_not_exist_is_a_404_not_an_empty_list():
    assert TestClient(app).get("/api/timelines/seerah/nowhere/asbab").status_code == 404
    with pytest.raises(KeyError):
        timelines.asbab("nosuch", "badr")


def test_the_endpoint_serves_every_section_with_its_source():
    response = TestClient(app).get("/api/timelines")
    assert response.status_code == 200
    body = response.json()
    assert [s["id"] for s in body["sections"]] == ["prophets", "seerah", "signs", "grave", "judgement"]
    assert body["source"]["key"] == "timelines"


def test_every_hadith_the_sections_cite_has_its_words_to_print():
    """The reader prints the hadith under the event, so a cited number with no
    words is a silent gap: the number would sit there alone with nothing under
    it and nobody would know a fetch had been missed."""
    library = timelines.library()
    words = library["hadith"]
    assert len(words) >= 70
    wanted = set()

    def walk(events):
        for event in events:
            for ref in event.get("refs") or []:
                if ref.get("hadith"):
                    wanted.add(f"{ref['hadith']}:{ref['number']}{ref.get('part') or ''}")
            walk(event.get("steps") or [])

    for section in library["sections"]:
        walk(section["events"])
    assert wanted - set(words) == set()
    for key, one in words.items():
        assert one["arabic"].strip(), key


def test_the_endpoint_sends_the_words_beside_the_numbers():
    body = TestClient(app).get("/api/timelines").json()
    fire = body["hadith"]["muslim:2902"]
    assert "الْحِجَازِ" in fire["arabic"] and "Hijaz" in fire["english"]
