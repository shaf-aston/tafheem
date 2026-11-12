"""Champion lists must pick exactly what scoring every match picks, only faster.

A small index of made-up passages, with a few words common enough to get lists
short enough to fill, so every branch is walked: a full list and its floor, a
source the list covers whole, a passage re-scored for a word its list left out,
and a question the lists turn away.
"""
from __future__ import annotations

import random
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.scripts.daleel.build_daleel_index import (  # noqa: E402
    _META_SCHEMA,
    _WORD_SCHEMA,
    fill_meta,
    fill_words,
)
from backend.services.daleel.index import champions, connection, share  # noqa: E402
from backend.services.text import fts  # noqa: E402

_SCHEMA = """
CREATE VIRTUAL TABLE passage USING fts5(
    source UNINDEXED, book UNINDEXED, locator UNINDEXED, arabic UNINDEXED,
    english, roots, fold, tokenize = 'trigram'
);
""" + _WORD_SCHEMA + _META_SCHEMA

# Common, middling and rare, so a question mixes words with and without lists.
_ARABIC = ["قال", "الله", "كان", "علم", "الكلام", "صبر", "رحمة", "النحو", "زيد", "عمرو"]
_WEIGHTS = [30, 25, 20, 12, 10, 3, 2, 2, 1, 1]
_ENGLISH = ["God", "said", "mercy", "patience", "the", "book"]
_DEPTH = 6


def _passages(rng: random.Random) -> list[tuple[str, ...]]:
    rows = []
    for source, size in (("corpus", 120), ("nahw-books", 200), ("maqayees", 15)):
        for n in range(size):
            fold = " ".join(rng.choices(_ARABIC, _WEIGHTS, k=rng.randint(2, 14)))
            english = " ".join(rng.choices(_ENGLISH, k=rng.randint(0, 6)))
            rows.append((source, source, f"{source} {n}", fold, english, "", fold))
    return rows


@pytest.fixture()
def built(tmp_path, monkeypatch):
    path = tmp_path / "daleel.db"
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    conn.executemany("INSERT INTO passage VALUES (?, ?, ?, ?, ?, ?, ?)", _passages(random.Random(7)))
    fill_words(conn)
    fill_meta(conn)
    left_out: list[str] = []
    kept = champions.fill(conn, least_hits=20, depth=_DEPTH, say=left_out.append)
    conn.close()
    monkeypatch.setattr(connection, "data_path", lambda _key: path)
    return kept, left_out


def _ordinary(monkeypatch):
    monkeypatch.setattr(champions, "best", lambda *_args: None)


def _picked(phrases, per_source):
    return [row.key for row in share.fairly(connection.db(), phrases, per_source)]


def test_every_common_word_gets_a_list_its_scores_reproduce(built):
    kept, left_out = built
    words = champions.stored(connection.db()).words
    assert kept == len(words) >= 6
    assert left_out == []
    # English is counted as the trigram index counts it, whatever its case.
    assert '"god"' in words


def test_the_lists_pick_what_scoring_every_match_picks(built, monkeypatch):
    rng = random.Random(11)
    vocabulary = [*_ARABIC, *(w.lower() for w in _ENGLISH), "قال الله", "علم الكلام"]
    questions = [[fts.quoted(w) for w in rng.sample(vocabulary, rng.randint(1, 4))] for _ in range(120)]
    sizes = [rng.randint(1, _DEPTH - 1) for _ in questions]

    answered = 0
    real = champions.best
    conn = connection.db()
    spans = share.source_spans(conn)
    for phrases, size in zip(questions, sizes):
        answered += real(conn, phrases, size, spans.starts) is not None
    fast = [_picked(phrases, size) for phrases, size in zip(questions, sizes)]

    _ordinary(monkeypatch)
    assert fast == [_picked(phrases, size) for phrases, size in zip(questions, sizes)]
    # Both paths are walked: many questions answered from the lists, some turned away.
    assert len(questions) > answered > len(questions) // 3


def test_a_page_as_long_as_a_list_is_asked_the_ordinary_way(built):
    conn = connection.db()
    starts = share.source_spans(conn).starts
    assert champions.best(conn, ['"قال"'], _DEPTH - 1, starts) is not None
    assert champions.best(conn, ['"قال"'], _DEPTH, starts) is None


def test_a_question_with_no_common_word_is_asked_the_ordinary_way(built):
    conn = connection.db()
    assert champions.best(conn, ['"زيد عمرو"', 'roots:"قول"'], 2, share.source_spans(conn).starts) is None


def test_an_index_without_lists_still_searches(built, monkeypatch):
    conn = sqlite3.connect(connection.data_path("daleel_index_path"))
    conn.executescript("DROP TABLE champion; DROP TABLE champion_word; DROP TABLE champion_corpus;")
    conn.close()
    assert champions.stored(connection.db()) is None
    assert len(_picked(['"قال"'], 2)) == 6


def test_the_score_is_fts5s_own(built):
    conn = connection.db()
    lists = champions.stored(conn)
    for phrase, word in lists.words.items():
        for rowid, rank in conn.execute("SELECT rowid, rank FROM passage WHERE passage MATCH ?", (phrase,)):
            columns = conn.execute(
                f"SELECT {', '.join(champions.SEARCHED)} FROM passage WHERE rowid = ?", (rowid,),
            ).fetchone()
            assert champions.score(word.word, champions.lowered(columns), word.hits, lists.corpus) == pytest.approx(
                rank, rel=1e-9,
            )


def test_the_timing_says_which_way_the_scores_were_found(built):
    conn = connection.db()
    answered: list[str] = []
    share.fairly(conn, ['"قال"'], 2, lap=answered.append)
    turned_away: list[str] = []
    share.fairly(conn, ['"قال"'], _DEPTH, lap=turned_away.append)
    assert answered == ["lists"]
    assert turned_away == ["lists", "scored"]
