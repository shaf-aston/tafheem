"""Whole-learner moves and wipes: forget, delete an account, hand a device's guest record to a new
account, sweep idle devices.
"""
from __future__ import annotations


from backend.config import get_settings
from backend.services.learner import circles
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
            circles.tidy(db, circle)
        db.execute("DELETE FROM accounts WHERE name = ?", (name,))
    return int(deleted)


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
