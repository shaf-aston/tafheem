"""What a learner has answered, right and wrong, and how long it took.

Deliberately ignorant of what an item is. It stores a module's own stable id and
nothing about the thing itself: the quiz sends a meaningKey, a future i'raab or
dictation panel sends whatever names its own questions. What kind of word that
id refers to is the caller's business, and the caller already holds the table
that says so; copying those tags in here would make a second copy that goes
stale every time the word list is rebuilt.

`user` is the learner's username (services/learner/username.py), or a guest record for
answers given while nobody is logged in: the device's own ("guest:<id>"), or GUEST from a
page that names no device. The questions table is a cache of AI answers shared by
everyone, so it stays under GUEST and lifecycle.claim_guest leaves it alone.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from backend.config import get_settings
from backend.services.learner import review_schedule
from backend.services.learner import rewards as reward_rules
from backend.services.learner.progress_db import connection
from backend.services.learner.username import GUEST


# Counts and timing in one pass. Whether an item is due is not here: it is worked
# out by replaying the item's answers (see _replay), so nothing extra is stored.
_SUMMARY = """
SELECT item,
       COUNT(*)                                              AS attempts,
       SUM(1 - correct)                                      AS wrong,
       AVG(CASE WHEN ms IS NOT NULL AND ms <= ? THEN ms END) AS avg_ms
FROM attempts
WHERE user = ? AND module = ?
GROUP BY item
ORDER BY item
"""

# The words a meaning was answered right through, so coverage credits the word
# asked and not a synonym. '' stands for right answers saved before words were.
_WORDS = """
SELECT DISTINCT item,
       CASE WHEN json_type(context, '$.word') = 'text' THEN json_extract(context, '$.word') ELSE '' END AS word
FROM attempts
WHERE user = ? AND module = ? AND correct = 1
ORDER BY item, word
"""

# One learner's every module in one pass, for the overview.
_MODULES = """
SELECT module, COUNT(*) AS attempts, SUM(correct) AS correct, MAX(at) AS last_at
FROM attempts
WHERE user = ?
GROUP BY module
ORDER BY module
"""

# `at` is UTC; the shift ("+60 minutes") gives the learner's day.
_DAYS = "SELECT DISTINCT date(at, ?) AS day FROM attempts WHERE user = ? ORDER BY day DESC"
# How far back the overview lists the days answered in: two weeks covers this week from any weekday.
_RECENT_DAYS = 14

# One row per (item, local day) answered right: XP source.
_EARNED = "SELECT DISTINCT module, item, date(at, ?) AS day FROM attempts WHERE user = ? AND correct = 1"

_EARNED_TODAY = (
    "SELECT 1 FROM attempts WHERE user = ? AND module = ? AND item = ? AND correct = 1 AND date(at, ?) = ? LIMIT 1"
)

_ANSWERS = "SELECT item, at, correct FROM attempts WHERE user = ? AND module = ? ORDER BY id"

# Every answer one learner gave, in every module, for the overview's learnt counts in one read.
_EVERY_ANSWER = "SELECT module, item, at, correct FROM attempts WHERE user = ? ORDER BY id"


def record(
    *,
    module: str,
    item: str,
    correct: bool,
    ms: int | None = None,
    context: dict | None = None,
    user: str = GUEST,
) -> int:
    """File one answer. Returns the row id, so a caller can prove it landed."""
    db = connection()
    with db:
        cursor = db.execute(
            "INSERT INTO attempts (user, module, item, correct, ms, context) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                user,
                module,
                item,
                1 if correct else 0,
                ms,
                json.dumps(context, ensure_ascii=False) if context else None,
            ),
        )
    return int(cursor.lastrowid)


def leave_feedback(*, module: str, message: str, item: str | None = None, user: str = GUEST) -> int:
    """File a note about something that looks wrong. Kept apart from answers, so
    the Settings wipe clears a learner's record without losing their reports."""
    db = connection()
    with db:
        cursor = db.execute(
            "INSERT INTO feedback (user, module, item, message) VALUES (?, ?, ?, ?)",
            (user, module, item, message),
        )
    return int(cursor.lastrowid)


def keep_questions(
    *, module: str, sentence: str, questions: list[dict], source: str, user: str = GUEST,
) -> int:
    """File generated questions as they were shown. Returns how many were new.

    A question already kept for this sentence is skipped rather than doubled,
    so asking again, or the page firing twice, leaves one copy.
    """
    rows = [
        (user, module, sentence, q["question"], q["answer"], q.get("hint"), source)
        for q in questions
        if q.get("question") and q.get("answer")
    ]
    db = connection()
    with db:
        before = db.total_changes
        db.executemany(
            "INSERT OR IGNORE INTO questions (user, module, sentence, question, answer, hint, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        return db.total_changes - before


def kept_questions(module: str, sentence: str | None = None, user: str = GUEST) -> list[dict]:
    """Questions filed by keep_questions, oldest first; for one sentence when given."""
    sql = "SELECT sentence, question, answer, hint, source, at FROM questions WHERE user = ? AND module = ?"
    args: list = [user, module]
    if sentence is not None:
        sql += " AND sentence = ?"
        args.append(sentence)
    return [dict(row) for row in connection().execute(sql + " ORDER BY id", args).fetchall()]


def learnt(module: str, name: str) -> int:
    """How many items this name has learnt in `module`: the leaderboard's measure."""
    now = datetime.now(timezone.utc)
    return sum(review_schedule.is_known(card, now) for card in _replay(module, name).values())


def _learnt_everywhere(user: str) -> dict[str, int]:
    """`learnt` for every module this learner answered in, from one read of their answers: the overview is read
    again after every answer, so it does not replay module by module."""
    now = datetime.now(timezone.utc)
    cards = _fold(connection().execute(_EVERY_ANSWER, (user,)), lambda row: (row["module"], row["item"]))
    counts: dict[str, int] = {}
    for (module, _item), card in cards.items():
        counts[module] = counts.get(module, 0) + review_schedule.is_known(card, now)
    return counts


def _shift(minutes: int) -> str:
    """SQLite date modifier for `minutes` east of UTC."""
    return f"{minutes:+d} minutes"


def local_today(minutes: int = 0):
    """The learner's today."""
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).date()


