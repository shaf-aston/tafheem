"""One-time harvest: a tafsir of the whole Qur'an, stored locally as plain text.

Run once:  python backend/scripts/build_quran_tafsir.py

Why this exists
---------------
The app can say what every word means and how the words assemble. It could not
say what the ayah is about. A tafsir is the one thing a learner reads next, and
Quran.com publishes several in English, free and without a key.

Same shape as build_quran_meanings.py: fetched once, kept in its own database,
read locally forever after. Ibn Kathir's abridgement is the default because it
is the one most readers are pointed at first; TAFSIR below is the only thing to
change to build a different one, the app reads whatever the database holds.

Two things this script does that a naive loop would not:

  It stores the text once. A tafsir commonly covers a run of ayahs in one
  passage, 78:1-10 is a single 9,000-character entry; so the passage is stored
  once in `entry` and each ayah points at it. Storing it per ayah would repeat
  that passage ten times.

  It does not fetch what it already has. When a passage comes back covering ten
  ayahs, those ten are marked done and never requested. That turns 6,236
  requests into roughly half as many.

Plain text, not HTML. What comes back is marked-up HTML, and nothing in this app
renders HTML from the network, it is stripped here, at the edge, so what
reaches the database is text and there is no way for markup to reach a page.

Safe to re-run: writes to a temporary file and swaps it in only at the end, so
an interrupted run never leaves a half-built database in place.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.markup import as_text  # noqa: E402, needs the path above

DATA_DIR = Path(__file__).parent.parent / "data" / "quran"
DATABASE = DATA_DIR / "tafsir.db"
MEANINGS = DATA_DIR / "meanings.db"

API = "https://api.quran.com/api/v4"

# Which tafsir this database holds. The id is Quran.com's; the name and author
# are stored alongside the text so the app can credit it without hardcoding a
# name that would go stale if this line ever changed.
TAFSIR = 169

PAUSE_SECONDS = 0.15
TIMEOUT_SECONDS = 30.0
RETRIES = 3

SCHEMA = """
CREATE TABLE entry (
    -- A passage is named by the first ayah it comments on, "78:1". The API
    -- gives a passage no id of its own, and the ayah it opens on is both stable
    -- and readable, which an invented number would not be.
    id   TEXT PRIMARY KEY,
    text TEXT NOT NULL
);

CREATE TABLE covers (
    surah INTEGER NOT NULL,
    ayah  INTEGER NOT NULL,
    entry TEXT NOT NULL REFERENCES entry(id),
    PRIMARY KEY (surah, ayah)
) WITHOUT ROWID;

