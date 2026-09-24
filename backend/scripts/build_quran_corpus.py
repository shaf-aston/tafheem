"""Build the Qur'anic grammar database from the Quranic Arabic Corpus.

Until now the Qur'an tab guessed each word's grammar by running a general-purpose
Arabic tagger over the text. That tagger was never taught Qur'anic spelling, so it
was wrong often enough to mislead. This replaces the guess with the corpus: every
word of the Qur'an tagged by hand, with its root, dictionary form, part of speech,
case and verb pattern.

    python backend/scripts/build_quran_corpus.py

Downloads the source once (about 6 MB) and writes backend/data/quran/corpus.db.
Both are gitignored, this script is how you get them back.

The source, its licence and how it was made live in data/sources.json beside every
other source the app cites, so the download and the credit never drift apart.
"""
from __future__ import annotations

import sqlite3
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services import provenance  # noqa: E402

DATA_DIR = Path(__file__).parent.parent / "data" / "quran"
RAW = DATA_DIR / "quran-morphology.txt"
DATABASE = DATA_DIR / "corpus.db"

SCHEMA = """
DROP TABLE IF EXISTS segment;
CREATE TABLE segment (
    surah    INTEGER NOT NULL,
    ayah     INTEGER NOT NULL,
    word     INTEGER NOT NULL,   -- word number within the ayah
    segment  INTEGER NOT NULL,   -- prefix / stem / suffix within the word
    form     TEXT    NOT NULL,   -- the letters as written
    pos      TEXT    NOT NULL,   -- N, V or P
    root     TEXT    NOT NULL DEFAULT '',
    lemma    TEXT    NOT NULL DEFAULT '',
    features TEXT    NOT NULL DEFAULT ''
);
"""

# Read after the rows are in: an index built on a full table is faster to make
# and better balanced than one maintained through 130,000 inserts.
INDEXES = """
CREATE INDEX segment_ayah ON segment (surah, ayah);
CREATE INDEX segment_root ON segment (root) WHERE root <> '';
CREATE INDEX segment_lemma ON segment (lemma) WHERE lemma <> '';
"""


def download(url: str) -> None:
    print(f"Downloading {url}")
    with urllib.request.urlopen(url, timeout=120) as response:
        RAW.write_bytes(response.read())
    print(f"Saved {RAW} ({RAW.stat().st_size / 1_000_000:.1f} MB)")


def parse(line: str) -> tuple | None:
    """One tab-separated row -> one segment, or None if the row is not one.

    A row looks like:  2:255:1:1  ٱللَّهُ  N  PN|ROOT:أله|LEM:اللَّه|NOM
    """
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3:
        return None

    location = parts[0].split(":")
    if len(location) != 4 or not location[0].isdigit():
        return None

    features = parts[3] if len(parts) > 3 else ""
    # ROOT and LEM are pulled into their own columns because everything in the
    # app hangs off them; the rest stays as written so no meaning is lost.
    root = lemma = ""
    keep = []
    for token in features.split("|"):
        if token.startswith("ROOT:"):
            root = token[5:]
        elif token.startswith("LEM:"):
            lemma = token[4:]
        elif token:
            keep.append(token)

    surah, ayah, word, segment = (int(number) for number in location)
    return (surah, ayah, word, segment, parts[1], parts[2], root, lemma, "|".join(keep))


def main() -> int:
    if not RAW.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        download(provenance.url_for("corpus"))

    rows = []
    skipped = 0
    for line in RAW.read_text(encoding="utf-8").splitlines():
        if row := parse(line):
            rows.append(row)
        elif line.strip():
            skipped += 1

    if not rows:
        print(f"No segments parsed from {RAW}. Delete it and re-run to download again.")
        return 1

    DATABASE.unlink(missing_ok=True)
    with sqlite3.connect(DATABASE) as db:
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO segment VALUES (?,?,?,?,?,?,?,?,?)", rows)
        db.executescript(INDEXES)
        ayat = db.execute("SELECT COUNT(DISTINCT surah || ':' || ayah) FROM segment").fetchone()[0]
        roots = db.execute("SELECT COUNT(DISTINCT root) FROM segment WHERE root <> ''").fetchone()[0]

    print(f"{len(rows)} segments, {ayat} ayat, {roots} roots ({skipped} rows skipped).")
    print(f"Wrote {DATABASE} ({DATABASE.stat().st_size / 1_000_000:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
