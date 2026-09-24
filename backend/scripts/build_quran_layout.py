"""One-time harvest: which printed page each ayah falls on, stored locally.

Run once:  python backend/scripts/build_quran_layout.py

Why this exists
---------------
Memorise deals a "page" by counting words, about 135 of them, because nothing
on this machine recorded where a real mushaf breaks. That is an estimate, and it
drifts: a page of long ayahs and a page of short ones are the same size in words
and different sizes on paper.

A page break is a fact about one printing, so it has to be fetched from something
that knows that printing. The 604-page Madani mushaf is the one this app already
renders, and Quran.com publishes the page number of every ayah in it. Fetched
once here, kept in its own small database, read locally forever after.

It is a SEPARATE file from meanings.db and corpus.db on purpose, for the same
reason those two are separate from each other: one source, one licence, one
rebuild schedule each. quran_layout.py is the only module that opens it.

Safe to re-run: writes to a temporary file and swaps it in only once all 114
chapters are through, so an interrupted run never leaves a half-built database.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent.parent / "data" / "quran"
DATABASE = DATA_DIR / "layout.db"

API = "https://api.quran.com/api/v4"
# The API caps a page of results at 50 verses; al-Baqarah's 286 take six calls.
PAGE_SIZE = 50
PAUSE_SECONDS = 0.25
TIMEOUT_SECONDS = 30.0
RETRIES = 3

# The 604-page Madani printing. Quran.com serves page_number in this numbering
# by default; naming it here is what makes the database's meaning checkable.
MUSHAF = "Madani, 604 pages, 15 lines"
TOTAL_PAGES = 604

SCHEMA = """
CREATE TABLE page (
    surah INTEGER NOT NULL,
    ayah  INTEGER NOT NULL,
    page  INTEGER NOT NULL,   -- 1..604, the printed page the ayah begins on
    PRIMARY KEY (surah, ayah)
) WITHOUT ROWID;
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


def pages_of(client: httpx.Client, surah: int) -> list[tuple[int, int, int]]:
    """Every ayah of one surah as (surah, ayah, page)."""
    rows: list[tuple[int, int, int]] = []
    page = 1
    while True:
        payload = _get(
            client,
            f"/verses/by_chapter/{surah}",
            fields="page_number",
            per_page=PAGE_SIZE,
            page=page,
        )
        verses = payload.get("verses", [])
        for verse in verses:
            # verse_key is "9:129", the ayah number without trusting list order.
            _, _, ayah = str(verse.get("verse_key", "")).partition(":")
            number = verse.get("page_number")
            if not ayah.isdigit() or not isinstance(number, int):
                raise ValueError(f"Surah {surah}: no page number for verse {verse.get('verse_key')}")
            rows.append((surah, int(ayah), number))
        pagination = payload.get("pagination") or {}
        if not pagination.get("next_page"):
            return rows
        page = pagination["next_page"]
        time.sleep(PAUSE_SECONDS)


def build() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = DATABASE.with_suffix(".building")
    temporary.unlink(missing_ok=True)

    db = sqlite3.connect(temporary)
    db.executescript(SCHEMA)

    with httpx.Client() as client:
        for surah in range(1, 115):
            rows = pages_of(client, surah)
            db.executemany("INSERT INTO page (surah, ayah, page) VALUES (?, ?, ?)", rows)
            db.commit()
            print(f"  surah {surah:3}: {len(rows):3} ayahs, pages {rows[0][2]}–{rows[-1][2]}")
            time.sleep(PAUSE_SECONDS)

    # Fail loud rather than shipping a database that is quietly wrong: the
    # Madani printing has exactly 604 pages and every one of them carries text.
    seen = {row[0] for row in db.execute("SELECT DISTINCT page FROM page")}
    db.close()
    if seen != set(range(1, TOTAL_PAGES + 1)):
        temporary.unlink(missing_ok=True)
        missing = sorted(set(range(1, TOTAL_PAGES + 1)) - seen)
        raise SystemExit(f"Not the {MUSHAF}, {len(missing)} pages have no ayah: {missing[:10]}")

    temporary.replace(DATABASE)
    print(f"Built {DATABASE}, {MUSHAF}")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:  # noqa: BLE001, a build script reports and stops
        sys.exit(f"Build failed: {exc}")
