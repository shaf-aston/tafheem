"""Lane's Lexicon as a second, citable bab source, alongside Wiktionary.

Both are fake adapters registered in verb_sources.SOURCES, the seam babs_of()
reads at call time; neither lane.py nor dictionary_service is touched here,
so these tests check only the merge/citation rules, not either real source.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.scripts import build_lane_verbs
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


def _lane(*runs: str) -> str:
    """A Lane body: each Arabic run wrapped in the dump's bidi isolates."""
    fsi, pdi = build_lane_verbs.FSI, build_lane_verbs.PDI
    return " ".join(r if r.startswith(("aor.", ",", "first", "originally")) else f"{fsi}{r}{pdi}"
                    for r in runs)


def test_build_reads_hollow_samia_past_over_first_pers_and_originally():
    # Lane's own خوف entry: the aor. follows "originally" and "first pers.", not the past.
    body = _lane("خَافَ", ",", "originally", "خَوِفَ", ",", "first pers.", "خِفْتُ", ",", "aor.", "يَخَافُ")
    assert build_lane_verbs.verbs_of("خوف", body) == [{"form": "I", "past": "خَافَ", "babs": ["i~a"]}]
    # Alif in the past but a damma present stays نَصَرَ, not the سَمِعَ rule.
    assert build_lane_verbs.verbs_of("قول", _lane("قَالَ", ",", "aor.", "يَقُولُ"))[0]["babs"] == ["a~u"]
    # Only hollow roots step back: a doubled مَسَّ read past its "first pers." would be a~a.
    doubled = _lane("مَسَّهُ", ",", "first pers.", "مَسِسْتُهُ", ",", "aor.", "يَمَسُّهُ")
    assert build_lane_verbs.verbs_of("مسس", doubled) == []
