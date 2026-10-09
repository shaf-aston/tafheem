"""Build the hadith database from what fetch_hadith_collections.py wrote.

    python backend/scripts/build_hadith_index.py

Reads collections.json and every <collection>.json beside it, and writes one
SQLite file: collections, their books, every hadith, and an FTS5 index over
the Arabic (hadith only, chain left out) and English text for search. Read-only at request time, like
daleel.db and quran/library.db beside it.

Rebuilding is safe at any time: it writes a fresh file beside the old one and
moves it into place at the end, so a run that fails leaves the working
database untouched rather than half-written.
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services import spelling  # noqa: E402
from backend.services.hadith import words  # noqa: E402
from backend.services.hadith.chain import chain_of  # noqa: E402
from backend.services.hadith.lemma import lemma  # noqa: E402

_SCHEMA = """
CREATE TABLE collection (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    short TEXT NOT NULL DEFAULT '',
    arabic TEXT NOT NULL DEFAULT '',
    arabic_short TEXT NOT NULL DEFAULT '',
    cite TEXT NOT NULL DEFAULT '',
    sahih INTEGER NOT NULL DEFAULT 0
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
    grades        TEXT NOT NULL DEFAULT '[]',  -- JSON list of {by, grade}
    PRIMARY KEY (collection_id, number, part)
);
CREATE INDEX hadith_by_book ON hadith (collection_id, book_number, number);

-- Arabic is indexed with its marks and spelling variants folded away, once as
-- written and once as each word's dictionary form (lemma, from CAMeL), and the
-- English stemmed, so a plain typed word finds the pointed or inflected one.
-- rowid ties a search hit straight back to its row in `hadith`.
CREATE VIRTUAL TABLE hadith_fts USING fts5(arabic, lemma, english, tokenize = 'porter unicode61');

-- Every distinct written word, lang ar or en, and n: how many hadiths hold it.
-- Repair reads n to prefer the commoner of two equally close words.
CREATE TABLE word (
    spelling TEXT NOT NULL,
    lang     TEXT NOT NULL,
    n        INTEGER NOT NULL,
    PRIMARY KEY (spelling, lang)
) WITHOUT ROWID;

-- Each word, and each word with one letter dropped, so a misspelling finds the
-- words one slip from it (or a doubled long vowel off) by plain lookup (services/spelling.py).
CREATE TABLE deletion (
    variant  TEXT NOT NULL,
    spelling TEXT NOT NULL,
    lang     TEXT NOT NULL
);
CREATE INDEX deletion_by_variant ON deletion (variant, lang);
"""


def _collections() -> dict:
    path = data_path("hadith_dir") / "collections.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if not key.startswith("_")}


def index_text(conn: sqlite3.Connection) -> None:
    """Fill hadith_fts, word and deletion from the hadith table. Shared with the tests' tiny database."""
    rows = conn.execute("SELECT rowid, arabic, english FROM hadith").fetchall()
    vocabulary: Counter[tuple[str, str]] = Counter()
    for rowid, arabic, english in rows:
        # Only the hadith, never its chain: a narrator's name is not what the hadith says.
        matn = chain_of(arabic).body
        folded = spelling.fold(matn)
        # Analysed as written, marks and all: the marks are what tell صَبْرَة the name from الصَّبْر.
        lemmas = " ".join(filter(None, (lemma(t) for t in words.ARABIC_TOKEN.findall(matn))))
        conn.execute("INSERT INTO hadith_fts (rowid, arabic, lemma, english) VALUES (?, ?, ?, ?)",
                     (rowid, folded, lemmas, english))
        vocabulary.update(("ar", w) for w in set(words.ARABIC_WORD.findall(folded)))
        vocabulary.update(("en", w) for w in set(words.ENGLISH_WORD.findall(english.lower())))
    conn.executemany("INSERT INTO word (spelling, lang, n) VALUES (?, ?, ?)",
                     [(w, lang, n) for (lang, w), n in vocabulary.items()])
    conn.executemany("INSERT INTO deletion (variant, spelling, lang) VALUES (?, ?, ?)",
                     ((v, w, lang) for lang, w in vocabulary for v in {w} | spelling.deletes(w)))


def build() -> dict[str, int]:
    target = data_path("hadith_index_path")
    scratch = target.with_suffix(".building.db")
    scratch.unlink(missing_ok=True)

    conn = sqlite3.connect(scratch)
    counts: dict[str, int] = {}
    try:
        conn.executescript(_SCHEMA)

        for key, meta in _collections().items():
            raw_path = data_path("hadith_dir") / f"{key}.json"
            if not raw_path.exists():
                print(f"  {key}: not fetched, skipped (run fetch_hadith_collections.py {key})")
                continue

            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO collection (id, name, short, arabic, arabic_short, cite, sahih) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (key, meta["name"], meta.get("short", meta["name"]), meta.get("arabic", ""), meta.get("arabic_short", ""),
                 meta.get("cite", ""), int(bool(meta.get("sahih")))),
            )
            conn.executemany(
                "INSERT INTO book (collection_id, number, name) VALUES (?, ?, ?)",
                [(key, b["number"], b["name"]) for b in raw.get("books", [])],
            )
            conn.executemany(
                "INSERT INTO hadith (collection_id, book_number, number, part, arabic, english, grades) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(key, h["book"], h["number"], h.get("part", ""), h["arabic"], h.get("english", ""),
                  json.dumps(h.get("grades", []), ensure_ascii=False))
                 for h in raw.get("hadith", [])],
            )
            counts[key] = len(raw.get("hadith", []))
            print(f"  {key}: {counts[key]:,} hadiths across {len(raw.get('books', [])):,} books")

        index_text(conn)
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
