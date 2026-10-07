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

`user` is the learner's typed name (services/profile.py), or 'local' for answers
given before names existed. The questions table is a cache of AI answers shared
by everyone, so it stays under 'local' and claim_local leaves it alone.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone

from backend.config import data_path, get_settings
from backend.services import review_schedule

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
-- Questions a panel generated, kept the moment they were made so an AI answer
-- is paid for once and can be read back later. `source` is the provenance key
-- the page showed (sources.json), so a row says who wrote it the same way the
-- badge did. The same question for the same sentence is kept once.
CREATE TABLE IF NOT EXISTS questions (
    id       INTEGER PRIMARY KEY,
    user     TEXT    NOT NULL DEFAULT 'local',
    module   TEXT    NOT NULL,
    sentence TEXT    NOT NULL,
    question TEXT    NOT NULL,
    answer   TEXT    NOT NULL,
    hint     TEXT,
    source   TEXT    NOT NULL,
    at       TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user, module, sentence, question)
);
CREATE INDEX IF NOT EXISTS ix_questions ON questions (user, module, sentence, id);
CREATE TABLE IF NOT EXISTS feedback (
    id      INTEGER PRIMARY KEY,
    user    TEXT    NOT NULL DEFAULT 'local',
    module  TEXT    NOT NULL,
    item    TEXT,
    message TEXT    NOT NULL,
    at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

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

_ANSWERS = "SELECT item, at, correct FROM attempts WHERE user = ? AND module = ? ORDER BY id"


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


def keep_questions(
    *, module: str, sentence: str, questions: list[dict], source: str, user: str = "local",
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
    db = _db()
    with db:
        before = db.total_changes
        db.executemany(
            "INSERT OR IGNORE INTO questions (user, module, sentence, question, answer, hint, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        return db.total_changes - before


def kept_questions(module: str, sentence: str | None = None, user: str = "local") -> list[dict]:
    """Questions filed by keep_questions, oldest first; for one sentence when given."""
    sql = "SELECT sentence, question, answer, hint, source, at FROM questions WHERE user = ? AND module = ?"
    args: list = [user, module]
    if sentence is not None:
        sql += " AND sentence = ?"
        args.append(sentence)
    return [dict(row) for row in _db().execute(sql + " ORDER BY id", args).fetchall()]


def forget(user: str = "local") -> int:
    """Delete every answer this learner has given, in every module. Returns how many.

    Whole learner, not per module: the button that calls it says "clear it all",
    and a list of module names here would drift from the panels that file answers.
    """
    db = _db()
    with db:
        cursor = db.execute("DELETE FROM attempts WHERE user = ?", (user,))
    return int(cursor.rowcount)


def claim_local(user: str) -> int:
    """Move the unnamed answers and reports onto `user`. Returns how many answers moved."""
    db = _db()
    with db:
        moved = db.execute("UPDATE attempts SET user = ? WHERE user = 'local'", (user,)).rowcount
        db.execute("UPDATE feedback SET user = ? WHERE user = 'local'", (user,))
    return int(moved)


def summary(module: str, user: str = "local") -> list[dict]:
    """Every item this learner has answered in this module, with its record.

    `avg_ms` is measured only over answers quicker than the cap. A question left
    open while somebody makes tea is still a real answer, so it keeps its right
    or wrong, but letting it into an average would say the learner is slow when
    what happened is that they walked away. None means nothing timed honestly.
    """
    cap = get_settings().progress_timing_cap_ms
    rows = _db().execute(_SUMMARY, (cap, user, module)).fetchall()
    cards = _replay(module, user)
    words: dict[str, list[str]] = {}
    for row in _db().execute(_WORDS, (user, module)):
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
    """Each item's FSRS card, folded from its saved answers in the order given.
    `at` is UTC text with no zone, so the zone is added here."""
    answers: dict[str, list[tuple[datetime, bool]]] = {}
    for row in _db().execute(_ANSWERS, (user, module)):
        at = datetime.fromisoformat(row["at"]).replace(tzinfo=timezone.utc)
        answers.setdefault(row["item"], []).append((at, bool(row["correct"])))
    return {item: review_schedule.card_of(rows) for item, rows in answers.items()}


def review_items(module: str, user: str = "local") -> list[str]:
    """Items due now, earliest due first."""
    due = [row for row in summary(module, user) if row["due"]]
    return [row["item"] for row in sorted(due, key=lambda row: datetime.fromisoformat(row["due_at"]))]
