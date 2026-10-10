"""An ayah typed into the Nahw analyser is read from its recorded tarkeeb.

The treebank was checked by hand, word by word; the parser is a model reading
bare letters. So when the sentence is an ayah the treebank recorded, the cards
and the picture both come from that record, and the parser is not asked.

A one-ayah tarkeeb.db is built here with the real build functions from the
treebank's rows for 100:9, the ayah the parser misread as تمييز + مفعول به.
"""
from __future__ import annotations

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.scripts import build_tarkeeb
from backend.services import nahw_book, syntax, tarkeeb_store
from tests.test_tarkeeb_treebank import AL_ADIYAT_9, SETTINGS

client = TestClient(app)
TYPED = "أَفَلَا يَعْلَمُ إِذَا بُعْثِرَ مَا فِي الْقُبُورِ"


@pytest.fixture(autouse=True)
def recorded(tmp_path, monkeypatch):
    words, _ = build_tarkeeb._words_of(AL_ADIYAT_9, SETTINGS)
    tree = build_tarkeeb._tree_of(words, SETTINGS, nahw_book.relation_tone)
    written = [i for i, word in enumerate(words) if not word["elided"]]
    path = tmp_path / "tarkeeb.db"
    db = sqlite3.connect(path)
    db.executescript(build_tarkeeb.SCHEMA)
    db.execute("INSERT INTO tarkeeb VALUES (?, ?, ?, ?, ?, ?)", (
        100, 9, json.dumps([w["text"] for w in words], ensure_ascii=False),
        json.dumps(tree, ensure_ascii=False),
        tarkeeb_store.letters([words[i]["text"] for i in written]), json.dumps(written)))
    db.commit()
    db.close()
    monkeypatch.setattr(tarkeeb_store, "DATABASE", path)


def test_a_typed_ayah_is_read_from_its_record_not_the_parser(monkeypatch):
    def parser(*_):
        raise AssertionError("the parser was asked about a recorded ayah")
    monkeypatch.setattr(syntax, "read", parser)

    answer = client.post("/api/analyze", json={"sentence": TYPED}).json()
    assert answer["source"]["key"] == "treebank"
    assert answer["tree"]["source"]["key"] == "treebank"
    assert (answer["tree"]["surah"], answer["tree"]["ayah"]) == (100, 9)
    roles = [word["role"] for word in answer["words"]]
    assert roles == [SETTINGS["particle_kinds"]["حرف استفهام"], nahw_book.term_ar("fil"),
                     nahw_book.term_ar("zarf_zaman"), nahw_book.term_ar("fil"),
                     SETTINGS["relation_terms"]["نائب فاعل"], nahw_book.term_ar("jarr"),
                     SETTINGS["relation_terms"]["مجرور"]]
    assert "تمييز" not in json.dumps(answer, ensure_ascii=False)
    assert answer["summary"] == nahw_book.term_ar("jumlah_filiyyah")


def test_a_card_is_coloured_the_same_whoever_named_it():
    words = client.post("/api/analyze", json={"sentence": TYPED}).json()["words"]
    by_word = {word["word"]: word["role_key"] for word in words}
    assert by_word["يَعْلَمُ"] == "fil"
    assert by_word["مَا"] == "fail"


def test_the_same_ayah_typed_without_vowels_finds_the_same_record():
    assert tarkeeb_store.find("افلا يعلم اذا بعثر ما في القبور")[:2] == (100, 9)


def test_a_sentence_that_is_no_ayah_goes_to_the_parser(monkeypatch):
    asked = []
    monkeypatch.setattr(syntax, "read", lambda sentence, picks: asked.append(sentence) or
                        {"roles": [{"role": None, "case": None}] * 3, "tree": None})
    client.post("/api/analyze", json={"sentence": "ذَهَبَ الطَّالِبُ مُسْرِعًا"})
    assert asked


def test_a_database_built_before_the_lookup_existed_is_not_an_error(tmp_path, monkeypatch):
    old = tmp_path / "old.db"
    db = sqlite3.connect(old)
    db.execute("CREATE TABLE tarkeeb (surah INTEGER, ayah INTEGER, words TEXT, tree TEXT)")
    db.commit()
    db.close()
    monkeypatch.setattr(tarkeeb_store, "DATABASE", old)
    assert tarkeeb_store.find(TYPED) is None
