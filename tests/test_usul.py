"""Weak points on the chains: a narrator's level from his grade, and the notes built from it.

Run on a tiny rijal.db made here: four narrators, two hadith, one mention
written twice at the same place (the case that must not double a note).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.main import app  # noqa: E402
from backend.scripts import build_rijal, build_usul  # noqa: E402
from backend.services.rijal import store as rijal_store  # noqa: E402
from backend.services.usul import store as usul_store  # noqa: E402
from backend.services.usul.level import level_of  # noqa: E402
from backend.services.usul.rule import rule  # noqa: E402

LEVELS = rule()["levels"]


@pytest.mark.parametrize("grade, level", [
    ("مجهول الحال", 7),  # the longer term first: not 9
    ("صدوق سيئ الحفظ", 5),  # سيئ and سيء are one word
    ("ضعيف سيء الحفظ", 8),
    ("ثقة ثقة", 2),
    ("متروك متهم بالكذب", 11),
    ("صدوق حسن الحديث", 4),
    ("صدوق رمي بالقدر", 5),
    ("ثقة رمي بالتشيع", 3),  # level 5 falls short of صدوق; a ثقة stays a ثقة
    ("ثقة ثبت قد يخطئ في حديث الثوري", 3),
    ("انفرد بتوثيقه ابن حبان", None),
])
def test_a_grade_reads_to_the_highest_level_its_words_name(grade, level):
    assert level_of(grade, LEVELS)[0] == level


def test_the_words_no_term_took_come_back_as_they_are():
    assert level_of("صدوق حسن الحديث", LEVELS) == (4, ["صدوق"], "حسن الحديث")
    assert level_of("انفرد بتوثيقه ابن حبان", LEVELS) == (None, [], "انفرد بتوثيقه ابن حبان")


# id -> grade; ids 1..4 are ثقة, ضعيف, صدوق سيئ الحفظ, and a grade no term reads.
GRADES = {1: "ثقة", 2: "ضعيف", 3: "صدوق سيئ الحفظ", 4: "انفرد بتوثيقه ابن حبان"}
# (number, part, start, narrator, ord) in muslim book 24; the second row for narrator 2 is a repeat.
MENTIONS = [(1, "", 0, 1, 0), (1, "", 10, 2, 1), (1, "", 10, 2, 2), (1, "", 20, 3, 3), (2, "a", 0, 4, 0), (2, "a", 8, 2, 1)]


@pytest.fixture()
def paths(tmp_path, monkeypatch):
    """A tiny rijal.db, and every module that opens a database pointed at temporary files."""
    where = {"rijal_index_path": tmp_path / "rijal.db", "usul_index_path": tmp_path / "usul.db",
             "usul_dir": build_usul.data_path("usul_dir"), "rijal_dir": build_usul.data_path("rijal_dir")}
    for module in (rijal_store, usul_store, build_usul):
        monkeypatch.setattr(module, "data_path", where.__getitem__)
    conn = sqlite3.connect(where["rijal_index_path"])
    conn.executescript(build_rijal._SCHEMA)
    conn.executemany("INSERT INTO narrator (id, name_ar, grade_ar) VALUES (?, ?, ?)",
                     [(who, f"راو {who}", grade) for who, grade in GRADES.items()])
    conn.executemany("INSERT INTO mention VALUES ('muslim', 24, ?, ?, ?, ?, ?, ?)",
                     [(number, part, start, start + 5, who, i) for number, part, start, who, i in MENTIONS])
    conn.commit()
    conn.close()
    return where


# The chains rijal.db would send for muslim book 24, built from the same mentions.
CHAINS = {f"{n}{p}": [[start, start + 5, who] for n2, p2, start, who, _ in MENTIONS if (n2, p2) == (n, p)]
          for n, p, *_ in MENTIONS}


def test_notes_are_keyed_by_hadith_and_placed_by_where_the_name_starts(paths):
    build_usul.build()
    found = usul_store.notes("muslim", 24, CHAINS)
    assert found == {
        "1": [{"at": 10, "id": 2, "level": 8, "kind": "weak", "grade": "ضعيف"},
              {"at": 20, "id": 3, "level": 5, "kind": "memory", "grade": "صدوق سيئ الحفظ"}],
        "2a": [{"at": 8, "id": 2, "level": 8, "kind": "weak", "grade": "ضعيف"}],
    }
    assert usul_store.notes("muslim", 25, {}) == {}


def test_a_note_rijal_no_longer_places_there_is_dropped(paths):
    build_usul.build()
    moved = {**CHAINS, "1": [[11, 16, 2], [20, 25, 3]]}  # rijal.db rebuilt: narrator 2 now starts at 11
    assert [n["id"] for n in usul_store.notes("muslim", 24, moved)["1"]] == [3]


def test_a_grade_no_term_reads_is_listed_never_marked(paths):
    build_usul.build()
    db = sqlite3.connect(paths["usul_index_path"])
    assert db.execute("SELECT what, text, count FROM gap").fetchall() == [("none", GRADES[4], 1)]
    assert db.execute("SELECT COUNT(*) FROM narrator_level WHERE narrator_id = 4").fetchone()[0] == 0


def test_a_rebuild_that_swings_the_notes_keeps_the_old_file(paths):
    build_usul.build()
    before = paths["usul_index_path"].read_bytes()
    conn = sqlite3.connect(paths["rijal_index_path"])
    conn.execute("UPDATE narrator SET grade_ar = 'ثقة' WHERE id IN (2, 3)")
    conn.commit()
    conn.close()
    with pytest.raises(SystemExit):
        build_usul.build()
    assert paths["usul_index_path"].read_bytes() == before


def test_the_chains_endpoint_carries_notes_and_the_scale(paths):
    build_usul.build()
    reply = TestClient(app).get("/api/rijal/chains/muslim/24").json()
    assert [n["id"] for n in reply["notes"]["1"]] == [2, 3]
    scale = reply["scale"]
    assert [row["level"] for row in scale] == list(range(1, 13))
    assert [row["weak"] for row in scale] == [False] * 4 + [True] * 8
    assert scale[10]["lift"]["lying"]["lifts"] is False and scale[4]["lift"].keys() == {"memory"}
    assert scale[7]["lift"] == {} and scale[0]["source"] == rule()["sources"]["taqrib"]["label"]


def test_the_chains_endpoint_is_as_before_where_usul_db_is_missing(paths):
    reply = TestClient(app).get("/api/rijal/chains/muslim/24").json()
    assert reply["notes"] == {} and reply["scale"] == [] and reply["ready"] is True
    assert reply["chains"]["1"][1] == [10, 15, 2]
