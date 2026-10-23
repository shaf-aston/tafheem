"""The one way a service opens its SQLite file for reading.

SQLite connections cannot cross threads and FastAPI runs handlers on several, so
each thread gets its own read-only connection.

Reopened when the file changes: build scripts write a new file and move it into
place, and an open connection keeps reading the old one. Keyed on path and mtime,
one stat per call, so "rebuild, refresh the page" shows the new data, and a test
that points the module at another file gets a fresh connection without resetting
anything by hand.

`per_build` keeps something worked out from the file (its shape, say) for as
long as that connection stays open, which is the "until it is rebuilt" cache a
service would otherwise write by hand around `stamp()`.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Callable


class ReadOnlyDb:
    """Call it for this thread's connection, or None while the file is not built."""

    def __init__(self, path: Callable[[], Path]):
        # A function, not a Path: modules and tests reassign their DATABASE global.
        self._path = path
        self._local = threading.local()

    def stamp(self) -> tuple[str, int] | None:
        """Which build of the file is on disk (path and mtime), None while it is not built."""
        path = self._path()
        return (str(path), path.stat().st_mtime_ns) if path.exists() else None

    def __call__(self) -> sqlite3.Connection | None:
        if (stamp := self.stamp()) is None:
            return None
        path = stamp[0]
        local = self._local
        if getattr(local, "stamp", None) != stamp:
            if getattr(local, "db", None) is not None:
                local.db.close()
            local.db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
            local.db.row_factory = sqlite3.Row
            local.stamp = stamp
            local.memo = {}
        return local.db

    def per_build(self, conn: sqlite3.Connection | None, work: Callable[[sqlite3.Connection], object]):
        """`work(conn)`, worked out once per build of the file and kept until it is rebuilt.

        Kept beside the connection it was read from and dropped with it, so an
        answer about one build is never applied to the next. Any connection but
        this thread's own is answered afresh: a test's in-memory index, say.
        """
        local = self._local
        if conn is None or conn is not getattr(local, "db", None):
            return work(conn)
        if work not in local.memo:
            local.memo[work] = work(conn)
        return local.memo[work]
