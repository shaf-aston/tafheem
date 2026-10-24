"""This thread's read-only connection to daleel.db, and whether the file is whole."""
from __future__ import annotations

import logging
import sqlite3

from backend.config import data_path
from backend.services.core.readonly_db import ReadOnlyDb

log = logging.getLogger(__name__)

# Reopened when a build replaces the file. A lambda so tests can point
# `data_path` at a fixture index.
db = ReadOnlyDb(lambda: data_path("daleel_index_path"))


def has_table(conn: sqlite3.Connection, name: str) -> bool:
    """Whether this index holds that table. Older ones hold fewer of them."""
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone())


def is_built() -> bool:
    """Whether the index is there and whole. The panel says so rather than
    showing nothing.

    An index built before `passage_meta` existed holds every passage but cannot
    answer a search, so it counts as not built. The half-minute mend is named
    in the log rather than on screen: the screen would be telling a reader to
    run a command about a table they have never heard of.
    """
    conn = db()
    if conn is None:
        return False
    if has_table(conn, "passage_meta"):
        return True

    log.warning("this index has no passage_meta table, so no search can run; "
                "run: python backend/scripts/daleel/build_daleel_index.py --meta")
    return False
