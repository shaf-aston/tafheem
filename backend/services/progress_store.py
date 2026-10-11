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

`user` is the learner's username (services/profile.py), or 'local' for answers
given before names existed. The questions table is a cache of AI answers shared
by everyone, so it stays under 'local' and claim_local leaves it alone.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone

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
-- Names typed before sign-up existed are accounts already, so their owners can log in.
INSERT OR IGNORE INTO accounts (name, at)
    SELECT user, MIN(at) FROM (SELECT user, at FROM attempts UNION ALL SELECT user, at FROM feedback)
    WHERE user NOT IN ('local', '') GROUP BY user;
"""

# Changes to tables that already exist, in order; PRAGMA user_version counts how many ran.
# Append only: a step that has run on a learner's file never runs again.
MIGRATIONS = (
    # Passphrase as "iterations$salt$hash" and the sign-in key's SHA-256; NULL until the first sign-in.
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
)

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

_DAYS = "SELECT DISTINCT date(at) AS day FROM attempts WHERE user = ? ORDER BY day DESC"

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
        db.execute("DELETE FROM saved WHERE user = ?", (user,))
    return int(cursor.rowcount)


def _hash_pass(passphrase: str, salt: bytes, iterations: int) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, iterations)
    return f"{iterations}${salt.hex()}${digest.hex()}"


def _pass_matches(passphrase: str, stored: str) -> bool:
    iterations, salt, _ = stored.split("$")
    return hmac.compare_digest(_hash_pass(passphrase, bytes.fromhex(salt), int(iterations)), stored)


def _key_hash(key: str) -> str:
    # The key is random, so one SHA-256 is enough; a database leak still hands out no key.
    return hashlib.sha256(key.encode()).hexdigest()


def _new_key(db: sqlite3.Connection, name: str) -> str:
    """A fresh sign-in key for `name`; the one before it stops working."""
    key = secrets.token_urlsafe(get_settings().signin_key_bytes)
    db.execute("UPDATE accounts SET key = ? WHERE name = ?", (_key_hash(key), name))
    return key


def _new_pass(passphrase: str) -> str:
    settings = get_settings()
    return _hash_pass(passphrase, secrets.token_bytes(settings.passphrase_salt_bytes), settings.passphrase_iterations)


def sign_up(name: str, passphrase: str) -> str | None:
    """Make the account with its passphrase. Its sign-in key, or None when the username is taken."""
    db = _db()
    with db:
        if db.execute("INSERT OR IGNORE INTO accounts (name, pass) VALUES (?, ?)",
                      (name, _new_pass(passphrase))).rowcount == 0:
            return None
        return _new_key(db, name)


def sign_in(name: str, passphrase: str) -> str | None:
    """A new sign-in key, or None for a wrong passphrase. An account with none yet takes this one."""
    db = _db()
    stored = lambda: db.execute("SELECT pass FROM accounts WHERE name = ?", (name,)).fetchone()  # noqa: E731
    with db:
        row = stored()
        if row is not None and row["pass"] is None:
            # Re-read after: when two first sign-ins race, both are checked against the winner.
            db.execute("UPDATE accounts SET pass = ? WHERE name = ? AND pass IS NULL", (_new_pass(passphrase), name))
            row = stored()
        if row is None or not _pass_matches(passphrase, row["pass"]):
            return None
        return _new_key(db, name)


def signed_in(name: str, key: str | None) -> bool:
    """Whether `key` is this account's current sign-in key."""
    row = _db().execute("SELECT key FROM accounts WHERE name = ?", (name,)).fetchone()
    return bool(key and row and row["key"]) and hmac.compare_digest(row["key"], _key_hash(key))


def has_account(name: str) -> bool:
    return _db().execute("SELECT 1 FROM accounts WHERE name = ?", (name,)).fetchone() is not None


