"""Download the books named in editions.json, from mirrors that need no account.

    python backend/scripts/fetch_quran_editions.py
    python backend/scripts/fetch_quran_editions.py --only jalalayn-ar
    python backend/scripts/fetch_quran_editions.py --list

This is the acquire step, and the only part of the library that touches the
network. It runs by hand, once per book, exactly as build_dictionary.py's
Wiktionary dump does. Afterwards the importer reads files and the app reads the
imported library; neither of them ever calls out.

Why this exists
---------------
The Quranic Universal Library holds all nine of these books, but its download
button sits behind a free account, so a script cannot reach it. The same books
are published elsewhere without any account at all:

    tafsir-api   github.com/spa5k/tafsir_api, served by the jsDelivr CDN. It
                 mirrors QUL's own resources, one JSON file per surah, and the
                 manifest's `origin` records which QUL resource each one is.

    quran.com    api.quran.com/api/v4, free and unauthenticated. It is already
                 where this app's word-by-word English, its mushaf layout and
                 Ibn Kathir came from, so it is not a new dependency.

What is written
---------------
One file per book, in the plainest shape a book can have:

    {"passages": [{"surah": 2, "ayah": 255, "text": "..."}, ...]}

Every mirror is flattened into that here, so the importer learns one shape and
nothing downstream knows a mirror exists. The header alongside it records where
the file came from and when, because a downloaded file with no provenance is a
file nobody can check later.

Ayah numbers are never guessed. tafsir-api states the surah and ayah of every
passage. Quran.com returns a whole chapter in order without numbering it, so the
count is checked against its own chapter index first and the run refuses to write
anything if the two disagree.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.scripts.import_quran_editions import manifest, source_file  # noqa: E402

SURAHS = 114

TAFSIR_API = "https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir"
QURAN_COM = "https://api.quran.com/api/v4"

# Courtesy pause between requests. These are free, unauthenticated services being
# asked for a whole book; there is no hurry.
PAUSE_SECONDS = 0.15
TIMEOUT_SECONDS = 60.0
RETRIES = 3


def _get(client: httpx.Client, url: str, **params):
    """One request, retried on the transient failures a 114-request run will hit."""
    for attempt in range(1, RETRIES + 1):
        try:
            response = client.get(url, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            if attempt == RETRIES:
                raise SystemExit(f"  {url} failed after {RETRIES} tries: {exc}") from exc
            wait = attempt * 2
            print(f"    {type(exc).__name__}, retrying in {wait}s ({attempt}/{RETRIES})")
            time.sleep(wait)
    raise AssertionError("unreachable")


# ── Mirrors: one per service, and the only code that knows that service ──────


def from_tafsir_api(client: httpx.Client, book: str) -> list[dict]:
    """A tafsir, one surah at a time. Each file already names its own ayahs."""
    passages = []
    for surah in range(1, SURAHS + 1):
        for row in _get(client, f"{TAFSIR_API}/{book}/{surah}.json"):
            if text := str(row.get("text", "")).strip():
                passages.append(
                    {"surah": int(row["surah"]), "ayah": int(row["ayah"]), "text": text}
                )
        time.sleep(PAUSE_SECONDS)
    return passages


def from_quran_com(client: httpx.Client, book: str) -> list[dict]:
    """A translation, one chapter at a time, numbered by its own chapter index.

    The endpoint returns a chapter's translations in order and does not say which
    ayah each belongs to. Rather than assume, the length is checked against the
    verse count quran.com itself publishes for that chapter. If a chapter ever
    comes back short, the ayah numbers from there on would all be wrong, and a
    translation silently attached to the wrong ayahs is the worst thing this
    script could produce, so it stops instead.
    """
    counts = {
        int(chapter["id"]): int(chapter["verses_count"])
        for chapter in _get(client, f"{QURAN_COM}/chapters")["chapters"]
    }

    passages = []
    for surah in range(1, SURAHS + 1):
        rows = _get(client, f"{QURAN_COM}/quran/translations/{book}", chapter_number=surah)
        rows = rows["translations"]
        if len(rows) != counts[surah]:
            raise SystemExit(
                f"  surah {surah} came back with {len(rows)} lines but has "
                f"{counts[surah]} ayahs. Nothing written: the ayah numbers after "
                "this point could not be trusted."
            )
        for ayah, row in enumerate(rows, start=1):
            if text := str(row.get("text", "")).strip():
                passages.append({"surah": surah, "ayah": ayah, "text": text})
        time.sleep(PAUSE_SECONDS)
    return passages


MIRRORS = {"tafsir-api": from_tafsir_api, "quran.com": from_quran_com}


# ── The run ─────────────────────────────────────────────────────────────────


def fetchable() -> dict[str, dict]:
    """The books this script can get: the ones the manifest gives a `fetch` block."""
    return {
        edition_id: spec
        for edition_id, spec in manifest().items()
        if isinstance(spec.get("fetch"), dict)
    }


def fetch(client: httpx.Client, edition_id: str, spec: dict) -> int:
    """Download one book and write it. Returns how many passages it holds."""
    where = spec["fetch"]
    mirror = where.get("mirror")
    if mirror not in MIRRORS:
        raise SystemExit(
            f"{edition_id}: fetch.mirror must be one of {sorted(MIRRORS)}, got {mirror!r}."
        )

    print(f"  {edition_id}: {spec['name']} from {mirror}")
    passages = MIRRORS[mirror](client, str(where["book"]))
    if not passages:
        raise SystemExit(f"{edition_id}: the mirror returned nothing. Nothing written.")

    target = source_file(spec)
    target.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "book": spec["name"],
        "origin": spec["origin"],
        "mirror": mirror,
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "passages": passages,
    }
    # Written whole and moved into place, so an interrupted download cannot leave
    # a half-file that looks importable.
    scratch = target.with_suffix(f"{target.suffix}.part")
    scratch.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    scratch.replace(target)

    ayahs = len({(row["surah"], row["ayah"]) for row in passages})
    print(f"    {len(passages):,} passages over {ayahs:,} ayahs -> {target.name}")
    return len(passages)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Fetch just this one edition id")
    parser.add_argument("--list", action="store_true", help="Show what can be fetched and stop")
    args = parser.parse_args()

    books = fetchable()
    if args.list:
        for edition_id, spec in books.items():
            print(f"  {edition_id:16} {spec['fetch']['mirror']:11} {spec['name']}")
        return 0

    if args.only:
        if args.only not in books:
            raise SystemExit(
                f"{args.only!r} is not a fetchable book. Try: {', '.join(books) or 'none'}."
            )
        books = {args.only: books[args.only]}

    print(f"Fetching into {data_path('quran_library_path').parent / 'downloads'}")
    with httpx.Client(headers={"Accept": "application/json"}, follow_redirects=True) as client:
        for edition_id, spec in books.items():
            fetch(client, edition_id, spec)

    print("\nNow import them:  python backend/scripts/import_quran_editions.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
