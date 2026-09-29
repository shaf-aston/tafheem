"""Download a hadith collection whole, books and all, for the Hadith tab to browse.

    python backend/scripts/fetch_hadith_collections.py
    python backend/scripts/fetch_hadith_collections.py bukhari

Run by hand, like fetch_timeline_hadith.py beside it. Afterwards
build_hadith_index.py reads what this writes and the app never calls out.

Where it comes from
--------------------
fawazahmed0/hadith-api on the jsDelivr CDN: the same mirror of sunnah.com
fetch_timeline_hadith.py already reads, here asked for a collection's every
hadith rather than a handful of cited numbers. Its editions carry
`metadata.sections`, a book number's name, and each hadith's own
`reference.book`, which is the browse structure this script exists to keep.

Numbering
---------
Written the way fetch_timeline_hadith.py already works it out: most
collections key a hadith by their own `hadithnumber`; Muslim instead keys it
by `arabicnumber`, the Abdul Baqi number sunnah.com prints as its reference.
See that script's docstring for why the two must never be confused.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above

EDITIONS = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions"
SOURCE = "https://github.com/fawazahmed0/hadith-api"
NUMBER_FIELD = {"muslim": "arabicnumber"}


def collections() -> dict:
    path = data_path("hadith_dir") / "collections.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if not key.startswith("_")}


def edition(client: httpx.Client, name: str) -> dict:
    reply = client.get(f"{EDITIONS}/{name}.json", timeout=180)
    reply.raise_for_status()
    return reply.json()


def books_of(metadata: dict) -> list[dict]:
    """Every book the edition's own sections declare, in book-number order.

    Book "0" is the edition's front matter (an introduction, or nothing);
    dropped rather than shown as a chapter with no hadiths of its own.
    """
    sections = metadata.get("sections") or {}
    return [
        {"number": int(number), "name": name}
        for number, name in sorted(sections.items(), key=lambda pair: int(pair[0]))
        if int(number) != 0 and str(name).strip()
    ]


def hadiths_of(arabic: dict, english: dict, collection: str) -> list[dict]:
    """Every hadith, numbered and placed in its book, Arabic first and English beside it.

    The Abdul Baqi number carries a part after the point (157.03), letters the
    narrations sharing one reference number the way sunnah.com prints them, so
    .01 is a, .03 is c. English is matched by the same field the Arabic used,
    since both editions of one collection number the same way; a hadith the
    English edition lacks a match for still gets its Arabic and an empty
    english. `grades` is each scholar's verdict as the English edition gives
    it; the two Sahihs carry none, their grading is the collection's own.
    """
    field = NUMBER_FIELD.get(collection, "hadithnumber")
    by_number = {}
    for item in english.get("hadiths") or []:
        whole, _, part = str(item.get(field) or "").partition(".")
        if whole.isdigit():
            by_number[(int(whole), part)] = item

    out = []
    for item in arabic.get("hadiths") or []:
        whole, _, part = str(item.get(field) or "").partition(".")
        if not whole.isdigit():
            continue
        number = int(whole)
        letter = chr(ord("a") + int(part) - 1) if part.isdigit() and 1 <= int(part) <= 26 else ""
        text = (item.get("text") or "").strip()
        if not text:
            continue
        match = by_number.get((number, part)) or {}
        out.append({
            "book": (item.get("reference") or {}).get("book", 0),
            "number": number,
            "part": letter,
            "arabic": text,
            "english": (match.get("text") or "").strip(),
            "grades": [{"by": g["name"], "grade": g["grade"]} for g in match.get("grades") or []
                       if g.get("name") and g.get("grade")],
        })
    return out


def fetch_one(client: httpx.Client, key: str) -> None:
    arabic = edition(client, f"ara-{key}")
    english = edition(client, f"eng-{key}")
    books = books_of(arabic.get("metadata") or {})
    hadiths = hadiths_of(arabic, english, key)
    kept_books = {h["book"] for h in hadiths}

    out = data_path("hadith_dir") / f"{key}.json"
    out.write_text(json.dumps({
        "_about": [
            f"Every hadith of {key}, Arabic and English, grouped by book.",
            "Written by backend/scripts/fetch_hadith_collections.py; never edited by hand.",
        ],
        "source": {"name": "fawazahmed0/hadith-api, from sunnah.com", "url": SOURCE,
                    "fetched": datetime.now(timezone.utc).date().isoformat()},
        "books": [b for b in books if b["number"] in kept_books],
        "hadith": hadiths,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  {key}: {len(hadiths)} hadiths across {len(kept_books)} books -> {out}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keys", nargs="*", help="collections to fetch; default is every one in collections.json")
    args = parser.parse_args()

    wanted = args.keys or list(collections())
    unknown = [k for k in wanted if k not in collections()]
    if unknown:
        print(f"not in collections.json: {', '.join(unknown)}")
        return 1

    with httpx.Client(follow_redirects=True) as client:
        for key in wanted:
            fetch_one(client, key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
