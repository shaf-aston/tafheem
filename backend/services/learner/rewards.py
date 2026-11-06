"""XP and level from answers. Pure; attempts.py feeds it.

- A right answer earns `xp_per_answer` once per item per local day; wrong earns 0.
- Level n needs `level_step * n` XP to reach n + 1.
Level names live in frontend/src/config/rewards.json.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable


def level_of(xp: int, step: int) -> dict:
    """Level reached, XP into it, XP that level needs."""
    level, into, need = 1, xp, step
    while into >= need:
        into -= need
        level += 1
        need = step * level
    return {"level": level, "into": into, "need": need}


def rewards_of(earned_days: Iterable[date], today: date, per_answer: int, step: int) -> dict:
    """`earned_days`: one local date per (item, day) answered right."""
    days = list(earned_days)
    xp = per_answer * len(days)
    return {"xp": xp, "xpToday": per_answer * sum(day == today for day in days), **level_of(xp, step)}


def streak(days: list, today: date) -> int:
    """Days in a row with an answer, newest first in `days` (the learner's own days). Today counts;
    a day not yet answered in leaves yesterday's streak standing."""
    day = today if days and days[0] == today else today - timedelta(days=1)
    count = 0
    for answered in days:
        if answered != day:
            break
        count += 1
        day -= timedelta(days=1)
    return count
