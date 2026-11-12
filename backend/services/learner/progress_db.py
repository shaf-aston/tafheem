"""The only module that opens data/progress.db, and the first thing in this app to
write to a database while serving. Every other store here is built once by a
script and read afterwards, so the rules that make a read-only store safe are
not enough: this one opens read-write, in WAL mode, with a busy timeout, because
FastAPI answers on several threads and two answers can land at once.
"""
from __future__ import annotations

import sqlite3
import threading

from backend.config import data_path, get_settings
from backend.services.learner.username import DEVICE, GUEST


_local = threading.local()

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS attempts (
    id      INTEGER PRIMARY KEY,
    user    TEXT    NOT NULL DEFAULT '{GUEST}',
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
    user     TEXT    NOT NULL DEFAULT '{GUEST}',
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
    user    TEXT    NOT NULL DEFAULT '{GUEST}',
    module  TEXT    NOT NULL,
    item    TEXT,
    message TEXT    NOT NULL,
    at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS accounts (
    name TEXT PRIMARY KEY,
    at   TEXT NOT NULL DEFAULT (datetime('now'))
);
-- The shelf: everything the page keeps for one account (settings, Grow steps,
-- favourites), as the page's own key -> text, one JSON object per name. Opaque
-- here on purpose: the page owns those keys, so a new one needs no change here.
CREATE TABLE IF NOT EXISTS saved (
    user TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    at   TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Changes to tables that already exist, in order; PRAGMA user_version counts how many ran.
# Append only: a step that has run on a learner's file never runs again.
MIGRATIONS = (
    # Passphrase and sign-in key columns, dropped by step 3; kept so a fresh file runs the same steps as an old one.
    "ALTER TABLE accounts ADD COLUMN pass TEXT; ALTER TABLE accounts ADD COLUMN key TEXT;",
    # Circles replace teams. `public` is whether the account shows in the global ranking. Every old team
    # becomes a circle named for its owner (admin, joined); its members are INVITED, since they never agreed.
    # `teams` is made first only so a file that never had one runs the same moves.
    """
    ALTER TABLE accounts ADD COLUMN public INTEGER NOT NULL DEFAULT 1;
    CREATE TABLE circles (
        id     INTEGER PRIMARY KEY,
        name   TEXT NOT NULL,
        kind   TEXT NOT NULL,
        parent INTEGER,
        at     TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE circle_members (
        circle     INTEGER NOT NULL,
        member     TEXT    NOT NULL,
        role       TEXT    NOT NULL CHECK (role IN ('admin', 'member')),
        status     TEXT    NOT NULL CHECK (status IN ('invited', 'joined')),
        invited_by TEXT    NOT NULL,
        at         TEXT    NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (circle, member)
    );
    CREATE INDEX ix_circle_members_member ON circle_members (member);
    CREATE TABLE IF NOT EXISTS teams (team TEXT NOT NULL, member TEXT NOT NULL);
    INSERT INTO circles (name, kind) SELECT DISTINCT team, 'team' FROM teams;
    INSERT INTO circle_members (circle, member, role, status, invited_by)
        SELECT id, name, 'admin', 'joined', name FROM circles;
    INSERT OR IGNORE INTO circle_members (circle, member, role, status, invited_by)
        SELECT c.id, t.member, 'member', 'invited', t.team FROM teams t JOIN circles c ON c.name = t.team;
    DROP TABLE teams;
    """,
    # Accounts are by username alone again: the two columns step 1 added go.
    "ALTER TABLE accounts DROP COLUMN pass; ALTER TABLE accounts DROP COLUMN key;",
    # Proof of owning an account (services/learner/tokens.py): the salted scrypt of its current recovery code,
    # NULL until claimed, and one row per logged-in device holding the SHA-256 of that device's token and the
    # day it was last used.
    # First, once: names typed before sign-up existed become accounts, so their owners can log in. This ran on
    # every connection before, so an answer filed just as its account was deleted brought the account back with
    # no proof of anyone's (docs/plans/2026-11-11-security.md §5). Guest records never become accounts.
    f"""
    INSERT OR IGNORE INTO accounts (name, at)
        SELECT user, MIN(at) FROM (SELECT user, at FROM attempts UNION ALL SELECT user, at FROM feedback)
        WHERE user NOT IN ('{GUEST}', '') AND user NOT LIKE '{DEVICE}%' GROUP BY user;
    ALTER TABLE accounts ADD COLUMN recovery TEXT;
    CREATE TABLE tokens (
        hash TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        at   TEXT NOT NULL DEFAULT (datetime('now')),
        used TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX ix_tokens_name ON tokens (name);
    """,
)


def connection() -> sqlite3.Connection:
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
        done = db.execute("PRAGMA user_version").fetchone()[0]
        for step, script in enumerate(MIGRATIONS[done:], start=done + 1):
            db.executescript(f"BEGIN; {script} PRAGMA user_version = {step}; COMMIT;")
        db.commit()
        _local.db = db
    return _local.db


def reset_connection() -> None:
    """Forget this thread's connection, so a test can point the setting elsewhere."""
    db = getattr(_local, "db", None)
    if db is not None:
        db.close()
    _local.db = None
