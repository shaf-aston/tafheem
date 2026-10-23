"""Which passages a search considers: a root is looked for where roots are kept.

Only the Qur'an and the dictionaries say which roots a passage holds. A root
matched in the text instead is three letters inside any word, and the passages
it found that way could never rank as a root match; they took each book's
share of the candidates from the passages that did answer.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.scripts.build_daleel_index import _META_SCHEMA, fill_meta  # noqa: E402
from backend.services.daleel.index import connection  # noqa: E402
from backend.services.daleel.index.candidates import candidates  # noqa: E402
from backend.services.daleel.query.expand import Expansion  # noqa: E402

_SCHEMA = """
CREATE VIRTUAL TABLE passage USING fts5(
    source UNINDEXED, book UNINDEXED, locator UNINDEXED, arabic UNINDEXED,
    english, roots, fold, tokenize = 'trigram'
);
""" + _META_SCHEMA

ROWS = [
    # An ayah, which the build files under its roots.
    ("corpus", "corpus", "1:3", "", "", "رحم", "الرحمن الرحيم"),
    # A book that says رحمة but holds no roots, and never says mercy.
    ("fiqh-books", "مختصر القدوري", "1", "", "", "", "باب رحمة الله"),
    # A book that answers the question as typed.
    ("fiqh-books", "مختصر القدوري", "2", "", "mercy to the poor", "", "باب"),
]


def _index(tmp_path, monkeypatch):
    path = tmp_path / "daleel.db"
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    conn.executemany("INSERT INTO passage VALUES (?, ?, ?, ?, ?, ?, ?)", ROWS)
    fill_meta(conn)
    conn.commit()
    conn.close()
    monkeypatch.setattr(connection, "data_path", lambda _key: path)


def test_a_root_is_matched_in_the_roots_column_only(tmp_path, monkeypatch):
    _index(tmp_path, monkeypatch)
    mercy = Expansion(typed=("mercy",), related=(), roots=("رحم",), loose=())
    found = {row.locator for row in candidates(connection.db(), mercy, 240)}
    assert found == {"1:3", "2"}


def test_a_root_that_is_also_a_word_is_still_read_as_a_word(tmp_path, monkeypatch):
    """صبر is a translation and its own root: typed as a word, it is looked for
    in the text, roots or none."""
    _index(tmp_path, monkeypatch)
    rahma = Expansion(typed=("رحمة",), related=(), roots=("رحمة",), loose=())
    found = {row.locator for row in candidates(connection.db(), rahma, 240)}
    assert found == {"1"}
