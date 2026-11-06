"""Learner records, mid-split.
"""
from __future__ import annotations

import sqlite3

from backend.config import get_settings
from backend.services.learner import accounts, attempts, circle_rules
from backend.services.learner.progress_db import connection
from backend.services.learner.username import DEVICE, GUEST


def forget(user: str = GUEST) -> int:
    """Delete every answer this learner has given, in every module. Returns how many.

    Whole learner, not per module: the button that calls it says "clear it all",
    and a list of module names here would drift from the panels that file answers.
    """
    db = connection()
    with db:
        cursor = db.execute("DELETE FROM attempts WHERE user = ?", (user,))
        db.execute("DELETE FROM saved WHERE user = ?", (user,))
    return int(cursor.rowcount)


def delete_account(name: str) -> int:
    """Wipe the answers, the shelf, the circle places and the username, together. Returns how many answers went.

    Reports about questions are kept, as the plain wipe keeps them, but filed under
    nobody (''): under the guest they would pass to whoever signs up next.
    """
    db = connection()
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


def _circle(circle: int) -> sqlite3.Row:
    row = connection().execute("SELECT * FROM circles WHERE id = ?", (circle,)).fetchone()
    if row is None:
        raise LookupError("No such circle")
    return row


def _member(circle: int, name: str) -> sqlite3.Row | None:
    return connection().execute("SELECT * FROM circle_members WHERE circle = ? AND member = ?", (circle, name)).fetchone()


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
        parent = connection().execute("SELECT parent FROM circles WHERE id = ?", (parent,)).fetchone()["parent"]
    return found


