"""A word that is no headword is found as the word it is a form of, and by its root.

مُنْتَصِرًا is in no dictionary. The search used to answer "No entries. Try the
bare root", and the root cards asked Maqayees about منتصرا, letters no root
book files. The Nahw and Sarf tabs read the same word as مُنْتَصِر of نصر; the
dictionary now asks the same reader (services/morphology.py) before it gives up.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.services import dictionary_service as service
from backend.services import morphology


def entry(arabic: str, root: str, meaning: str) -> dict:
    return {"arabic": arabic, "root": root, "definitions": [meaning]}


@pytest.fixture
def dictionary(monkeypatch):
    """A few headwords, indexed exactly as load_dictionary() indexes them."""
    entries = [
        entry("نَصَرَ", "نصر", "to help"), entry("اِنْتَصَرَ", "نصر", "to be victorious"),
        entry("قَالَ", "قول", "to say"), entry("قَوْل", "قول", "saying"), entry("قَيْلُولَة", "قيل", "siesta"),
        entry("فَرَّ", "فرر", "to flee"), entry("فَرْو", "فرو", "fur"),
        entry("أَتَى", "ءتي", "to come"), entry("آتَى", "ءتي", "to give"),
        entry("مَدْرَسَة", "درس", "school"),
    ]
    arabic, english = service._build_indices(entries)
    monkeypatch.setattr(service, "_dictionary", entries)
    monkeypatch.setattr(service, "_arabic_index", arabic)
    monkeypatch.setattr(service, "_english_index", english)
    monkeypatch.setattr(service, "_loaded", True)
    service._arabic_matches.cache_clear()
    yield
    service._arabic_matches.cache_clear()


def read_as(monkeypatch, table: dict[str, list[tuple[str, str]]]) -> None:
    """CAMeL's readings, as CI has no CAMeL data: # for a weak radical it could not pin down."""
    monkeypatch.setattr(morphology, "readings", lambda word: table.get(word, []))


def found(query: str) -> list[str]:
    return [e["arabic"] for e in service.search_arabic(query)]


@pytest.mark.usefixtures("dictionary")
def test_a_form_is_found_by_its_root(monkeypatch):
    read_as(monkeypatch, {"مُنْتَصِرًا": [("منتصر", "نصر")]})
    entries, reading = service.search_arabic_read("مُنْتَصِرًا")
    assert [e["arabic"] for e in entries] == ["نَصَرَ", "اِنْتَصَرَ"]  # the root's own verb first
    assert reading == ("", "نصر")  # مُنْتَصِر itself is no headword here


@pytest.mark.usefixtures("dictionary")
def test_a_weak_radical_is_filled_only_with_a_root_the_dictionary_has(monkeypatch):
    read_as(monkeypatch, {"قالوا": [("قال", "ق#ل")], "يقولون": [("قول", "ق#ل")], "زالوا": [("زال", "ز#ل")]})
    assert found("قالوا") == ["قَالَ", "قَوْل"]  # found as قال, so its own root, not قيل (siesta) too
    assert found("زالوا") == []  # no زول or زيل here: nothing is guessed onto the page


@pytest.mark.usefixtures("dictionary")
def test_every_reading_is_offered_likeliest_first(monkeypatch):
    read_as(monkeypatch, {"فَفِرُّوا": [("فر", "فرر"), ("فرو", "فر#")]})
    assert found("فَفِرُّوا") == ["فَرَّ", "فَرْو"]


@pytest.mark.usefixtures("dictionary")
def test_the_lemma_as_spelt_beats_its_hamza_twin(monkeypatch):
    read_as(monkeypatch, {"يُؤْتُونَ": [("آتى", "#ت#")]})
    assert found("يُؤْتُونَ")[0] == "آتَى"  # give, not أَتَى come, though the two fold alike


@pytest.mark.usefixtures("dictionary")
def test_a_headword_is_not_read_again(monkeypatch):
    asked = []
    monkeypatch.setattr(morphology, "readings", lambda word: asked.append(word) or [])
    assert found("مدرسة") == ["مَدْرَسَة"]
    assert asked == []


@pytest.mark.usefixtures("dictionary")
def test_the_page_is_told_the_reading_and_the_root_to_ask_the_books(monkeypatch):
    read_as(monkeypatch, {"قالوا": [("قال", "ق#ل")]})
    app = TestClient(create_app())
    answer = app.get("/api/dictionary/search", params={"q": "قالوا"}).json()
    assert answer["read_as"] == {"typed": "قالوا", "lemma": "قال", "root": "قول"}
    assert answer["root"] == "قول"
    typed = app.get("/api/dictionary/search", params={"q": "مدرسة"}).json()
    assert typed["read_as"] is None and typed["root"] == "درس"  # a headword names its own root


@pytest.mark.skipif(morphology.get_engine_name() != "camel-tools", reason="CAMeL data not installed")
def test_camel_reads_the_words_from_the_report():
    assert ("منتصر", "نصر") in morphology.readings("مُنْتَصِرًا")
    assert morphology.readings("قالوا")[0] == ("قال", "ق#ل")
    assert morphology.readings("فَفِرُّوا")[0] == ("فر", "فرر")  # the typed shadda: flee, not fur
