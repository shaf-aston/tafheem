"""The Qur'an reader's page view: a printed mushaf, line for line.

Run: python -m pytest tests/test_mushaf.py
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.services.quran import mushaf
from backend.services.quran.mushaf import DATA_DIR

PRINTING = "madani-1421"


@pytest.fixture(scope="module")
def pages() -> list:
    return json.loads((DATA_DIR / f"{PRINTING}.json").read_text(encoding="utf-8"))["pages"]


def test_the_madani_printing_is_offered():
    assert [one["id"] for one in mushaf.printings()] == [PRINTING]


def test_every_page_has_the_print_s_lines(pages):
    assert len(pages) == 604
    for number, lines in enumerate(pages, start=1):
        assert len(lines) == (8 if number <= 2 else 15), f"page {number}"


def test_every_surah_is_named_once_in_order_and_basmalas_where_printed(pages):
    names = [line[1] for page in pages for line in page if line[0] == "surah"]
    assert names == list(range(1, 115))
    assert sum(line[0] == "basmala" for page in pages for line in page) == 112


def test_every_ayah_is_on_the_pages_once_ended_by_its_number(pages):
    ends = []
    for page in pages:
        for line in page:
            if line[0] == "ayah":
                ends += [(s, a) for s, a, text in line[1] if text.split(" ")[-1].isdigit()]
    assert len(ends) == 6236 and len(set(ends)) == 6236


def test_a_surah_named_at_the_foot_of_a_page_reads_on_overleaf(pages):
    # An-Nisa's name closes page 76; its basmala opens 77.
    assert pages[75][-1] == ["surah", 4]
    assert pages[76][0] == ["basmala"]


def test_a_surah_gets_every_whole_page_it_is_on():
    got = mushaf.for_surah(PRINTING, 1)
    assert [one["page"] for one in got] == [1]
    baqarah = [one["page"] for one in mushaf.for_surah(PRINTING, 2)]
    assert baqarah == list(range(2, 50))
    assert mushaf.for_surah(PRINTING, 4)[0]["page"] == 76


def test_an_unknown_printing_is_none():
    assert mushaf.for_surah("no-such", 1) is None


def test_the_routes():
    client = TestClient(create_app())
    listed = client.get("/api/quran/mushaf").json()
    assert listed[0]["id"] == PRINTING and listed[0]["source"]["key"] == "mushaf"
    pages = client.get(f"/api/quran/mushaf/{PRINTING}/surah/112").json()
    assert [one["page"] for one in pages["pages"]] == [604]
    assert client.get("/api/quran/mushaf/no-such/surah/1").status_code == 404
