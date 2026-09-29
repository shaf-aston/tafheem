"""The dawah file must be whole before the app serves it.

Each rule in services/dawah.faults gets one broken copy beside a sound control.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import copy

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import dawah

COLLECTIONS = {"bukhari": {"kind": "hadith", "name": "Bukhari", "cite": "https://sunnah.com/bukhari:{number}"}}
AYAHS = {n: 7 for n in range(1, 115)} | {2: 286}


def question(id, **more):
    return {"id": id, "q": "q?", "short": "s", "points": [point()], "islamqa": None, **more}


def point(**more):
    return {"title": "t", "text": "x", "refs": [{"quran": "2:255"}], **more}


SOUND = {"islamqa": {"name": "IslamQA", "cite": "https://islamqa.info/en/answers/{number}"}, "topics": [
    {"id": "god", "title": "God", "arabic": "الله", "blurb": "b", "questions": [question("one"), question("two")]},
    {"id": "quran", "title": "Qur'an", "arabic": "القرآن", "blurb": "b", "questions": [question("three")]},
]}


def broken(change):
    data = copy.deepcopy(SOUND)
    change(data)
    return dawah.faults(data, COLLECTIONS, AYAHS)


def test_sound_file_has_no_faults():
    assert dawah.faults(SOUND, COLLECTIONS, AYAHS) == []


def test_a_note_alone_is_evidence():
    assert broken(lambda d: d["topics"][0]["questions"][0].update(points=[point(refs=[], note="Ibn Kathir on 2:255")])) == []


@pytest.mark.parametrize("change, said", [
    (lambda d: d["topics"][0]["questions"].append(question("one")), "already used"),        # exact duplicate
    (lambda d: d["topics"][1]["questions"].append(question("one")), "already used"),        # repeat across topics
    (lambda d: d["topics"].append(copy.deepcopy(d["topics"][1])), "given twice"),
    (lambda d: d["topics"][0]["questions"][0].update(short=" "), "has no short"),
    (lambda d: d["topics"][0]["questions"][0].update(points=[{"title": "t", "text": ""}]), "no reasoning"),
    (lambda d: d["topics"][0]["questions"][0].update(points=[]), "no reasoning"),
    (lambda d: d["topics"][0]["questions"][0].update(islamqa={"number": "12", "title": "t"}), "whole number"),
    (lambda d: d.update(islamqa={"name": "IslamQA", "cite": "https://islamqa.info/"}), "no {number}"),
    (lambda d: d["topics"][0]["questions"][0].update(points=[point(refs=[])]), "no evidence"),
    (lambda d: d["topics"][0]["questions"][0].update(points=[point(refs=[{"quran": "1:8"}])]), "passes the end"),
    (lambda d: d["topics"][0]["questions"][0].update(points=[point(refs=[{"hadith": "muslim", "number": 1}])]), "does not declare"),
    (lambda d: d["topics"][0]["questions"][0].update(points=[point(), point(title="u", refs=[], note=" ")]), "no evidence"),
    (lambda d: d["topics"][0].update(questions=[]), "no questions"),
])
def test_each_fault_is_named(change, said):
    assert any(said in why for why in broken(change))


def test_real_file_is_served():
    body = TestClient(app).get("/api/dawah").json()
    assert body["topics"] and body["collections"]["bukhari"] and body["source"]["key"] == "dawah"
