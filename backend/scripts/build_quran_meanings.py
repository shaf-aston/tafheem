"""One-time harvest: the word-by-word meanings of the whole Qur'an, stored locally.

Run once:  python backend/scripts/build_quran_meanings.py
Dry run:   python backend/scripts/build_quran_meanings.py --dry-run

Why this exists
---------------
The grammar has always been offline, corpus.db answers in about a millisecond.
The English did not: it was fetched from api.quran.com one ayah at a time, which
costs ~1.2s the first time and ~220ms from the disk cache. Fine for one ayah,
useless for a surah, al-Baqarah would have meant 286 requests back to back.

So the English is built the same way the grammar already is: fetched once, kept
in its own small database, then read locally forever after. A whole surah becomes
two local queries.

It is a SEPARATE file from corpus.db on purpose. The grammar is the Quranic
Arabic Corpus (GNU GPL, tagged by hand); this is Quran.com's translation. Two
sources, two licences, two rebuild schedules; sources.json credits each one, and
keeping them apart is what lets either be rebuilt without touching the other.

Safe to re-run: it writes to a temporary file and swaps it in only once every
chapter has been fetched, so an interrupted run never leaves a half-built database
in place. --dry-run keeps that temporary file and never swaps, so a rebuild can be
diffed against the database in use before it replaces it.

More than one language
----------------------
Quran.com glosses each word in several languages, chosen by one query parameter,
so a second language is a second pass over the same words and lands in its own
column of the same row. LANGUAGES below is the list; adding to it also needs that
column in the schema, since a column per language is what keeps every existing
reader's `SELECT ... en FROM meaning` working untouched.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path
from typing import NamedTuple

import httpx

DATA_DIR = Path(__file__).parent.parent / "data" / "quran"
DATABASE = DATA_DIR / "meanings.db"

API = "https://api.quran.com/api/v4"
# Quran.com's own code for each language, which is also the column it fills.
# English first: the printed spelling and the ayah-end markers are taken from
# that pass, and the passes after it add nothing but their own column.
LANGUAGES = ("en", "ur")
# The API caps a page at 50 verses; al-Baqarah's 286 therefore take six.
PAGE_SIZE = 50
# Courtesy pause between requests. This is a free, unauthenticated API being
# asked for the whole Qur'an, there is no hurry.
PAUSE_SECONDS = 0.25
TIMEOUT_SECONDS = 30.0
RETRIES = 3

SCHEMA = """
CREATE TABLE meaning (
    surah INTEGER NOT NULL,
    ayah  INTEGER NOT NULL,
    word  INTEGER NOT NULL,   -- word number within the ayah, 1-based
    en    TEXT    NOT NULL,
    ur    TEXT,               -- NULL where Quran.com glosses the word in English only
    PRIMARY KEY (surah, ayah, word)
) WITHOUT ROWID;

-- The printed Uthmani spelling of each word, waqf (pause) marks included where
-- the mushaf carries one. Kept apart from `meaning`: a particle has no English
-- but still has printed text, so this table has a row wherever that one doesn't.
CREATE TABLE uthmani (
    surah INTEGER NOT NULL,
    ayah  INTEGER NOT NULL,
    word  INTEGER NOT NULL,
    ar    TEXT    NOT NULL,
    PRIMARY KEY (surah, ayah, word)
) WITHOUT ROWID;

-- The ayah-end marker api.quran.com prints as its own trailing "word": just the
-- ayah's number, in Arabic-Indic digits. The end-of-ayah ring (U+06DD) around it
-- is added where this is read, not stored, since it is punctuation, not data.
CREATE TABLE ayah_end (
    surah  INTEGER NOT NULL,
    ayah   INTEGER NOT NULL,
    number TEXT    NOT NULL,
    PRIMARY KEY (surah, ayah)
) WITHOUT ROWID;

