"""Usernames, the shelf the page keeps for each, and the global ranking. Making one, and proving it is
yours, is services/learner/tokens.py.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from backend.services.learner import attempts
from backend.services.learner.progress_db import connection


def has_account(name: str) -> bool:
    return connection().execute("SELECT 1 FROM accounts WHERE name = ?", (name,)).fetchone() is not None


def account(name: str) -> dict | None:
    """Who, since when (UTC ISO), how many answers given and whether in the global ranking; None when not signed up."""
    row = connection().execute(
        "SELECT name, at, public, (SELECT COUNT(*) FROM attempts WHERE user = name) AS answers "
        "FROM accounts WHERE name = ?", (name,)).fetchone()
    if row is None:
        return None
    joined = datetime.strptime(row["at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return {"name": row["name"], "joined": joined.isoformat(), "answers": row["answers"], "public": bool(row["public"])}


def shelf(user: str) -> dict[str, str]:
    """What the page last kept for this name; empty when nothing was."""
    row = connection().execute("SELECT data FROM saved WHERE user = ?", (user,)).fetchone()
    return json.loads(row["data"]) if row else {}


def keep_shelf(user: str, data: dict[str, str]) -> None:
    """Replace this name's shelf whole: the page always sends all of it."""
    db = connection()
    with db:
        db.execute(
            "INSERT INTO saved (user, data) VALUES (?, ?) "
            "ON CONFLICT (user) DO UPDATE SET data = excluded.data, at = datetime('now')",
            (user, json.dumps(data, ensure_ascii=False)),
        )


def account_names() -> list[str]:
    """Every username, A to Z."""
    return [row["name"] for row in connection().execute("SELECT name FROM accounts ORDER BY name")]


def leaderboard(module: str, user: str) -> tuple[list[dict], dict | None]:
    """The global ranking: accounts that show in it, and `user`'s own row, ranked among them even when hidden.

    An account from before tokens shows once it is claimed (services/learner/tokens.py): until then its name
    alone opens it, and a public list of such names is a list of accounts to take."""
    shown = [row["name"] for row in connection().execute(
        "SELECT name FROM accounts WHERE public = 1 AND recovery IS NOT NULL ORDER BY name")]
    ranked = attempts.ranked(shown if user in shown or not has_account(user) else [*shown, user], module)
    return [row for row in ranked if row["name"] in shown], next((row for row in ranked if row["name"] == user), None)


def set_public(user: str, public: bool) -> None:
    db = connection()
    with db:
        db.execute("UPDATE accounts SET public = ? WHERE name = ?", (int(public), user))
