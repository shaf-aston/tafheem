"""Build the hadith database from what fetch_hadith_collections.py wrote.

    python backend/scripts/build_hadith_index.py

Reads collections.json and every <collection>.json beside it, and writes one
SQLite file: collections, their books, every hadith, and an FTS5 index over
the Arabic and English text for search. Read-only at request time, like
daleel.db and quran/library.db beside it.

Rebuilding is safe at any time: it writes a fresh file beside the old one and
moves it into place at the end, so a run that fails leaves the working
database untouched rather than half-written.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above

_SCHEMA = """
CREATE TABLE collection (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cite TEXT NOT NULL DEFAULT ''
);

CREATE TABLE book (
    collection_id TEXT NOT NULL,
    number        INTEGER NOT NULL,
    name          TEXT NOT NULL,
    PRIMARY KEY (collection_id, number)
);

CREATE TABLE hadith (
    collection_id TEXT NOT NULL,
    book_number   INTEGER NOT NULL,
    number        INTEGER NOT NULL,
    part          TEXT NOT NULL DEFAULT '',
    arabic        TEXT NOT NULL,
    english       TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (collection_id, number, part)
);
CREATE INDEX hadith_by_book ON hadith (collection_id, book_number, number);

-- External content: the text stays in `hadith` alone, this only indexes it.
-- content_rowid ties a search hit straight back to its row.
CREATE VIRTUAL TABLE hadith_fts USING fts5(
    arabic, english,
    content = 'hadith', content_rowid = 'rowid'
);
"""


def _collections() -> dict:
    path = data_path("hadith_dir") / "collections.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if not key.startswith("_")}


def build() -> dict[str, int]:
    target = data_path("hadith_index_path")
    scratch = target.with_suffix(".building.db")
    scratch.unlink(missing_ok=True)

    conn = sqlite3.connect(scratch)
    counts: dict[str, int] = {}
    try:
        conn.executescript(_SCHEMA)

        for key, meta in sorted(_collections().items()):
            raw_path = data_path("hadith_dir") / f"{key}.json"
            if not raw_path.exists():
                print(f"  {key}: not fetched, skipped (run fetch_hadith_collections.py {key})")
                continue

            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO collection (id, name, cite) VALUES (?, ?, ?)",
                (key, meta["name"], meta.get("cite", "")),
            )
            conn.executemany(
                "INSERT INTO book (collection_id, number, name) VALUES (?, ?, ?)",
                [(key, b["number"], b["name"]) for b in raw.get("books", [])],
            )
            conn.executemany(
                "INSERT INTO hadith (collection_id, book_number, number, part, arabic, english) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [(key, h["book"], h["number"], h.get("part", ""), h["arabic"], h.get("english", ""))
                 for h in raw.get("hadith", [])],
            )
            counts[key] = len(raw.get("hadith", []))
            print(f"  {key}: {counts[key]:,} hadiths across {len(raw.get('books', [])):,} books")

        conn.execute("INSERT INTO hadith_fts (rowid, arabic, english) "
                      "SELECT rowid, arabic, english FROM hadith")
        conn.commit()
        conn.close()
    except Exception:
        conn.close()
        scratch.unlink(missing_ok=True)
        raise

    scratch.replace(target)
    return counts


def main() -> int:
    print("Building the hadith database")
    counts = build()
    if not counts:
        print("Nothing fetched yet. Run: python backend/scripts/fetch_hadith_collections.py")
        return 1
    print(f"\nTotal: {sum(counts.values()):,} hadiths from {len(counts)} collection(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