CREATE TABLE surah (
    id      INTEGER PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    ayahs   INTEGER NOT NULL
);
"""


def _get(client: httpx.Client, path: str, **params) -> dict:
    """One API call, retried on the transient failures a long run will hit."""
    for attempt in range(1, RETRIES + 1):
        try:
            response = client.get(f"{API}{path}", params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            if attempt == RETRIES:
                raise
            wait = attempt * 2
            print(f"    {type(exc).__name__}, retrying in {wait}s ({attempt}/{RETRIES})")
            time.sleep(wait)
    raise AssertionError("unreachable")


def chapters(client: httpx.Client) -> list[dict]:
    payload = _get(client, "/chapters")
    return payload["chapters"]


class Harvest(NamedTuple):
    """The three tables one fetch fills, kept together because one word can add
    a row to two of them and splitting the walk would read the payload twice.

    `meanings` is keyed by position rather than being a flat list, because each
    language is a separate pass over the same words and they have to meet again
    on the word they both gloss.
    """

    meanings: dict[tuple[int, int, int], dict[str, str]]
    uthmani: list[tuple[int, int, int, str]]
    ends: list[tuple[int, int, str]]


def _ayah_of(verse: dict) -> int:
    """The ayah number out of "2:255". Zero when the key is missing or odd,
    which the caller stores as it finds it rather than guessing a number."""
    return int(str(verse.get("verse_key", "0:0")).partition(":")[2] or 0)


def read_verse(surah: int, verse: dict, into: Harvest, language: str, printed: bool) -> None:
    """One verse's words, added to the harvest.

    Pure: a dict in, rows appended, nothing fetched. This is where the shape of
    Quran.com's answer is understood, and having it apart from the paging is
    what lets it be checked against a saved payload instead of the network.

    A verse's "words" include the ayah-end marker; only real words are numbered
    against the corpus, so the marker goes to its own table and does not take a
    position.

    `printed` says whether to take the Arabic and the end marker from this pass
    as well. They are the same whichever language was asked for, so only the
    first pass collects them and the rest add their gloss to a word already seen.
    """
    ayah = _ayah_of(verse)
    position = 0
    for word in verse.get("words", []):
        kind = word.get("char_type_name")
        if kind == "end":
            if printed and (number := (word.get("text_uthmani") or word.get("text") or "").strip()):
                into.ends.append((surah, ayah, number))
            continue
        if kind != "word":
            continue
        position += 1
        if printed and (arabic := (word.get("text_uthmani") or "").strip()):
            into.uthmani.append((surah, ayah, position, arabic))
        if gloss := ((word.get("translation") or {}).get("text") or "").strip():
            into.meanings.setdefault((surah, ayah, position), {})[language] = gloss


def words_of(client: httpx.Client, surah: int) -> Harvest:
    """Every glossed word of one surah: its meaning in each language, the printed
    Uthmani spelling, and each ayah's end-marker number.

    One pass per language, because the API glosses a word in the one language
    asked for. Only the paging lives here; what a page means is read_verse's.
    """
    found = Harvest({}, [], [])
    for language in LANGUAGES:
        page = 1
        while True:
            payload = _get(
                client,
                f"/verses/by_chapter/{surah}",
                words="true",
                per_page=PAGE_SIZE,
                page=page,
                word_fields="text_uthmani",
                language=language,
            )
            for verse in payload.get("verses", []):
                read_verse(surah, verse, found, language, printed=language == LANGUAGES[0])

            if not (payload.get("pagination") or {}).get("next_page"):
                break
            page += 1
            time.sleep(PAUSE_SECONDS)
        time.sleep(PAUSE_SECONDS)
    return found


def meaning_rows(found: Harvest) -> tuple[list[tuple], int]:
    """The harvest's words as rows, and how many were dropped for having no
    English.

    A row needs its English: every reader of this table selects `en`, and a word
    the other languages gloss but English does not would have to be stored as an
    empty meaning, which reads as "means nothing" rather than "not recorded".
    The count is returned rather than swallowed so a run says how many it lost.
    """
    rows, dropped = [], 0
    for (surah, ayah, word), glosses in sorted(found.meanings.items()):
        if not glosses.get("en"):
            dropped += 1
            continue
        rows.append((surah, ayah, word, glosses["en"], glosses.get("ur")))
    return rows, dropped


def build(dry_run: bool = False) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    building = DATABASE.with_suffix(".building")
    building.unlink(missing_ok=True)

    db = sqlite3.connect(building)
    db.executescript(SCHEMA)

    with httpx.Client(headers={"Accept": "application/json"}) as client:
        listing = chapters(client)
        languages = ", ".join(LANGUAGES)
        print(f"Fetching the word-by-word {languages} of {len(listing)} surahs…")

        db.executemany(
            "INSERT INTO surah (id, name_en, name_ar, ayahs) VALUES (?, ?, ?, ?)",
            [
                (c["id"], c["name_simple"], c["name_arabic"], c["verses_count"])
                for c in listing
            ],
        )

        total = englishless = 0
        for chapter in listing:
            surah = chapter["id"]
            found = words_of(client, surah)
            rows, dropped = meaning_rows(found)
            db.executemany("INSERT OR REPLACE INTO meaning VALUES (?, ?, ?, ?, ?)", rows)
            db.executemany("INSERT OR REPLACE INTO uthmani VALUES (?, ?, ?, ?)", found.uthmani)
            db.executemany("INSERT OR REPLACE INTO ayah_end VALUES (?, ?, ?)", found.ends)
            db.commit()
            total += len(rows)
            englishless += dropped
            missing = sum(1 for row in rows if not row[4])
            print(
                f"  {surah:3}. {chapter['name_simple']:<24} {len(rows):>5} words"
                + (f"   {missing} with no Urdu" if missing else "")
            )
            time.sleep(PAUSE_SECONDS)

    db.execute("CREATE INDEX meaning_ayah ON meaning (surah, ayah)")
    db.execute("CREATE INDEX uthmani_ayah ON uthmani (surah, ayah)")
    db.commit()
    db.close()

    if englishless:
        print(f"\n{englishless} words were glossed in another language but not English, and were not stored.")

    if dry_run:
        print(f"\nDry run, {total:,} words. Left at {building}; {DATABASE} is untouched.")
        return

    # Swapped in only now, so an interrupted run leaves the old file untouched.
    building.replace(DATABASE)
    size_mb = DATABASE.stat().st_size / 1_000_000
    print(f"\nDone, {total:,} words in {DATABASE} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    try:
        build(dry_run="--dry-run" in sys.argv[1:])
    except KeyboardInterrupt:
        print("\nStopped. Nothing was replaced; re-run to start over.")
        sys.exit(1)