def account(name: str) -> dict | None:
    """Who, since when (UTC ISO), how many answers given and whether in the global ranking; None when not signed up."""
    row = _db().execute(
        "SELECT name, at, public, (SELECT COUNT(*) FROM attempts WHERE user = name) AS answers "
        "FROM accounts WHERE name = ?", (name,)).fetchone()
    if row is None:
        return None
    joined = datetime.strptime(row["at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return {"name": row["name"], "joined": joined.isoformat(), "answers": row["answers"], "public": bool(row["public"])}


def delete_account(name: str) -> int:
    """Wipe the answers, the shelf, the circle places and the username, together. Returns how many answers went.

    Reports about questions are kept, as the plain wipe keeps them, but filed under
    nobody (''): under the guest they would pass to whoever signs up next.
    """
    db = _db()
    with db:
        deleted = db.execute("DELETE FROM attempts WHERE user = ?", (name,)).rowcount
        db.execute("UPDATE feedback SET user = '' WHERE user = ?", (name,))
        db.execute("DELETE FROM saved WHERE user = ?", (name,))
        affected = [row["circle"] for row in db.execute("SELECT circle FROM circle_members WHERE member = ?", (name,))]
        db.execute("DELETE FROM circle_members WHERE member = ?", (name,))
        for circle in affected:
            _tidy(db, circle)
        db.execute("DELETE FROM accounts WHERE name = ?", (name,))
    return int(deleted)


def shelf(user: str) -> dict[str, str]:
    """What the page last kept for this name; empty when nothing was."""
    row = _db().execute("SELECT data FROM saved WHERE user = ?", (user,)).fetchone()
    return json.loads(row["data"]) if row else {}


def keep_shelf(user: str, data: dict[str, str]) -> None:
    """Replace this name's shelf whole: the page always sends all of it."""
    db = _db()
    with db:
        db.execute(
            "INSERT INTO saved (user, data) VALUES (?, ?) "
            "ON CONFLICT (user) DO UPDATE SET data = excluded.data, at = datetime('now')",
            (user, json.dumps(data, ensure_ascii=False)),
        )


def account_names() -> list[str]:
    """Every username, A to Z."""
    return [row["name"] for row in _db().execute("SELECT name FROM accounts ORDER BY name")]


def learnt(module: str, name: str) -> int:
    """How many items this name has learnt in `module`: the leaderboard's measure."""
    return sum(row["known"] for row in summary(module, name))


def overview(user: str) -> dict:
    """Every module this learner answered in, the totals, and the streak of days.

    Learnt is the leaderboard's own measure, so the two never disagree.
    """
    modules = [
        {**dict(row), "learnt": learnt(row["module"], user),
         "last_at": datetime.fromisoformat(row["last_at"]).replace(tzinfo=timezone.utc).isoformat()}
        for row in _db().execute(_MODULES, (user,))
    ]
    totals = {key: sum(row[key] for row in modules) for key in ("attempts", "correct", "learnt")}
    days = [datetime.fromisoformat(row["day"]).date() for row in _db().execute(_DAYS, (user,))]
    return {"modules": modules, **totals, "streak": _streak(days, datetime.now(timezone.utc).date())}


def _streak(days: list, today) -> int:
    """Days in a row with an answer, newest first in `days` (UTC). Today counts;
    a day not yet answered in leaves yesterday's streak standing."""
    day = today if days and days[0] == today else today - timedelta(days=1)
    streak = 0
    for answered in days:
        if answered != day:
            break
        streak += 1
        day -= timedelta(days=1)
    return streak


def _answers(module: str, name: str) -> int:
    return _db().execute("SELECT COUNT(*) FROM attempts WHERE user = ? AND module = ?", (name, module)).fetchone()[0]


def _ranked(names: list[str], module: str) -> list[dict]:
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


def leaderboard(module: str, user: str) -> tuple[list[dict], dict | None]:
    """The global ranking: accounts that show in it, and `user`'s own row, ranked among them even when hidden."""
    shown = [row["name"] for row in _db().execute("SELECT name FROM accounts WHERE public = 1 ORDER BY name")]
    ranked = _ranked(shown if user in shown or not has_account(user) else [*shown, user], module)
    return [row for row in ranked if row["name"] in shown], next((row for row in ranked if row["name"] == user), None)


def set_public(user: str, public: bool) -> None:
    db = _db()
    with db:
        db.execute("UPDATE accounts SET public = ? WHERE name = ?", (int(public), user))


# Circles: people grouped by kind (config circle_kinds), nestable. A member is invited first and sees
# nothing until they accept; an invited row shows only to admins and to the invited person.

ROLES = ("admin", "member")


def _circle(circle: int) -> sqlite3.Row:
    row = _db().execute("SELECT * FROM circles WHERE id = ?", (circle,)).fetchone()
    if row is None:
        raise LookupError("No such circle")
    return row


def _member(circle: int, name: str) -> sqlite3.Row | None:
    return _db().execute("SELECT * FROM circle_members WHERE circle = ? AND member = ?", (circle, name)).fetchone()


def _joined(circle: int, name: str) -> bool:
    row = _member(circle, name)
    return bool(row and row["status"] == "joined")


def _admin(circle: int, name: str) -> bool:
    row = _member(circle, name)
    return bool(row and row["status"] == "joined" and row["role"] == "admin")


def _need_admin(circle: int, name: str) -> None:
    _circle(circle)
    if not _admin(circle, name):
        raise PermissionError("Only an admin of this circle can do that")


def _above(circle: int) -> list[int]:
    """The circles this one sits inside, nearest first; a bad row cannot make it loop."""
    found: list[int] = []
    parent = _circle(circle)["parent"]
    while parent is not None and parent not in found:
        found.append(parent)
        parent = _db().execute("SELECT parent FROM circles WHERE id = ?", (parent,)).fetchone()["parent"]
    return found


def _others(circle: int, name: str) -> tuple[bool, bool]:
    """Whether anyone else is in the circle, and whether another joined admin is."""
    rows = _db().execute("SELECT member, role, status FROM circle_members WHERE circle = ? AND member != ?",
                         (circle, name)).fetchall()
    return bool(rows), any(r["role"] == "admin" and r["status"] == "joined" for r in rows)


def _drop(db: sqlite3.Connection, circle: int) -> None:
    db.execute("UPDATE circles SET parent = NULL WHERE parent = ?", (circle,))
    db.execute("DELETE FROM circle_members WHERE circle = ?", (circle,))
    db.execute("DELETE FROM circles WHERE id = ?", (circle,))


def circle_kinds() -> list[str]:
    return list(get_settings().circle_kinds)


def create_circle(user: str, name: str, kind: str, parent: int | None = None) -> int:
    """Make a circle with `user` as its joined admin. A parent needs `user` to be its admin."""
    name = name.strip()
    if not name or len(name) > get_settings().circle_name_max:
        raise ValueError(f"A circle name is 1 to {get_settings().circle_name_max} characters")
    if kind not in get_settings().circle_kinds:
        raise ValueError(f"Kind must be one of: {', '.join(circle_kinds())}")
    if parent is not None:
        _need_admin(parent, user)
    db = _db()
    with db:
        made = db.execute("INSERT INTO circles (name, kind, parent) VALUES (?, ?, ?)", (name, kind, parent)).lastrowid
        db.execute("INSERT INTO circle_members (circle, member, role, status, invited_by) "
                   "VALUES (?, ?, 'admin', 'joined', ?)", (made, user, user))
    return int(made)


def move_circle(circle: int, admin: str, parent: int | None) -> None:
    """Put a circle inside another (None: on its own). Needs admin of both; never inside itself or what it holds."""
    _need_admin(circle, admin)
    if parent is not None:
        _need_admin(parent, admin)
        if parent == circle or circle in _above(parent):
            raise ValueError("A circle cannot go inside itself or a circle inside it")
    db = _db()
    with db:
        db.execute("UPDATE circles SET parent = ? WHERE id = ?", (parent, circle))


def my_circles(user: str) -> list[dict]:
    """Every circle `user` is in or invited to, the invites marked by status."""
    return [dict(row) for row in _db().execute(
        "SELECT c.id, c.name, c.kind, c.parent, m.role, m.status, m.invited_by FROM circle_members m "
        "JOIN circles c ON c.id = m.circle WHERE m.member = ? ORDER BY m.status DESC, c.name", (user,))]


def can_see(viewer: str, target: str) -> bool:
    """Whether `viewer` may open `target`'s full overview: themselves; an admin of a circle `target` is joined
    in or of any circle above it; or a fellow member of a circle whose kind shows members' details."""
    if viewer == target:
        return True
    kinds = get_settings().circle_kinds
    mine = {row["circle"]: row for row in _db().execute(
        "SELECT m.circle, m.role, c.kind FROM circle_members m JOIN circles c ON c.id = m.circle "
        "WHERE m.member = ? AND m.status = 'joined'", (viewer,))}
    for row in _db().execute("SELECT circle FROM circle_members WHERE member = ? AND status = 'joined'", (target,)):
        if any(c in mine and mine[c]["role"] == "admin" for c in (row["circle"], *_above(row["circle"]))):
            return True
        if row["circle"] in mine and kinds.get(mine[row["circle"]]["kind"]):
            return True
    return False


def circle_detail(circle: int, user: str) -> dict:
    """One circle for a joined member (joined people only) or admin (invited people too), or for an admin of a
    circle above it (joined people only, and the circles inside it)."""
    found = _circle(circle)
    me = _member(circle, user)
    admin = _admin(circle, user)
    above = any(_admin(parent, user) for parent in _above(circle))
    if not (_joined(circle, user) or above):
        raise PermissionError("You are not in this circle")
    rows = _db().execute("SELECT member, role, status FROM circle_members WHERE circle = ? ORDER BY member", (circle,))
    members = [
        {"name": row["member"], "role": row["role"], "status": row["status"],
         "seeable": row["status"] == "joined" and can_see(user, row["member"])}
        for row in rows if admin or row["status"] == "joined"
    ]
    inside = [dict(row) for row in _db().execute(
        "SELECT id, name, kind FROM circles WHERE parent = ? ORDER BY name", (circle,))] if admin or above else []
    return {"id": found["id"], "name": found["name"], "kind": found["kind"], "parent": found["parent"],
            "role": me["role"] if me and me["status"] == "joined" else None, "members": members, "inside": inside}


def circle_ranking(circle: int, module: str, user: str) -> list[dict]:
    """The joined members of a circle by words learnt, for a joined member."""
    _circle(circle)
    if not _joined(circle, user):
        raise PermissionError("You are not in this circle")
    names = [row["member"] for row in _db().execute(
        "SELECT member FROM circle_members WHERE circle = ? AND status = 'joined' ORDER BY member", (circle,))]
    return _ranked(names, module)


def member_overview(circle: int, viewer: str, member: str) -> dict:
    """A joined member's overview, if `viewer` may see it (can_see)."""
    _circle(circle)
    if not _joined(circle, member) or not can_see(viewer, member):
        raise PermissionError("You cannot see that member's progress")
    return overview(member)


def invite(circle: int, admin: str, member: str, role: str) -> None:
    _need_admin(circle, admin)
    if role not in ROLES:
        raise ValueError("A role is admin or member")
    if not has_account(member):
        raise LookupError("No account with that username")
    if _member(circle, member):
        raise ValueError(f"{member} is already in this circle or invited to it")
    db = _db()
    with db:
        db.execute("INSERT INTO circle_members (circle, member, role, status, invited_by) "
                   "VALUES (?, ?, ?, 'invited', ?)", (circle, member, role, admin))


def accept(circle: int, user: str) -> None:
    db = _db()
    with db:
        changed = db.execute("UPDATE circle_members SET status = 'joined' "
                             "WHERE circle = ? AND member = ? AND status = 'invited'", (circle, user)).rowcount
    if not changed:
        raise LookupError("No invite to accept")


def decline(circle: int, user: str) -> None:
    db = _db()
    with db:
        changed = db.execute("DELETE FROM circle_members WHERE circle = ? AND member = ? AND status = 'invited'",
                             (circle, user)).rowcount
    if not changed:
        raise LookupError("No invite to decline")


def leave(circle: int, user: str) -> None:
    """Leave a circle. The last admin may not while anyone else is in it; alone, leaving ends the circle."""
    _circle(circle)
    if not _joined(circle, user):
        raise LookupError("You are not in this circle")
    others, other_admin = _others(circle, user)
    if _admin(circle, user) and others and not other_admin:
        raise ValueError("You are the only admin: make someone else an admin first")
    db = _db()
    with db:
        db.execute("DELETE FROM circle_members WHERE circle = ? AND member = ?", (circle, user))
        if not others:
            _drop(db, circle)


def remove(circle: int, admin: str, member: str) -> None:
    _need_admin(circle, admin)
    if member == admin:
        raise ValueError("Use leave to go yourself")
    db = _db()
    with db:
        gone = db.execute("DELETE FROM circle_members WHERE circle = ? AND member = ?", (circle, member)).rowcount
    if not gone:
        raise LookupError("Not in this circle")


def set_role(circle: int, admin: str, member: str, role: str) -> None:
    _need_admin(circle, admin)
    if role not in ROLES:
        raise ValueError("A role is admin or member")
    if not _joined(circle, member):
        raise LookupError("Not a joined member of this circle")
    if member == admin and role != "admin" and not _others(circle, admin)[1]:
        raise ValueError("You are the only admin: make someone else an admin first")
    db = _db()
    with db:
        db.execute("UPDATE circle_members SET role = ? WHERE circle = ? AND member = ?", (role, circle, member))


def delete_circle(circle: int, admin: str) -> None:
    """End a circle; the circles inside it lose their parent."""
    _need_admin(circle, admin)
    db = _db()
    with db:
        _drop(db, circle)


def _tidy(db: sqlite3.Connection, circle: int) -> None:
    """After someone goes, a circle with no admin hands it to its longest-joined member, or ends if empty."""
    if db.execute("SELECT 1 FROM circle_members WHERE circle = ? AND role = 'admin' AND status = 'joined'",
                  (circle,)).fetchone():
        return
    heir = db.execute("SELECT member FROM circle_members WHERE circle = ? AND status = 'joined' "
                      "ORDER BY at, member LIMIT 1", (circle,)).fetchone()
    if heir:
        db.execute("UPDATE circle_members SET role = 'admin' WHERE circle = ? AND member = ?", (circle, heir["member"]))
    else:
        _drop(db, circle)


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
