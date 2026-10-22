"""Each source's share of the candidates, cut without passage_meta.

The fast path relies on one fact about the index, that every source's passages
are one unbroken run of rowids, and must pick exactly what the SQL it replaces
picks. Both are checked here on a small index written the way the build writes.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.scripts.build_daleel_index import _META_SCHEMA, fill_meta  # noqa: E402
from backend.services.daleel import search  # noqa: E402

_SCHEMA = """
CREATE VIRTUAL TABLE passage USING fts5(
    source UNINDEXED, book UNINDEXED, locator UNINDEXED, arabic UNINDEXED,
    english, roots, fold, tokenize = 'trigram'
);
""" + _META_SCHEMA


def _rows(order):
    """Five passages per source, the word padded out more each time so every
    passage scores differently and the best two of each are a real choice."""
    return [(source, source, f"{source} {n}", "", "", "", "صلاة" + " كلمة" * (n * 3 % 5))
            for source in order for n in range(5)]


def _index(tmp_path, monkeypatch, rows):
    path = tmp_path / "daleel.db"
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    conn.executemany("INSERT INTO passage VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    fill_meta(conn)
    conn.commit()
    conn.close()
    monkeypatch.setattr(search, "data_path", lambda _key: path)


@pytest.fixture()
def built(tmp_path, monkeypatch):
    _index(tmp_path, monkeypatch, _rows(["corpus", "tafsir", "maqayees"]))


def _picked(monkeypatch, fast):
    if not fast:
        monkeypatch.setattr(search, "_source_spans", lambda: None)
    return sorted(row.locator for row in search._fairly(search._db(), '"صلاة"', 2))


def test_the_heap_picks_what_the_sql_picks(built, monkeypatch):
    fast = _picked(monkeypatch, fast=True)
    assert len(fast) == 6
    assert fast == _picked(monkeypatch, fast=False)


def test_the_runs_are_read_from_the_index(built):
    spans = search._source_spans()
    assert spans.sources == ("corpus", "tafsir", "maqayees")
    assert spans.starts == (1, 6, 11)


def test_an_index_not_written_a_source_at_a_time_falls_back(tmp_path, monkeypatch):
    rows = _rows(["corpus", "tafsir"])
    _index(tmp_path, monkeypatch, rows[::2] + rows[1::2])
    assert search._source_spans() is None
    assert len(_picked(monkeypatch, fast=True)) == 4