def _others(circle: int, name: str) -> tuple[bool, bool]:
    """Whether anyone else is in the circle, and whether another joined admin is."""
    rows = connection().execute("SELECT member, role, status FROM circle_members WHERE circle = ? AND member != ?",
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
    db = connection()
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
    db = connection()
    with db:
        db.execute("UPDATE circles SET parent = ? WHERE id = ?", (parent, circle))


def my_circles(user: str) -> list[dict]:
    """Every circle `user` is in or invited to, the invites marked by status."""
    return [dict(row) for row in connection().execute(
        "SELECT c.id, c.name, c.kind, c.parent, m.role, m.status, m.invited_by FROM circle_members m "
        "JOIN circles c ON c.id = m.circle WHERE m.member = ? ORDER BY m.status DESC, c.name", (user,))]


def can_see(viewer: str, target: str) -> bool:
    """Whether `viewer` may open `target`'s full overview (the rule is circle_rules.can_see)."""
    mine = {row["circle"]: (row["role"], row["kind"]) for row in connection().execute(
        "SELECT m.circle, m.role, c.kind FROM circle_members m JOIN circles c ON c.id = m.circle "
        "WHERE m.member = ? AND m.status = 'joined'", (viewer,))}
    theirs = {row["circle"]: [row["circle"], *_above(row["circle"])] for row in connection().execute(
        "SELECT circle FROM circle_members WHERE member = ? AND status = 'joined'", (target,))}
    return circle_rules.can_see(viewer, target, mine, theirs, get_settings().circle_kinds)


def circle_detail(circle: int, user: str) -> dict:
    """One circle for a joined member (joined people only) or admin (invited people too), or for an admin of a
    circle above it (joined people only, and the circles inside it)."""
    found = _circle(circle)
    me = _member(circle, user)
    admin = _admin(circle, user)
    above = any(_admin(parent, user) for parent in _above(circle))
    if not (_joined(circle, user) or above):
        raise PermissionError("You are not in this circle")
    rows = connection().execute("SELECT member, role, status FROM circle_members WHERE circle = ? ORDER BY member", (circle,))
    members = [
        {"name": row["member"], "role": row["role"], "status": row["status"],
         "seeable": row["status"] == "joined" and can_see(user, row["member"])}
        for row in rows if admin or row["status"] == "joined"
    ]
    inside = [dict(row) for row in connection().execute(
        "SELECT id, name, kind FROM circles WHERE parent = ? ORDER BY name", (circle,))] if admin or above else []
    return {"id": found["id"], "name": found["name"], "kind": found["kind"], "parent": found["parent"],
            "role": me["role"] if me and me["status"] == "joined" else None, "members": members, "inside": inside}


def circle_ranking(circle: int, module: str, user: str) -> list[dict]:
    """The joined members of a circle by words learnt, for a joined member."""
    _circle(circle)
    if not _joined(circle, user):
        raise PermissionError("You are not in this circle")
    names = [row["member"] for row in connection().execute(
        "SELECT member FROM circle_members WHERE circle = ? AND status = 'joined' ORDER BY member", (circle,))]
    return attempts.ranked(names, module)


def member_overview(circle: int, viewer: str, member: str) -> dict:
    """A joined member's overview, if `viewer` may see it (can_see)."""
    _circle(circle)
    if not _joined(circle, member) or not can_see(viewer, member):
        raise PermissionError("You cannot see that member's progress")
    return attempts.overview(member)


def invite(circle: int, admin: str, member: str, role: str) -> None:
    _need_admin(circle, admin)
    if role not in circle_rules.ROLES:
        raise ValueError("A role is admin or member")
    if not accounts.has_account(member):
        raise LookupError("No account with that username")
    if _member(circle, member):
        raise ValueError(f"{member} is already in this circle or invited to it")
    db = connection()
    with db:
        db.execute("INSERT INTO circle_members (circle, member, role, status, invited_by) "
                   "VALUES (?, ?, ?, 'invited', ?)", (circle, member, role, admin))


def accept(circle: int, user: str) -> None:
    db = connection()
    with db:
        changed = db.execute("UPDATE circle_members SET status = 'joined' "
                             "WHERE circle = ? AND member = ? AND status = 'invited'", (circle, user)).rowcount
    if not changed:
        raise LookupError("No invite to accept")


def decline(circle: int, user: str) -> None:
    db = connection()
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
    db = connection()
    with db:
        db.execute("DELETE FROM circle_members WHERE circle = ? AND member = ?", (circle, user))
        if not others:
            _drop(db, circle)


def remove(circle: int, admin: str, member: str) -> None:
    _need_admin(circle, admin)
    if member == admin:
        raise ValueError("Use leave to go yourself")
    db = connection()
    with db:
        gone = db.execute("DELETE FROM circle_members WHERE circle = ? AND member = ?", (circle, member)).rowcount
    if not gone:
        raise LookupError("Not in this circle")


def set_role(circle: int, admin: str, member: str, role: str) -> None:
    _need_admin(circle, admin)
    if role not in circle_rules.ROLES:
        raise ValueError("A role is admin or member")
    if not _joined(circle, member):
        raise LookupError("Not a joined member of this circle")
    if member == admin and role != "admin" and not _others(circle, admin)[1]:
        raise ValueError("You are the only admin: make someone else an admin first")
    db = connection()
    with db:
        db.execute("UPDATE circle_members SET role = ? WHERE circle = ? AND member = ?", (role, circle, member))


def delete_circle(circle: int, admin: str) -> None:
    """End a circle; the circles inside it lose their parent."""
    _need_admin(circle, admin)
    db = connection()
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


def claim_guest(user: str, guest: str = GUEST) -> None:
    """Move one guest record's answers and reports (the signing-up device's) onto `user`."""
    db = connection()
    with db:
        db.execute("UPDATE attempts SET user = ? WHERE user = ?", (user, guest))
        db.execute("UPDATE feedback SET user = ? WHERE user = ?", (user, guest))


# Device records whose newest answer is older than the cut-off. A range, not LIKE, so the (user, …) index serves it:
# ";" is the character after ":", so this is every key that starts with DEVICE.
_IDLE_DEVICES = (f"SELECT user FROM attempts WHERE user >= '{DEVICE}' AND user < '{DEVICE[:-1]};' "
                 "GROUP BY user HAVING MAX(at) < datetime('now', ?)")


def sweep_guests(days: int) -> int:
    """Delete the answers of every device record not answered in for `days`; returns how many went.

    Nobody can come back for them once the device's id is gone, and a device still in use keeps all
    of it, its oldest answers too. Their reports are kept, under nobody (''), as delete_account
    keeps them; a device that only ever reported has no answers to sweep. Accounts and the shared
    GUEST record are never touched. Two statements in one write transaction, each choosing the idle
    devices itself, so an answer landing meanwhile waits for the lock and is never deleted with them.
    """
    db = connection()
    since = (f"-{days} days",)
    with db:
        db.execute(f"UPDATE feedback SET user = '' WHERE user IN ({_IDLE_DEVICES})", since)
        deleted = db.execute(f"DELETE FROM attempts WHERE user IN ({_IDLE_DEVICES})", since).rowcount
    return int(deleted)


def sweep() -> int:
    """`sweep_guests` at the configured age, for the startup step."""
    return sweep_guests(get_settings().progress_guest_days)
