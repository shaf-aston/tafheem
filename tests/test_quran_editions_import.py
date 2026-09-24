"""Reading a foreign book's file, without needing that book to be here.

The importer's whole risk is in three small readers, one per foreign shape, and
QUL publishes no schema for theirs: the column names and the row shapes were
read out of their exporter's source. A test that can only run once somebody has
downloaded a 100MB tafsir would never run, so these build QUL's own shape by
hand, exactly as their exporter writes it, and read it back.

The tafsir shape is the one worth pinning. Their `tafsir` table holds three
different kinds of row at once:

  text     the passage, with `ayah_keys` naming every ayah it covers
  pointer  another ayah of that run: empty text, `group_ayah_key` pointing back
  empty    an ayah the book says nothing about, with no text at all

Reading the pointer rows as passages would store one passage many times over.
Reading the empty rows would fill the library with blank commentary. Both look
fine in a row count, which is why they are checked here rather than by eye.

Run: python -m pytest tests/test_quran_editions_import.py
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from backend.scripts.import_quran_editions import (
    check,
    read_app_tafsir_db,
    read_ayah_json,
    read_qul_tafsir,
    read_qul_translation,
)

# What QUL's exporter writes, column for column.
QUL_TAFSIR = """
CREATE TABLE tafsir (
    ayah_key TEXT, group_ayah_key TEXT, from_ayah TEXT,
    to_ayah TEXT, ayah_keys TEXT, text TEXT
);
"""

QUL_TRANSLATION = """
CREATE TABLE translations (
    sura INTEGER, ayah INTEGER, ayah_key TEXT, text TEXT, footnotes TEXT DEFAULT '{}'
);
"""

APP_TAFSIR = """
CREATE TABLE entry (id TEXT PRIMARY KEY, text TEXT NOT NULL);
CREATE TABLE covers (surah INTEGER, ayah INTEGER, entry TEXT, PRIMARY KEY (surah, ayah));
"""


@pytest.fixture
def qul_tafsir(tmp_path):
    """One passage over three ayahs, one over one, and one silent ayah."""
    path = tmp_path / "tafsir.db"
    db = sqlite3.connect(path)
    db.executescript(QUL_TAFSIR)
    db.executemany(
        "INSERT INTO tafsir VALUES (?, ?, ?, ?, ?, ?)",
        [
            # text row: the run 78:1-3, written about together
            ("78:1", "78:1", "78:1", "78:3", "78:1,78:2,78:3", "<p>About the run &amp; its ayahs</p>"),
            # pointer rows: the other two ayahs of that run
            ("78:2", "78:1", "", "", "", ""),
            ("78:3", "78:1", "", "", "", ""),
            # text row: one ayah on its own
            ("78:4", "78:4", "78:4", "78:4", "78:4", "<div>On one ayah</div>"),
            # empty row: an ayah this book says nothing about
            ("78:5", "78:5", "78:5", "78:5", "78:5", None),
        ],
    )
    db.commit()
    db.close()
    return path


def test_a_run_is_one_passage_naming_every_ayah_it_covers(qul_tafsir):
    passages = list(read_qul_tafsir(qul_tafsir))
    run = next(one for one in passages if one.id == "78:1")
    assert run.covers == ((78, 1), (78, 2), (78, 3))


def test_pointer_and_silent_rows_are_not_passages(qul_tafsir):
    """Five rows in, two passages out. The other three are not commentary."""
    assert sorted(one.id for one in read_qul_tafsir(qul_tafsir)) == ["78:1", "78:4"]


def test_markup_is_stripped_on_the_way_in(qul_tafsir):
    for passage in read_qul_tafsir(qul_tafsir):
        assert "<" not in passage.text
        assert "&amp;" not in passage.text
    assert next(iter(read_qul_tafsir(qul_tafsir))).text == "About the run & its ayahs"


def test_a_file_that_is_not_a_tafsir_export_says_so(tmp_path):
    path = tmp_path / "wrong.db"
    sqlite3.connect(path).close()
    with pytest.raises(SystemExit, match="tafsir"):
        list(read_qul_tafsir(path))


@pytest.mark.parametrize("table", ["translation", "translations"])
def test_either_name_their_exporter_uses_is_read(tmp_path, table):
    """Their export variants disagree on the table name, so it is looked up."""
    path = tmp_path / f"{table}.db"
    db = sqlite3.connect(path)
    db.executescript(QUL_TRANSLATION.replace("translations", table))
    db.execute(f"INSERT INTO {table} VALUES (1, 1, '1:1', '<i>In the name</i>', '{{}}')")  # noqa: S608
    db.commit()
    db.close()

    passages = list(read_qul_translation(path))
    assert len(passages) == 1
    assert passages[0].covers == ((1, 1),)
    assert passages[0].text == "In the name"


def test_a_translation_file_with_no_such_table_says_what_it_holds(tmp_path):
    path = tmp_path / "odd.db"
    db = sqlite3.connect(path)
    db.executescript("CREATE TABLE verses (id INTEGER)")
    db.commit()
    db.close()
    with pytest.raises(SystemExit, match="verses"):
        list(read_qul_translation(path))


def test_the_apps_own_tafsir_shape_keeps_its_runs(tmp_path):
    path = tmp_path / "app.db"
    db = sqlite3.connect(path)
    db.executescript(APP_TAFSIR)
    db.execute("INSERT INTO entry VALUES ('78:1', 'One passage')")
    db.executemany("INSERT INTO covers VALUES (?, ?, ?)", [(78, n, "78:1") for n in (1, 2, 3)])
    db.commit()
    db.close()

    passages = list(read_app_tafsir_db(path))
    assert len(passages) == 1
    assert passages[0].covers == ((78, 1), (78, 2), (78, 3))


def good() -> dict:
    return {
        "kind": "tafsir", "language": "ar", "name": "A book", "author": "Someone",
        "licence": "As the publisher states it", "origin": "qul:1", "credit": "qul",
        "format": "qul-tafsir", "file": "downloads/a.db", "confidence": "verified",
    }


def test_a_well_described_book_passes():
    check("a-book", good())


@pytest.mark.parametrize("field", ["licence", "name", "author", "origin", "credit"])
def test_a_book_the_app_could_not_describe_is_refused(field):
    """Each of these would otherwise be a blank where the reader expects to be
    told who wrote this and on what terms."""
    spec = good() | {field: ""}
    with pytest.raises(SystemExit, match=field):
        check("a-book", spec)


@pytest.mark.parametrize("field,value", [
    ("confidence", "probably"),   # a badge word the UI cannot draw
    ("kind", "poetry"),           # a kind that belongs to no panel
    ("format", "csv"),            # a shape no reader knows
])
def test_a_value_outside_the_app_s_vocabulary_is_refused(field, value):
    with pytest.raises(SystemExit, match=field):
        check("a-book", good() | {field: value})


# ── The fetched shape ────────────────────────────────────────────────────────
#
# What fetch_quran_editions.py writes: one text per ayah, no runs, because the
# open mirrors publish the books that way. Small enough to build here in full.


def fetched(tmp_path, passages) -> str:
    path = tmp_path / "book.json"
    path.write_text(
        json.dumps({"book": "A book", "passages": passages}, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def test_a_fetched_book_is_one_passage_per_ayah(tmp_path):
    path = fetched(tmp_path, [
        {"surah": 2, "ayah": 255, "text": "On the Throne Verse"},
        {"surah": 78, "ayah": 1, "text": "On the great news"},
    ])
    passages = list(read_ayah_json(path))
    assert [p.id for p in passages] == ["2:255", "78:1"]
    assert [p.covers for p in passages] == [((2, 255),), ((78, 1),)]


def test_a_fetched_ayah_with_no_text_is_not_a_passage(tmp_path):
    """A mirror that has nothing for an ayah must leave it silent, not blank.

    An empty passage would draw an empty panel under a book's name, which reads
    as "this book says nothing here" being rendered as "here is what it says".
    """
    path = fetched(tmp_path, [
        {"surah": 2, "ayah": 1, "text": ""},
        {"surah": 2, "ayah": 2, "text": "   "},
        {"surah": 2, "ayah": 3, "text": "Real"},
    ])
    assert [p.id for p in read_ayah_json(path)] == ["2:3"]


def test_a_fetched_book_is_stripped_of_markup_and_footnote_markers(tmp_path):
    """Quran.com writes footnotes as "Allah,<sup foot_note=1>1</sup> the ...".

    Removing the tag alone leaves the 1 stuck to the sentence, where it reads as
    part of the translation rather than as a marker for a note nothing shows.
    """
    path = fetched(tmp_path, [
        {"surah": 1, "ayah": 1, "text": "In the name of Allah,<sup foot_note=9>1</sup> the Merciful."},
    ])
    assert list(read_ayah_json(path))[0].text == "In the name of Allah, the Merciful."


def test_a_file_that_is_not_a_fetched_book_says_so(tmp_path):
    path = tmp_path / "book.json"
    path.write_text('{"book": "A book"}', encoding="utf-8")
    with pytest.raises(SystemExit, match="passages"):
        list(read_ayah_json(path))
