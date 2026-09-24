"""Cut al-Suyuti's Lubab al-Nuqul into one asbab al-nuzul passage per ayah.

    python backend/scripts/build_asbab.py            # download if needed, then split
    python backend/scripts/build_asbab.py --from path/to/file   # split a file already here
    python backend/scripts/build_asbab.py --dry-run  # count everything, write nothing

Why a script of its own rather than a reader inside import_quran_editions.py:
the other books arrive already hung on ayahs. This one is a book of running
prose that has to be cut up and matched before it is one, and that matching is
the part a person has to be able to check. So it runs here, writes the plain
ayah-json shape the importer already reads, and lists every report it could not
place beside it:

    data/quran/downloads/lubab-ara1.txt        the book as OpenITI published it
    data/quran/downloads/asbab-lubab-ar.json   the passages, ready to import
    data/quran/asbab-unmatched.json            every report that found no ayah

Then:

    python backend/scripts/import_quran_editions.py --only asbab-lubab-ar

The rule itself is backend/services/asbab_split.py, which is pure and tested.
Nothing here decides where a report goes.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services import asbab_split  # noqa: E402

# OpenITI's pri-data, the same library backend/data/books came from. Free for
# non-commercial use, and the download needs no account.
BOOK_URL = (
    "https://raw.githubusercontent.com/OpenITI/0925AH/master/data/"
    "0911Suyuti/0911Suyuti.LubabNuqul/0911Suyuti.LubabNuqul.Shamela0002247-ara1"
)
BOOK_FILE = "downloads/lubab-ara1.txt"
PASSAGES_FILE = "downloads/asbab-lubab-ar.json"
UNMATCHED_FILE = "asbab-unmatched.json"
# Under this, the split has broken rather than the book being short: the Lubab
# holds around three hundred reports and has done since 1505.
FEWEST_REPORTS = 250


def quran_dir() -> Path:
    return data_path("quran_library_path").parent


def download(target: Path) -> None:
    print(f"  downloading {BOOK_URL}")
    response = httpx.get(BOOK_URL, timeout=120.0, follow_redirects=True)
    response.raise_for_status()
    target.parent.mkdir(parents=True, exist_ok=True)
    scratch = target.with_suffix(".part")
    scratch.write_text(response.text, encoding="utf-8")
    scratch.replace(target)
    print(f"    {target.stat().st_size:,} bytes -> {target.name}")


def surah_names() -> dict[int, str]:
    """Every surah's Arabic name, from meanings.db, which the app already builds."""
    path = quran_dir() / "meanings.db"
    if not path.exists():
        raise SystemExit(
            f"No {path.name}. Run backend/scripts/build_quran_meanings.py first: "
            "the split needs the surah names and the ayahs to match against."
        )
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
        return {int(row[0]): str(row[1]) for row in db.execute("SELECT id, name_ar FROM surah")}


def ayah_text() -> dict[int, dict[int, str]]:
    """Every ayah in plain spelling, by surah, from the file the Qur'an ear uses."""
    path = data_path("quran_imlaei_path")
    if not path.exists():
        raise SystemExit(
            f"No {path.name}. Run backend/scripts/fetch_recitation_checks.py first: "
            "the split matches the book's quotations against this text."
        )
    by_surah: dict[int, dict[int, str]] = {}
    for key, text in json.loads(path.read_text(encoding="utf-8")).items():
        surah, _, ayah = key.partition(":")
        by_surah.setdefault(int(surah), {})[int(ayah)] = text
    return by_surah


def write_surah_types(target: Path) -> None:
    """Which surahs came down at Makkah and which at Madinah, from Quran.com.

    Written once, beside the book, because the timelines need it: a report that
    names no event is put on the Makkan or the Madinan stretch of the Seerah by
    its surah, and nothing else here records which a surah is.
    """
    if target.exists():
        return
    print(f"  fetching revelation places for {target.name}")
    chapters = httpx.get("https://api.quran.com/api/v4/chapters", timeout=60.0).json()["chapters"]
    places = {str(row["id"]): ("makkan" if row["revelation_place"] == "makkah" else "madinan") for row in chapters}
    if len(places) != 114:
        raise SystemExit(f"  expected 114 surahs, got {len(places)}. Nothing written.")
    target.write_text(json.dumps({
        "_comment": "Where each surah came down, from Quran.com. Used to put an asbab report that names no event on the Makkan or the Madinan stretch of the Seerah.",
        "places": places,
    }, ensure_ascii=False, indent=1), encoding="utf-8")


def aliases() -> dict[str, int]:
    """The book's own spellings of surah names, which are data and not code."""
    path = quran_dir() / "asbab-surahs.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {key: value for key, value in rows.items() if not key.startswith("_")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="source", help="Split this file instead of downloading")
    parser.add_argument("--dry-run", action="store_true", help="Count everything, write nothing")
    args = parser.parse_args()

    book_path = Path(args.source) if args.source else quran_dir() / BOOK_FILE
    if not book_path.exists():
        if args.source:
            raise SystemExit(f"No such file: {book_path}")
        download(book_path)

    book = book_path.read_text(encoding="utf-8")
    texts = ayah_text()
    rows, missed = asbab_split.passages(book, surah_names(), aliases(), lambda surah: texts.get(surah, {}))

    reports = len(asbab_split.reports(book))
    if reports < FEWEST_REPORTS:
        raise SystemExit(
            f"Only {reports} reports were cut out of {book_path.name}, and the book has "
            f"about {FEWEST_REPORTS}+. The file or the split rule is wrong; nothing written."
        )

    print(f"  {reports} reports: {reports - len(missed)} placed on {len(rows)} ayahs, {len(missed)} unplaced")
    for why, count in Counter(row["why"] for row in missed).most_common():
        print(f"    {count:4}  {why}")
    if args.dry_run:
        return 0

    target = quran_dir() / PASSAGES_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "book": "Lubab al-Nuqul fi Asbab al-Nuzul",
        "origin": f"OpenITI, {BOOK_URL}",
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "passages": rows,
    }, ensure_ascii=False), encoding="utf-8")

    unmatched = quran_dir() / UNMATCHED_FILE
    unmatched.write_text(json.dumps({
        "_comment": "Reports in the Lubab that this split could not place on one ayah. Listed rather than guessed at: a report on the wrong ayah is worse than a report nobody sees.",
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "reports": missed,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    write_surah_types(quran_dir() / "surah-type.json")
    print(f"  -> {target.name} and {unmatched.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
