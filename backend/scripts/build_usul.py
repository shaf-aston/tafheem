"""Build the weak-points database from rijal.db and the rule in usul.json.

    python backend/scripts/build_usul.py

Levels every narrator from his grade (services/usul/level.py), then keeps a
note for each place a narrator at or below `weak_from` is named in a chain.
Prints the narrators levelled, the notes per level and the wordings no term
took, so a grade the rule cannot read is seen and never guessed.

Rebuilding is safe at any time: it writes a fresh file beside the old one and
moves it into place at the end, like build_rijal.py. It stops, leaving the old
file, if the number of notes moves more than `max_change_ratio` against it.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services.usul.level import kind_of, level_of  # noqa: E402
from backend.services.usul.rule import rule  # noqa: E402

# Lists are JSON. A note is keyed by where its narrator's name starts in the hadith's Arabic.
_SCHEMA = """
CREATE TABLE narrator_level (
    narrator_id INTEGER PRIMARY KEY, level INTEGER NOT NULL, terms TEXT NOT NULL, kind TEXT NOT NULL, grade TEXT NOT NULL
);
CREATE TABLE note (
    collection TEXT NOT NULL, book INTEGER NOT NULL, number INTEGER NOT NULL, part TEXT NOT NULL,
    at INTEGER NOT NULL, narrator_id INTEGER NOT NULL, level INTEGER NOT NULL, kind TEXT NOT NULL,
    PRIMARY KEY (collection, book, number, part, at)
) WITHOUT ROWID;
CREATE TABLE gap (what TEXT NOT NULL, text TEXT NOT NULL, count INTEGER NOT NULL);
"""


def level_narrators(rijal: sqlite3.Connection, levels: list[dict]) -> tuple[dict[int, tuple[int, list[str], str, str]], Counter]:
    """({narrator id: (level, terms, kind, his grade)}, the wordings no term took by (what, text)).

    what is "left" for words beside a matched term and "none" for a grade with no match at all."""
    found: dict[int, tuple[int, list[str], str, str]] = {}
    gaps: Counter = Counter()
    for who, grade in rijal.execute("SELECT id, grade_ar FROM narrator WHERE grade_ar != ''"):
        level, matched, left = level_of(grade, levels)
        if level is None:
            gaps["none", grade] += 1
            continue
        found[who] = (level, matched, kind_of(level, matched, levels), grade)
        if left:
            gaps["left", left] += 1
    return found, gaps


def add_notes(conn: sqlite3.Connection, rijal: sqlite3.Connection, found: dict, weak_from: int) -> int:
    """One note per place a weak narrator is named; a mention placed twice at the same start is one note."""
    for collection, book, number, part, start, who in rijal.execute(
            "SELECT collection, book, number, part, start, narrator_id FROM mention ORDER BY collection, book, number, part, ord"):
        level, _, kind, _ = found.get(who, (0, None, None, None))
        if level >= weak_from:
            conn.execute("INSERT OR IGNORE INTO note VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (collection, book, number, part, start, who, level, kind))
    return conn.execute("SELECT COUNT(*) FROM note").fetchone()[0]


def build() -> None:
    source = data_path("rijal_index_path")
    if not source.exists():
        raise SystemExit(f"no {source.name}. Run: python backend/scripts/build_rijal.py")
    cfg = rule()
    target = data_path("usul_index_path")
    scratch = target.with_suffix(".building.db")
    scratch.unlink(missing_ok=True)
    rijal = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    conn = sqlite3.connect(scratch)
    try:
        conn.executescript(_SCHEMA)
        found, gaps = level_narrators(rijal, cfg["levels"])
        conn.executemany("INSERT INTO narrator_level VALUES (?, ?, ?, ?, ?)",
                         [(who, level, json.dumps(terms, ensure_ascii=False), kind, grade)
                          for who, (level, terms, kind, grade) in found.items()])
        conn.executemany("INSERT INTO gap VALUES (?, ?, ?)", [(what, text, n) for (what, text), n in gaps.items()])
        notes = add_notes(conn, rijal, found, cfg["weak_from"])
        if target.exists():
            before = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
            was = before.execute("SELECT COUNT(*) FROM note").fetchone()[0]
            before.close()
            if was and abs(notes - was) / was > cfg["max_change_ratio"]:
                raise SystemExit(f"notes went {was:,} to {notes:,}, more than {cfg['max_change_ratio']:.0%}. Old file kept; "
                                 "delete it to accept the new count.")
        per_level = conn.execute("SELECT level, COUNT(*) FROM note GROUP BY level ORDER BY level").fetchall()
        conn.commit()
    except BaseException:
        conn.close()
        scratch.unlink(missing_ok=True)
        raise
    finally:
        rijal.close()
    conn.close()
    scratch.replace(target)

    print(f"narrators levelled: {len(found):,}")
    print(f"notes: {notes:,}")
    for level, n in per_level:
        print(f"  level {level}: {n:,}")
    print("wordings no term took (narrators):")
    for (what, text), n in gaps.most_common(cfg["gap_print"]):
        print(f"  {n:>5}  {what:<4} {text}")
    print(f"  {len(gaps):,} wordings in all, in the gap table")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # the wordings are Arabic
    build()
