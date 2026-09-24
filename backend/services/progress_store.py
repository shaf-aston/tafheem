"""What a learner has answered, right and wrong, and how long it took.

The only module that opens data/progress.db, and the first thing in this app to
write to a database while serving. Every other store here is built once by a
script and read afterwards, so the rules that make a read-only store safe are
not enough: this one opens read-write, in WAL mode, with a busy timeout, because
FastAPI answers on several threads and two answers can land at once.

Deliberately ignorant of what an item is. It stores a module's own stable id and
nothing about the thing itself: the quiz sends a meaningKey, a future i'raab or
dictation panel sends whatever names its own questions. What kind of word that
id refers to is the caller's business, and the caller already holds the table
that says so; copying those tags in here would make a second copy that goes
stale every time the word list is rebuilt.

`user` is a column, not a feature. There are no accounts yet, so everything is
filed under 'local'. When there are, the router passes a real name and nothing
in here changes.
"""
from __future__ import annotations

import json
import sqlite3
import threading

from backend.config import data_path, get_settings

_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id      INTEGER PRIMARY KEY,
    user    TEXT    NOT NULL DEFAULT 'local',
    module  TEXT    NOT NULL,
    item    TEXT    NOT NULL,
    correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
    ms      INTEGER CHECK (ms >= 0),
    context TEXT,
    at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_attempts ON attempts (user, module, item, id);
CREATE TABLE IF NOT EXISTS feedback (
    id      INTEGER PRIMARY KEY,
    user    TEXT    NOT NULL DEFAULT 'local',
    module  TEXT    NOT NULL,
    item    TEXT,
    message TEXT    NOT NULL,
    at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# One pass for everything the callers ask. `last_wrong` is the newest wrong
# answer for an item and `since_wrong` counts what has been answered after it,
# all of which is necessarily right, so the review rule below is a comparison
# rather than a second query.
_SUMMARY = """
WITH agg AS (
    SELECT item,
           COUNT(*)                                              AS attempts,
           SUM(1 - correct)                                      AS wrong,
           AVG(CASE WHEN ms IS NOT NULL AND ms <= ? THEN ms END) AS avg_ms,
           MAX(CASE WHEN correct = 0 THEN id END)                AS last_wrong
    FROM attempts
    WHERE user = ? AND module = ?
    GROUP BY item
)
SELECT agg.*,
       (SELECT COUNT(*) FROM attempts a
         WHERE a.user = ? AND a.module = ? AND a.item = agg.item
           AND a.id > agg.last_wrong)                            AS since_wrong
FROM agg
ORDER BY agg.item
"""


def _db() -> sqlite3.Connection:
    """One read-write connection per thread, with the file made if it is missing.

    WAL so a read of the summary never blocks a write of an answer, and a busy
    timeout because without one SQLite gives up the instant two writes overlap,
    which auto-advance answering makes ordinary rather than rare.
    """
    if getattr(_local, "db", None) is None:
        path = data_path("progress_db_path")
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(path, check_same_thread=False)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(f"PRAGMA busy_timeout={get_settings().progress_busy_timeout_ms}")
        db.executescript(SCHEMA)
        db.commit()
        _local.db = db
    return _local.db


def reset_connection() -> None:
    """Forget this thread's connection, so a test can point the setting elsewhere."""
    db = getattr(_local, "db", None)
    if db is not None:
        db.close()
    _local.db = None


def record(
    *,
    module: str,
    item: str,
    correct: bool,
    ms: int | None = None,
    context: dict | None = None,
    user: str = "local",
) -> int:
    """File one answer. Returns the row id, so a caller can prove it landed."""
    db = _db()
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


def leave_feedback(*, module: str, message: str, item: str | None = None, user: str = "local") -> int:
    """File a note about something that looks wrong. Kept apart from answers, so
    the Settings wipe clears a learner's record without losing their reports."""
    db = _db()
    with db:
        cursor = db.execute(
            "INSERT INTO feedback (user, module, item, message) VALUES (?, ?, ?, ?)",
            (user, module, item, message),
        )
    return int(cursor.lastrowid)


def forget(user: str = "local") -> int:
    """Delete every answer this learner has given, in every module. Returns how many.

    Whole learner, not per module: the button that calls it says "clear it all",
    and a list of module names here would drift from the panels that file answers.
    """
    db = _db()
    with db:
        cursor = db.execute("DELETE FROM attempts WHERE user = ?", (user,))
    return int(cursor.rowcount)


def summary(module: str, user: str = "local") -> list[dict]:
    """Every item this learner has answered in this module, with its record.

    `avg_ms` is measured only over answers quicker than the cap. A question left
    open while somebody makes tea is still a real answer, so it keeps its right
    or wrong, but letting it into an average would say the learner is slow when
    what happened is that they walked away. None means nothing timed honestly.
    """
    settings = get_settings()
    cap = settings.progress_timing_cap_ms
    clear_streak = settings.progress_review_clear_streak
    rows = _db().execute(_SUMMARY, (cap, user, module, user, module)).fetchall()

    return [
        {
            "item": row["item"],
            "attempts": row["attempts"],
            "wrong": row["wrong"],
            "avg_ms": round(row["avg_ms"]) if row["avg_ms"] is not None else None,
            # An item joins the review list the first time it is got wrong and
            # leaves after enough right answers in a row since then, counted
            # wherever they happened. Held nowhere: it is read back out of the
            # answers themselves, so there is no second record to drift.
            "in_review": row["last_wrong"] is not None and row["since_wrong"] < clear_streak,
        }
        for row in rows
    ]


def review_items(module: str, user: str = "local") -> list[str]:
    """Just the items still waiting to be got right, newest rule, same one pass."""
    return [row["item"] for row in summary(module, user) if row["in_review"]]
