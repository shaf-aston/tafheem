"""English readings of Maqayees entries, kept once they have been made.

Putting an entry into English costs a call to a model and gives roughly the same
answer every time, so it is worth doing once. This is where those answers live:
files beside the book, keyed by the root, read on startup and added to whenever
a new entry is read.

Two shapes of reading, two files, one machinery. The prose file holds the whole
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

# One writer at a time. Two readers pressing the button at once would otherwise
# each write the whole file from their own copy, and one would lose the other's.
_lock = threading.Lock()
_entries: dict[str, str] | None = None
_line_entries: dict[str, list[str]] | None = None


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
    worst it can cost is re-reading entries that had already been read, and the
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


def _loaded() -> dict[str, str]:
    global _entries
    if _entries is None:
        _entries = _read_store(STORE_FILE, _is_prose)
        logger.info("%d Maqayees entries already read into English", len(_entries))
    return _entries


def _loaded_lines() -> dict[str, list[str]]:
    global _line_entries
    if _line_entries is None:
        _line_entries = _read_store(LINES_FILE, _is_lines)
        logger.info("%d Maqayees entries already read line by line", len(_line_entries))
    return _line_entries


def get(root: str) -> str | None:
    """The prose English kept for this root, if it has been read before."""
    return _loaded().get(root) or None


def get_lines(root: str) -> list[str] | None:
    """The line-by-line English kept for this root, if it has been made."""
    return _loaded_lines().get(root) or None


def put(root: str, english: str) -> None:
    """Keep this prose reading, so the same entry is never read twice."""
    english = english.strip()
    if root and english:
        _keep(STORE_FILE, _loaded, _is_prose, root, english)


def put_lines(root: str, lines: list[str]) -> None:
    """Keep this line-by-line reading. A list that fails the shape check is
    dropped here rather than trusted later."""
    lines = [line.strip() for line in lines]
    if root and _is_lines(lines):
        _keep(LINES_FILE, _loaded_lines, _is_lines, root, lines)


def _keep(path: Path, loaded, keeps, root: str, value) -> None:
    """Write one reading into its store.

    Written to a neighbouring file and moved into place, so a crash midway
    leaves the old file whole rather than half a new one.
    """
    with _lock:
        cache = loaded()
        kept = dict(cache)
        kept[root] = value

        # The store only ever grows. Anything on disk that this process has not
        # seen was written by something else while it was running, so it is
        # carried over rather than overwritten, writing from a stale copy is
        # how 123 readings were once lost. What is in memory wins a clash,
        # because that is the newer reading of the same root.
        on_disk = _read_store(path, keeps)
        if unseen := set(on_disk) - set(kept):
            logger.warning(
                "%d readings in %s were written by something else, keeping them.",
                len(unseen), path,
            )
            kept = {**on_disk, **kept}

        scratch = path.with_suffix(".writing")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            scratch.write_text(
                json.dumps(kept, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8"
            )
            os.replace(scratch, path)
        except OSError as exc:
            # Losing the file costs time, never correctness; the reading is
            # still returned to whoever asked for it.
            logger.warning("Could not keep the English for %s (%s)", root, exc)
            scratch.unlink(missing_ok=True)
            return
        cache.update({root: value})


def count() -> int:
    """How many entries have been read into prose English so far."""
    return len(_loaded())
