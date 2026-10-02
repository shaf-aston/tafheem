"""The English of Maqayees entries, kept once they have been made.

Putting an entry into English costs a call to a model and gives roughly the same
answer every time, so it is worth doing once. This is where those answers live:
files beside the book, keyed by the root, re-read whenever another process has
added to them.

Two shapes of English, two files, one machinery. The prose file holds the whole
entry retold as paragraphs; the lines file holds it as a list, one English line
per Arabic line, for the view that prints them interleaved. They are separate
files because a reader with one is not owed the other, and mixing shapes in one
file would make every reader check which it got.

Two things fill the prose store. A reader pressing the button fills one root.
The backfill script fills the rest, and can be stopped and started because it
skips whatever is already here. The lines store is filled only by readers
asking. Either way an entry is only ever put into English once per shape.

These are caches, not sources: deleting a file loses nothing but the time it
took to make. The book itself is untouched by any of this.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA = Path(__file__).parent.parent / "data" / "maqayees"
STORE_FILE = _DATA / "english_entries.json"
LINES_FILE = _DATA / "english_lines.json"
# What readers' presses add on the server. Apart from LINES_FILE because a
# deploy copies every tracked file over the server's copy, which erased them;
# this one is untracked, so a deploy never touches it.
LINES_KEPT_FILE = _DATA / "english_lines.kept.json"

# One writer at a time within a process. Two backend copies share these files
# too; a write from each at the same instant can lose one root, which costs
# only a remake the next time it is asked for.
_lock = threading.Lock()
# First file -> (every file's change time when read, their merged entries).
# Checked on each read, so one backend copy sees what the other kept.
_cache: dict[Path, tuple[tuple, dict]] = {}


def _is_prose(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_lines(value: object) -> bool:
    """A list of lines, every one a real line. One bad line spoils the list:
    kept, it would sit under the wrong Arabic, which is worse than absent."""
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(line, str) and line.strip() for line in value)
    )


def _read_store(path: Path, keeps) -> dict:
    """The file as it stands, or an empty store if there isn't one yet.

    An unreadable file is a warning and an empty store, never a failure: the
    worst it can cost is making English that had already been made, and the
    card it feeds has a book to show either way.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        logger.warning("Could not read %s (%s), starting with none kept.", path, exc)
        return {}
    if not isinstance(raw, dict):
        logger.warning("%s is not a set of roots, starting with none kept.", path)
        return {}
    return {k: v for k, v in raw.items() if isinstance(k, str) and keeps(v)}


def _changed_at(path: Path) -> int | None:
    try:
        return path.stat().st_mtime_ns
    except FileNotFoundError:
        return None


def _store(paths: tuple[Path, ...], keeps) -> dict:
    """Every file's entries, the first file winning a clash; re-read only when one changed."""
    stamp = tuple(_changed_at(path) for path in paths)
    hit = _cache.get(paths[0])
    if hit is None or hit[0] != stamp:
        merged: dict = {}
        for path in reversed(paths):
            merged.update(_read_store(path, keeps))
        logger.info("%d Maqayees entries in English in %s", len(merged), paths[0].name)
        hit = _cache[paths[0]] = (stamp, merged)
    return hit[1]


def _prose() -> dict[str, str]:
    return _store((STORE_FILE,), _is_prose)


def _lines() -> dict[str, list[str]]:
    # The shipped file wins: it is the whole-book run, made against the book as
    # it now stands.
    return _store((LINES_FILE, LINES_KEPT_FILE), _is_lines)


def get(root: str) -> str | None:
    """The prose English kept for this root, if it has been made."""
    return _prose().get(root) or None


def get_lines(root: str) -> list[str] | None:
    """The line-by-line English kept for this root, if it has been made."""
    return _lines().get(root) or None


def put(root: str, english: str) -> None:
    """Keep this prose English. Only the backfill script makes it, so it goes
    into the shipped file."""
    english = english.strip()
    if root and english:
        _keep(STORE_FILE, _is_prose, root, english)


def put_lines(root: str, lines: list[str]) -> None:
    """Keep this line-by-line English. A list that fails the shape check is
    dropped here rather than trusted later."""
    lines = [line.strip() for line in lines]
    if root and _is_lines(lines):
        _keep(LINES_KEPT_FILE, _is_lines, root, lines)


def _keep(path: Path, keeps, root: str, value) -> None:
    """Add one root to a file.

    Added to the file as it stands on disk, never to a copy in memory: writing
    from a stale copy is how 123 entries' English was once lost. Written to a
    neighbouring file and moved into place, so a crash midway leaves the old
    file whole rather than half a new one.
    """
    with _lock:
        kept = _read_store(path, keeps)
        kept[root] = value
        scratch = path.with_suffix(f".{os.getpid()}.writing")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            scratch.write_text(
                json.dumps(kept, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8"
            )
            os.replace(scratch, path)
        except OSError as exc:
            # Losing the file costs time, never correctness; the English is
            # still returned to whoever asked for it.
            logger.warning("Could not keep the English for %s (%s)", root, exc)
            scratch.unlink(missing_ok=True)


def count() -> int:
    """How many entries have prose English so far."""
    return len(_prose())
