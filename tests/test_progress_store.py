"""What a learner has answered: the record, the review rule, and honest timing.

Three things here can go wrong quietly, which is why each has its own check.

The review rule is the feature: a word joins the list the first time it is got
wrong and leaves after two right answers in a row. Both halves matter. A rule
that never lets go turns the list into a graveyard; one that lets go on a single
right answer lets a lucky guess between four options count as learning.

The timing cap is the subtle one. A question left open while somebody makes tea
is still a real answer, so it must keep its right or wrong, and must not reach
the average. Getting that backwards either loses answers or reports a learner as
slow when what happened is that they walked away.

And the store must be ignorant of the quiz. Anything with a stable id can file
answers here, so a second module's rows must not touch the first's.

Run: python -m pytest tests/test_progress_store.py
"""
from __future__ import annotations

import pytest

from backend.config import get_settings
from backend.services import progress_store


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """A fresh database per test, made where the setting points.

    The setting is what production reads, so pointing it here also proves that
    the path really is configurable rather than baked into the module.
    """
    monkeypatch.setenv("PROGRESS_DB_PATH", "data/test-progress.db")
    get_settings.cache_clear()
    target = tmp_path / "progress.db"
    monkeypatch.setattr(progress_store, "data_path", lambda _name: target)
    progress_store.reset_connection()
    yield progress_store
    progress_store.reset_connection()
    get_settings.cache_clear()


def answer(store, item, correct, ms=None, module="quiz"):
    return store.record(module=module, item=item, correct=correct, ms=ms)


def stats_for(store, item, module="quiz"):
    return next(row for row in store.summary(module) if row["item"] == item)


def test_makes_its_own_database_and_can_be_opened_twice(store, tmp_path):
    """No build script: the first answer makes the file, and reopening keeps it."""
    answer(store, "to-write", True)
    store.reset_connection()  # a second thread, or a restart
    answer(store, "to-write", True)
    assert stats_for(store, "to-write")["attempts"] == 2


def test_records_right_and_wrong(store):
    answer(store, "to-write", True)
    answer(store, "to-write", False)
    row = stats_for(store, "to-write")
    assert (row["attempts"], row["wrong"]) == (2, 1)


def test_a_wrong_answer_puts_a_word_in_review(store):
    answer(store, "to-write", False)
    assert store.review_items("quiz") == ["to-write"]


def test_two_rights_in_a_row_clear_it(store):
    answer(store, "to-write", False)
    answer(store, "to-write", True)
    assert store.review_items("quiz") == ["to-write"], "one right answer is a coin flip"
    answer(store, "to-write", True)
    assert store.review_items("quiz") == []


def test_a_new_mistake_puts_it_back(store):
    for correct in (False, True, True, False):
        answer(store, "to-write", correct)
    assert store.review_items("quiz") == ["to-write"]


def test_a_word_never_got_wrong_is_never_in_review(store):
    answer(store, "to-write", True)
    assert store.review_items("quiz") == []
    assert stats_for(store, "to-write")["in_review"] is False


def test_a_slow_answer_counts_but_is_not_timed(store):
    """The edge the request named: past the cap, and the nearest case under it."""
    cap = get_settings().progress_timing_cap_ms
    answer(store, "to-write", True, ms=cap + 1)
    row = stats_for(store, "to-write")
    assert row["attempts"] == 1, "a slow answer is still an answer"
    assert row["avg_ms"] is None, "nobody was measured while they were away"

    answer(store, "to-write", True, ms=cap)
    assert stats_for(store, "to-write")["avg_ms"] == cap, "exactly at the cap still counts"


def test_timing_averages_only_the_honest_ones(store):
    for ms in (1_000, 3_000, 500_000):
        answer(store, "to-write", True, ms=ms)
    assert stats_for(store, "to-write")["avg_ms"] == 2_000


def test_an_untimed_answer_does_not_become_a_zero(store):
    answer(store, "to-write", True)
    answer(store, "to-write", True, ms=4_000)
    assert stats_for(store, "to-write")["avg_ms"] == 4_000


def test_modules_do_not_see_each_other(store):
    answer(store, "to-write", False, module="quiz")
    answer(store, "2:255:3", False, module="iraab")
    assert store.review_items("quiz") == ["to-write"]
    assert store.review_items("iraab") == ["2:255:3"]


def test_forget_empties_every_module_for_one_learner(store):
    answer(store, "to-write", False, module="quiz")
    answer(store, "2:255:3", False, module="iraab")
    store.record(module="quiz", item="to-read", correct=False, user="someone-else")
    assert store.forget() == 2
    assert store.review_items("quiz") == []
    assert store.review_items("iraab") == []
    assert store.review_items("quiz", "someone-else") == ["to-read"]
    assert store.forget() == 0


def test_learners_do_not_see_each_other(store):
    """No accounts yet, but the column is the whole reason sign-in stays cheap."""
    store.record(module="quiz", item="to-write", correct=False)
    store.record(module="quiz", item="to-read", correct=False, user="someone-else")
    assert store.review_items("quiz") == ["to-write"]
    assert store.review_items("quiz", "someone-else") == ["to-read"]


def test_context_is_kept_as_given(store):
    store.record(module="quiz", item="to-write", correct=True,
                 context={"bank": "quranic", "direction": "ar-en"})
    row = store._db().execute("SELECT context FROM attempts").fetchone()
    assert '"quranic"' in row["context"]
