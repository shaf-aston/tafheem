"""Skipping the commonest words must pick exactly what scoring every match picks.

The made-up index of the champion tests, with the bar for "commonest" lowered
so its common words qualify, and both ways a source can be finished walked:
the common words counted in the text of the few passages near the bar, and
FTS5 scoring a whole source that has no bar.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import get_settings  # noqa: E402
from backend.services.daleel.index import champions, connection, max_score, share  # noqa: E402
from backend.services.text import fts  # noqa: E402
from tests.daleel.test_daleel_champions import _ARABIC, _ENGLISH, built  # noqa: E402,F401


@pytest.fixture()
def commonest(built, monkeypatch):  # noqa: F811
    monkeypatch.setattr(get_settings(), "daleel_skip_word_share", 0.3)
    monkeypatch.setattr(champions, "best", lambda *_args: None)  # so max_score is what answers
    return connection.db()


def _picked(phrases, per_source):
    return [row.key for row in share.fairly(connection.db(), phrases, per_source)]


def test_it_picks_what_scoring_every_match_picks(commonest, monkeypatch):
    rng = random.Random(5)
    vocabulary = [*_ARABIC, *(w.lower() for w in _ENGLISH), "قال الله", "علم الكلام"]
    questions = [[fts.quoted(w) for w in rng.sample(vocabulary, rng.randint(2, 5))] for _ in range(150)]
    sizes = [rng.randint(1, 12) for _ in questions]

    spans = share.source_spans(commonest)
    answered = sum(max_score.best(commonest, q, n, spans.starts) is not None for q, n in zip(questions, sizes))
    skimmed = [_picked(q, n) for q, n in zip(questions, sizes)]

    monkeypatch.setattr(max_score, "best", lambda *_args: None)
    assert skimmed == [_picked(q, n) for q, n in zip(questions, sizes)]
    assert len(questions) > answered > 0


@pytest.mark.parametrize("text_most", [1, 10_000])
def test_both_ways_of_finishing_a_source_agree(commonest, monkeypatch, text_most):
    """1 sends every source to FTS5 whole; 10,000 lets every barred source be read from text."""
    monkeypatch.setattr(get_settings(), "daleel_skip_text_most", text_most)
    phrases = ['"قال"', '"الله"', '"زيد"', '"علم الكلام"']
    skimmed = _picked(phrases, 3)
    monkeypatch.setattr(max_score, "best", lambda *_args: None)
    assert skimmed == _picked(phrases, 3)


def test_a_question_with_nothing_to_skip_is_asked_the_ordinary_way(commonest):
    starts = share.source_spans(commonest).starts
    assert max_score.best(commonest, ['"زيد"', '"عمرو"'], 2, starts) is None  # nothing common
    assert max_score.best(commonest, ['"قال"'], 2, starts) is None  # nothing left once it is skipped


def test_no_passage_can_beat_the_ceiling(built):  # noqa: F811
    conn = connection.db()
    lists = champions.stored(conn)
    for phrase, word in lists.words.items():
        lowest = conn.execute("SELECT min(rank) FROM passage WHERE passage MATCH ?", (phrase,)).fetchone()[0]
        assert -champions.ceiling(word.hits, lists.corpus) < lowest


def test_the_timing_says_the_commonest_words_were_skipped(commonest):
    steps: list[str] = []
    share.fairly(commonest, ['"قال"', '"زيد"'], 2, lap=steps.append)
    assert steps == ["lists", "skimmed"]
