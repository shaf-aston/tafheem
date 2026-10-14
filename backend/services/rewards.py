"""XP and level: how much a learner has grown, from the answers alone.

Pure, like review_schedule.py: no database and no clock. progress_store.py
reads the answers and the day; this decides what they are worth.

The two rules:
  - a right answer earns `xp_per_answer`, once per item per day. Saying the same
    word ten times in one evening earns it once; saying it right again tomorrow
    earns it again. So XP rewards coming back, and cannot be bought by
    hammering one button. A wrong answer earns nothing and costs nothing.
  - level n needs `level_step * n` XP to reach level n + 1, so each level takes
    a little longer than the one before: 100 to level 2, 200 more to level 3.

What a level is called (seed, sprout, ...) is the page's business (rewards.json
in the frontend). This only counts.
"""
from __future__ import annotations

from datetime import date
from typing import Iterable


def level_of(xp: int, step: int) -> dict:
    """The level `xp` reaches, how far into it, and how much that level needs in all."""
    level, into, need = 1, xp, step
    while into >= need:
        into -= need
        level += 1
        need = step * level
    return {"level": level, "into": into, "need": need}


def rewards_of(earned_days: Iterable[date], today: date, per_answer: int, step: int) -> dict:
    """Everything the page shows about XP. `earned_days` has one entry per item
    answered right on a day (its local day), however many times it was said that day."""
    days = list(earned_days)
    xp = per_answer * len(days)
    return {"xp": xp, "xpToday": per_answer * sum(day == today for day in days), **level_of(xp, step)}