-- One row. What this database is, so the app credits the right scholar even if
-- TAFSIR above is changed and the database rebuilt.
CREATE TABLE about (
    name   TEXT NOT NULL,
    author TEXT NOT NULL
);
"""

def _get(client: httpx.Client, path: str) -> dict:
    """One API call, retried on the transient failures a long run will hit."""
    for attempt in range(1, RETRIES + 1):
        try:
            response = client.get(f"{API}{path}", timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            if attempt == RETRIES:
                raise
            wait = attempt * 2
            print(f"    {type(exc).__name__}, retrying in {wait}s ({attempt}/{RETRIES})")
            time.sleep(wait)
    raise AssertionError("unreachable")


def whose(client: httpx.Client) -> tuple[str, str]:
    """The name and author of the tafsir being built, so the app credits it
    without a name hardcoded here that TAFSIR could silently outgrow."""
    for resource in _get(client, "/resources/tafsirs").get("tafsirs", []):
        if resource.get("id") == TAFSIR:
            return resource.get("name", ""), resource.get("author_name", "")
    raise SystemExit(f"Quran.com lists no tafsir {TAFSIR}, check the TAFSIR id.")


def ayah_counts() -> list[tuple[int, int]]:
    """(surah, how many ayahs), from the build the meanings script already made.

    Read rather than fetched: the number of ayahs in a surah is a fact this
    machine already holds, and one more source of it is one more thing to
    disagree with the others.
    """
    if not MEANINGS.exists():
        raise SystemExit(
            f"{MEANINGS.name} is missing, run build_quran_meanings.py first; "
            "this script reads the ayah counts from it rather than fetching them again."
        )
    db = sqlite3.connect(f"file:{MEANINGS}?mode=ro", uri=True)
    rows = db.execute("SELECT id, ayahs FROM surah ORDER BY id").fetchall()
    db.close()
    return [(int(surah), int(count)) for surah, count in rows]


def read_passage(surah: int, ayah: int, payload: dict) -> tuple[str, list[int]]:
    """One answer from the API, as its words and the ayahs of this surah it
    covers.

    Pure: a dict in, a passage out, nothing fetched and nothing stored. A
    commentary is often written about a run of ayahs at once, and the API says
    so in `verses`; where it says nothing the ayah asked for is the only one
    covered. Keys naming another surah are dropped rather than trusted, because
    storing one would file this surah's passage under a different one.

    Empty text, or nothing covered, means the scholar did not comment here. The
    caller stores neither: absent is a state the app knows how to show, an empty
    panel is not.
    """
    tafsir = payload.get("tafsir") or {}
    text = as_text(tafsir.get("text") or "")

    keys = list((tafsir.get("verses") or {}).keys()) or [f"{surah}:{ayah}"]
    covered = []
    for key in keys:
        part, _, number = str(key).partition(":")
        if part.isdigit() and number.isdigit() and int(part) == surah:
            covered.append(int(number))
    return text, covered


def build() -> None:
    counts = ayah_counts()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = DATABASE.with_suffix(".building")
    temporary.unlink(missing_ok=True)

    db = sqlite3.connect(temporary)
    db.executescript(SCHEMA)

    fetched = 0

    with httpx.Client() as client:
        about = whose(client)
        for surah, total in counts:
            done: set[int] = set()
            for ayah in range(1, total + 1):
                if ayah in done:
                    continue
                payload = _get(client, f"/tafsirs/{TAFSIR}/by_ayah/{surah}:{ayah}")
                fetched += 1

                text, covered = read_passage(surah, ayah, payload)
                # Marked done whether or not the passage is stored: an ayah
                # this answer covered has been asked about, and asking again
                # costs a request for the same words.
                done.update(covered)
                if not text or not covered:
                    time.sleep(PAUSE_SECONDS)
                    continue

                # The passage is named by the ayah it opens on, so the same
                # passage reached from any of its ayahs is stored once.
                entry = f"{surah}:{min(covered)}"
                db.execute("INSERT OR IGNORE INTO entry (id, text) VALUES (?, ?)", (entry, text))
                db.executemany(
                    "INSERT OR REPLACE INTO covers (surah, ayah, entry) VALUES (?, ?, ?)",
                    [(surah, number, entry) for number in covered],
                )
                time.sleep(PAUSE_SECONDS)

            db.commit()
            held = db.execute("SELECT COUNT(*) FROM covers WHERE surah = ?", (surah,)).fetchone()[0]
            print(f"  surah {surah:3}: {held:3}/{total} ayahs covered  ({fetched} requests so far)")

    name, author = about
    db.execute("INSERT INTO about (name, author) VALUES (?, ?)", (name, author))
    db.commit()

    ayahs = db.execute("SELECT COUNT(*) FROM covers").fetchone()[0]
    entries = db.execute("SELECT COUNT(*) FROM entry").fetchone()[0]
    db.close()

    # Fail loud rather than shipping a database that is mostly empty. A tafsir
    # that reached under half the Qur'an means the run broke, not that the
    # scholar was quiet.
    if ayahs < 3000:
        temporary.unlink(missing_ok=True)
        raise SystemExit(f"Only {ayahs} ayahs covered, that is a broken run, not a tafsir.")

    temporary.replace(DATABASE)
    print(f"Built {DATABASE}, {name}: {entries} passages over {ayahs} ayahs, {fetched} requests")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:  # noqa: BLE001, a build script reports and stops
        sys.exit(f"Build failed: {exc}")
