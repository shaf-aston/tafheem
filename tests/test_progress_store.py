"""What a learner has answered: the record, the review rule, and honest timing.

Three things here can go wrong quietly, which is why each has its own check.

The review schedule is the feature (FSRS-6, replayed from the saved answers): a
wrong answer is due at once, and a right one pushes the next ask further out. A
single right answer must not count as learnt, or a lucky guess between four
options would pass for knowing the word.

The timing cap is the subtle one. A question left open while somebody makes tea
is still a real answer, so it must keep its right or wrong, and must not reach
the average. Getting that backwards either loses answers or reports a learner as
slow when what happened is that they walked away.

And the store must be ignorant of the quiz. Anything with a stable id can file
answers here, so a second module's rows must not touch the first's.

Run: python -m pytest tests/test_progress_store.py
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

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


def answer_at(store, item, correct, when, module="quiz"):
    """File an answer with an explicit UTC time, as the column stores it."""
    db = store._db()
    with db:
        db.execute(
            "INSERT INTO attempts (module, item, correct, at) VALUES (?, ?, ?, ?)",
            (module, item, 1 if correct else 0, when.strftime("%Y-%m-%d %H:%M:%S")),
        )


def ago(**delta):
    return datetime.now(timezone.utc) - timedelta(**delta)


def test_a_wrong_answer_is_due_now(store):
    answer(store, "to-write", False)
    assert store.review_items("quiz") == ["to-write"]
    assert stats_for(store, "to-write")["due"] is True


def test_a_word_right_a_minute_ago_is_not_due(store):
    answer_at(store, "to-write", True, ago(minutes=1))
    row = stats_for(store, "to-write")
    assert (row["due"], row["known"]) == (False, False)
    assert store.review_items("quiz") == []


def test_right_once_comes_back_the_next_day(store):
    answer_at(store, "to-write", True, ago(hours=25))
    assert store.review_items("quiz") == ["to-write"]


def test_right_on_two_days_comes_back_a_week_later(store):
    answer_at(store, "to-write", True, ago(days=10))
    answer_at(store, "to-write", True, ago(days=9))
    assert store.review_items("quiz") == ["to-write"]


def test_right_twice_is_known_but_a_lucky_guess_is_not(store):
    answer_at(store, "learnt", True, ago(days=2))
    answer_at(store, "learnt", True, ago(days=1))
    answer_at(store, "guess", True, ago(minutes=50))
    assert stats_for(store, "learnt")["known"] is True
    assert stats_for(store, "guess")["known"] is False


def test_right_twice_in_the_same_minute_is_not_known(store):
    # The old Mistakes rule cleared a word on exactly this; it proves short-term memory only.
    answer_at(store, "rushed", True, ago(minutes=2))
    answer_at(store, "rushed", True, ago(minutes=1))
    assert stats_for(store, "rushed")["known"] is False


def test_a_new_mistake_makes_it_due_again(store):
    for correct in (False, True, True, False):
        answer(store, "to-write", correct)
    assert store.review_items("quiz") == ["to-write"]
    assert stats_for(store, "to-write")["known"] is False


def test_review_lists_the_longest_waiting_first(store):
    answer_at(store, "later", False, ago(hours=1))
    answer_at(store, "earlier", False, ago(days=2))
    assert store.review_items("quiz") == ["earlier", "later"]


def test_the_schedule_is_the_same_every_time_it_is_read(store):
    for when, correct in ((ago(days=5), False), (ago(days=4), True), (ago(days=1), True)):
        answer_at(store, "to-write", correct, when)
    first = stats_for(store, "to-write")
    assert stats_for(store, "to-write") == first
    assert first["due_at"].endswith("+00:00")


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


def test_the_summary_names_the_words_got_right(store):
    """A meaning can have several words; only the ones answered right are named."""
    for word, correct in [("رَيْب", True), ("لَبْس", False), ("رَيْب", True)]:
        store.record(module="quiz", item="doubt", correct=correct, context={"word": word})
    store.record(module="quiz", item="doubt", correct=True)  # an answer from before words were saved
    assert stats_for(store, "doubt")["words"] == ["رَيْب"]
