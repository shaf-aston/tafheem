"""Lane's Lexicon as a second, citable bab source, alongside Wiktionary.

Both are fake adapters registered in verb_sources.SOURCES, the seam babs_of()
reads at call time; neither lane.py nor dictionary_service is touched here,
so these tests check only the merge/citation rules, not either real source.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import conjugation, verb_sources

client = TestClient(app)


def _sources(monkeypatch, **by_source: dict[str, list[dict]]) -> None:
    monkeypatch.setattr(verb_sources, "SOURCES", {
        key: (lambda word, table=table: table.get(conjugation.bare(word), []))
        for key, table in by_source.items()
    })


def test_lane_only_word_is_cited_as_lane(monkeypatch):
    _sources(monkeypatch, lane={"زقم": [{"form": "I", "past": "زَقَمَ", "babs": ["a~u"]}]})
    verb = client.post("/api/morphology", json={"word": "زَقَمَ"}).json()["verb"]
    assert len(verb["readings"]) == 1
    assert [s["key"] for s in verb["readings"][0]["sources"]] == ["lane"]


def test_both_sources_agree_merge_into_one_reading_lane_then_wiktionary(monkeypatch):
    _sources(
        monkeypatch,
        lane={"كتب": [{"form": "I", "past": "كَتَبَ", "babs": ["a~u"]}]},
        wiktionary={"كتب": [{"form": "I", "past": "كَتَبَ", "babs": ["a~u"]}]},
    )
    verb = client.post("/api/morphology", json={"word": "كَتَبَ"}).json()["verb"]
    assert len(verb["readings"]) == 1
    assert [s["key"] for s in verb["readings"][0]["sources"]] == ["lane", "wiktionary"]


def test_sources_disagree_keep_both_readings(monkeypatch):
    _sources(
        monkeypatch,
        lane={"زقم": [{"form": "I", "past": "زَقَمَ", "babs": ["a~u"]}]},
        wiktionary={"زقم": [{"form": "I", "past": "زَقَمَ", "babs": ["a~i"]}]},
    )
    verb = client.post("/api/morphology", json={"word": "زَقَمَ"}).json()["verb"]
    assert len(verb["readings"]) == 2
    assert [s["key"] for s in verb["readings"][0]["sources"]] == ["lane"]
    assert [s["key"] for s in verb["readings"][1]["sources"]] == ["wiktionary"]


def test_two_lane_pasts_typed_bare_gives_both_readings_vowelled_gives_one(monkeypatch):
    _sources(monkeypatch, lane={"حبل": [
        {"form": "I", "past": "حَبَلَ", "babs": ["a~u"]},
        {"form": "I", "past": "حَبِلَ", "babs": ["i~a"]},
    ]})
    bare = client.post("/api/morphology", json={"word": "حبل"}).json()["verb"]
    assert len(bare["readings"]) == 2

    vowelled = client.post("/api/morphology", json={"word": "حَبِلَ"}).json()["verb"]
    assert len(vowelled["readings"]) == 1
    assert vowelled["readings"][0]["label"] == "حَبِلَ · باب سَمِعَ يَسْمَعُ"
