"""A further book's hadith (Mishkat) borrows the grades of its twin in the books its closing line names."""
from __future__ import annotations

import itertools
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.scripts.hadith import build_hadith_index as build  # noqa: E402
from backend.services.hadith import twin  # noqa: E402
from backend.services.hadith.usul import match  # noqa: E402

LINE = {"words": 40, "cue": ["رواه", "متفق"], "agreed_upon": ["bukhari", "muslim"]}
FORMS = {"bukhari": ["بخاري"], "muslim": ["مسلم"], "abudawud": ["داود"], "tirmidhi": ["ترمذي"]}
KNOBS = {"gram": 3, "df_max": 20, "floor": 3.0, "whole_floor": 2.0, "whole": 0.9, "tie_ratio": 0.9}
_LETTERS = "بتثجحخدذرزسشصضطظعغفقكلمن"
_WORDS = ["".join(w) for w in itertools.product(_LETTERS, repeat=3)]


def matn(seed: int) -> str:
    """Twelve words no other seed shares."""
    return " ".join(_WORDS[seed * 12:seed * 12 + 12])


def test_the_closing_line_names_who_recorded_it():
    assert set(twin.recorders(matn(1) + " رواه الترمذي وأبو داود", FORMS, LINE)) == {"tirmidhi", "abudawud"}
    assert twin.recorders(matn(1) + " رواه أحمد", FORMS, LINE) == []
    assert twin.recorders(matn(1), FORMS, LINE) == []


def test_agreed_upon_names_both_sahih_books():
    assert set(twin.recorders(matn(1) + " متفق عليه", FORMS, LINE)) == {"bukhari", "muslim"}


def test_a_name_inside_the_matn_is_no_recorder():
    assert twin.recorders("حق المسلم على المسلم " + matn(1), FORMS, LINE) == []


def test_the_twin_is_looked_for_only_in_the_books_named():
    docs = {c: match.Index({(c, 1, ""): match.tokens(matn(1)), (c, 2, ""): match.tokens(matn(2)),
                           (c, 3, ""): match.tokens(matn(3))}, KNOBS["gram"]) for c in FORMS}
    assert twin.twins(matn(2), ["tirmidhi"], docs, KNOBS) == [("tirmidhi", 2, "")]
    assert twin.twins(matn(2), ["tirmidhi", "muslim"], docs, KNOBS) == [("tirmidhi", 2, ""), ("muslim", 2, "")]
    assert twin.twins(matn(9), ["tirmidhi", "muslim"], docs, KNOBS) == []


def test_a_book_holding_the_matn_twice_gives_one_twin():
    words = {("tirmidhi", n, ""): match.tokens(matn(k)) for n, k in ((1, 1), (2, 2), (3, 3), (4, 3))}
    index = {"tirmidhi": match.Index(words, KNOBS["gram"])}
    assert len(twin.twins(matn(3), ["tirmidhi"], index, KNOBS)) == 1


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(build._SCHEMA)
    rows = [
        ("tirmidhi", 10, matn(1), [{"by": "Al-Albani", "grade": "Hasan"}]),
        ("tirmidhi", 11, matn(4), []),    # other hadith, so a phrase only one holds counts as rare
        ("tirmidhi", 12, matn(5), []),
        ("muslim", 20, matn(2), []),
        ("muslim", 21, matn(4), []),
        ("muslim", 22, matn(5), []),
        ("mishkat", 1, matn(1) + " رواه الترمذي", []),
        ("mishkat", 2, matn(2) + " رواه مسلم", []),
        ("mishkat", 3, matn(3) + " رواه الترمذي", []),   # named, but the book does not hold it
        ("mishkat", 4, matn(1), []),                       # no closing line
    ]
    conn.executemany("INSERT INTO hadith (collection_id, book_number, number, arabic, grades) VALUES (?, 1, ?, ?, ?)",
                     [(c, n, a, json.dumps(g)) for c, n, a, g in rows])
    return conn


def test_the_build_gives_a_hadith_its_twins_grades_and_says_whose(monkeypatch):
    monkeypatch.setattr(build, "rule", lambda: {"rulings": {"match": KNOBS}})
    collections = {
        "tirmidhi": {"name": "Jami at-Tirmidhi", "short": "Tirmidhi", "recorded_as": ["ترمذي"]},
        "muslim": {"name": "Sahih Muslim", "short": "Muslim", "recorded_as": ["مسلم"], "sahih": True},
        "mishkat": {"name": "Mishkat", "short": "Mishkat", "borrows_grades": LINE},
    }
    conn = _db()
    assert build.borrow_grades(conn, collections) == {"mishkat": 2}
    grades = {n: json.loads(g) for n, g in conn.execute("SELECT number, grades FROM hadith WHERE collection_id = 'mishkat'")}
    assert grades[1] == [{"by": "Al-Albani", "grade": "Hasan", "of": "Tirmidhi 10"}]
    assert grades[2] == [{"by": "Sahih Muslim", "grade": "Sahih", "of": "Muslim 20"}]
    assert grades[3] == grades[4] == []