def earns(module: str, item: str, user: str, minutes: int = 0) -> bool:
    """True if this item has not been answered right yet today (so a right answer earns)."""
    found = connection().execute(_EARNED_TODAY, (user, module, item, _shift(minutes), local_today(minutes).isoformat()))
    return found.fetchone() is None


def rewards(user: str, minutes: int = 0) -> dict:
    """XP, XP today, level and streak, on the learner's days (services/learner/rewards.py)."""
    settings = get_settings()
    today = local_today(minutes)
    days = [datetime.fromisoformat(row["day"]).date() for row in connection().execute(_EARNED, (_shift(minutes), user))]
    answered = [datetime.fromisoformat(row["day"]).date() for row in connection().execute(_DAYS, (_shift(minutes), user))]
    return {
        **reward_rules.rewards_of(days, today, settings.rewards_xp_per_answer, settings.rewards_level_step),
        "streak": reward_rules.streak(answered, today),
    }


def overview(user: str, minutes: int = 0) -> dict:
    """Every module this learner answered in, the totals, the streak of days, and the days of the last two weeks.

    Learnt is the leaderboard's measure. Streak counts the learner's days. `days` are the local days answered in
    since 13 days ago, newest first: enough for a week view on any weekday, without sending the whole history.
    """
    known = _learnt_everywhere(user)
    modules = [
        {**dict(row), "learnt": known.get(row["module"], 0),
         "last_at": datetime.fromisoformat(row["last_at"]).replace(tzinfo=timezone.utc).isoformat()}
        for row in connection().execute(_MODULES, (user,))
    ]
    totals = {key: sum(row[key] for row in modules) for key in ("attempts", "correct", "learnt")}
    days = [datetime.fromisoformat(row["day"]).date() for row in connection().execute(_DAYS, (_shift(minutes), user))]
    today = local_today(minutes)
    recent = [day.isoformat() for day in days if day > today - timedelta(days=_RECENT_DAYS)]
    return {"modules": modules, **totals, "streak": reward_rules.streak(days, today), "days": recent}


def _answers(module: str, name: str) -> int:
    return connection().execute("SELECT COUNT(*) FROM attempts WHERE user = ? AND module = ?", (name, module)).fetchone()[0]


def ranked(names: list[str], module: str) -> list[dict]:
    """These accounts by words learnt in `module`, most first; ties share a rank.

    Replays each account's answers, which is fine at the size this app is.
    """
    rows = sorted(
        ({"name": name, "learnt": learnt(module, name), "answers": _answers(module, name)} for name in names),
        key=lambda row: (-row["learnt"], row["name"]),
    )
    for row in rows:
        row["rank"] = 1 + sum(other["learnt"] > row["learnt"] for other in rows)
    return rows


def summary(module: str, user: str = GUEST) -> list[dict]:
    """Every item this learner has answered in this module, with its record.

    `avg_ms` is measured only over answers quicker than the cap. A question left
    open while somebody makes tea is still a real answer, so it keeps its right
    or wrong, but letting it into an average would say the learner is slow when
    what happened is that they walked away. None means nothing timed honestly.
    """
    cap = get_settings().progress_timing_cap_ms
    rows = connection().execute(_SUMMARY, (cap, user, module)).fetchall()
    cards = _replay(module, user)
    words: dict[str, list[str]] = {}
    for row in connection().execute(_WORDS, (user, module)):
        words.setdefault(row["item"], []).append(row["word"])
    now = datetime.now(timezone.utc)

    return [
        {
            "item": row["item"],
            "attempts": row["attempts"],
            "wrong": row["wrong"],
            "avg_ms": round(row["avg_ms"]) if row["avg_ms"] is not None else None,
            "due": review_schedule.is_due(cards[row["item"]], now),
            "known": review_schedule.is_known(cards[row["item"]], now),
            "due_at": cards[row["item"]].due.isoformat(),
            "words": words.get(row["item"], []),
        }
        for row in rows
    ]


def _replay(module: str, user: str) -> dict:
    """Each item's FSRS card in `module`."""
    return _fold(connection().execute(_ANSWERS, (user, module)), lambda row: row["item"])


def _fold(rows, key) -> dict:
    """An FSRS card per `key(row)`, folded from saved answers in the order given.
    `at` is UTC text with no zone, so the zone is added here."""
    answers: dict = {}
    for row in rows:
        at = datetime.fromisoformat(row["at"]).replace(tzinfo=timezone.utc)
        answers.setdefault(key(row), []).append((at, bool(row["correct"])))
    return {found: review_schedule.card_of(rows) for found, rows in answers.items()}


def review_items(module: str, user: str = GUEST) -> list[str]:
    """Items due now, earliest due first."""
    due = [row for row in summary(module, user) if row["due"]]
    return [row["item"] for row in sorted(due, key=lambda row: datetime.fromisoformat(row["due_at"]))]
