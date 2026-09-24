"""The one way a service opens its SQLite file for reading.

SQLite connections cannot cross threads and FastAPI runs handlers on several, so
each thread gets its own read-only connection.

Reopened when the file changes: build scripts write a new file and move it into
place, and an open connection keeps reading the old one. Keyed on path and mtime,
one stat per call, so "rebuild, refresh the page" shows the new data, and a test
that points the module at another file gets a fresh connection without resetting
anything by hand.
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

    def __call__(self) -> sqlite3.Connection | None:
        path = self._path()
        if not path.exists():
            return None
        stamp = (str(path), path.stat().st_mtime_ns)
        local = self._local
        if getattr(local, "stamp", None) != stamp:
            if getattr(local, "db", None) is not None:
                local.db.close()
            local.db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
            local.db.row_factory = sqlite3.Row
            local.stamp = stamp
        return local.db
