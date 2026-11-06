"""The one way a build script writes a file the app reads (the write side of `ReadOnlyDb`).

Build in a scratch file beside the target and move it over the target only when
the build ends clean, so a run that fails or is stopped leaves the old file whole
and no scratch behind.

`guard=(ratio, tables)` also refuses a build whose row count in any of those
SQLite tables moved by more than `ratio` against the file it would replace, so a
broken rule cannot ship quietly. `dry_run` runs the same build and keeps the scratch file for
inspection instead of replacing the target.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator


def _count(path: Path, table: str) -> int:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:   # a file built before this table existed
        return 0
    finally:
        conn.close()


def _refuse_big_change(target: Path, scratch: Path, ratio: float, tables: Iterable[str]) -> None:
    if not target.exists():
        return
    for table in tables:
        was, now = _count(target, table), _count(scratch, table)
        if was and abs(now - was) / was > ratio:
            raise SystemExit(f"{table} rows went {was:,} to {now:,}, more than {ratio:.0%}. Old file kept; "
                             "delete it to accept the new count.")


@contextmanager
def building(target: Path, *, guard: tuple[float, Iterable[str]] | None = None, dry_run: bool = False) -> Iterator[Path]:
    """Yield the scratch path to write; close any connection to it before the block ends."""
    scratch = target.with_name(target.name + ".building")
    target.parent.mkdir(parents=True, exist_ok=True)
    scratch.unlink(missing_ok=True)
    try:
        yield scratch
        if guard:
            _refuse_big_change(target, scratch, *guard)
        if not dry_run:
            scratch.replace(target)
    except BaseException:
        scratch.unlink(missing_ok=True)
        raise
