"""When a word is next worth asking, from the answers alone (FSRS-6).

Pure: no database, no clock. Callers pass the answers and the time, so the same
answers always give the same schedule (fuzzing is off for that reason).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from typing import Iterable

from fsrs import Card, Rating, Scheduler, State

from backend.config import get_settings


@lru_cache(maxsize=1)
def _scheduler() -> Scheduler:
    # A wrong answer is due again at once (the first step is zero); a first right
    # answer waits to be confirmed another day, so one lucky guess is not learnt.
    settings = get_settings()
    return Scheduler(
        desired_retention=settings.progress_review_retention,
        enable_fuzzing=False,
        learning_steps=(timedelta(0), timedelta(hours=settings.progress_learning_hours)),
        relearning_steps=(timedelta(0),),
    )


def card_of(answers: Iterable[tuple[datetime, bool]]) -> Card:
    """Replay (when, correct) answers in order: wrong is Again, right is Good.
    Times must be timezone-aware UTC.

    A right answer before the word was due proves only short-term memory, so it
    does not move the word on; a wrong answer always counts."""
    scheduler = _scheduler()
    # A fixed id: without one the library makes an id from the clock and sleeps
    # a millisecond so the next differs. Cards here are rebuilt on every read and
    # never stored, so the id is never used.
    card = Card(card_id=0)
    for at, correct in answers:
        if correct and card.last_review is not None and at < card.due:
            continue
        card, _ = scheduler.review_card(card, Rating.Good if correct else Rating.Again, at)
    return card


def is_due(card: Card, now: datetime) -> bool:
    return card.due <= now


def is_known(card: Card, now: datetime) -> bool:
    """Out of learning and still likely recalled. One lucky right answer stays in learning."""
    return (
        card.state == State.Review
        and _scheduler().get_card_retrievability(card, now)
        >= get_settings().progress_known_retrievability
    )
