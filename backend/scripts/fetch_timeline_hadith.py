"""Download the hadiths the timelines cite, so their words can be read in the tab.

    python backend/scripts/fetch_timeline_hadith.py
    python backend/scripts/fetch_timeline_hadith.py --check

The acquire step, run by hand. Afterwards the app reads data/timelines/hadith.json
and never calls out, exactly as fetch_quran_editions.py works.

Why this exists
---------------
A timeline event named its hadith by number and nothing more, so a reader who
wanted the words had to leave the app for sunnah.com. No hadith collection is
installed here, so the only honest way to print the words was to bring them in.

Where they come from
--------------------
fawazahmed0/hadith-api on the jsDelivr CDN: the nine books in Arabic and in
English, free and with no account. It is itself taken from sunnah.com, which is
where every number in the timelines was checked, so the two agree.

Numbering is the trap and is never guessed
------------------------------------------
sunnah.com's reference number is not the same count in every collection:

    bukhari, abudawud, tirmidhi, ibnmajah   the edition's own `hadithnumber`
    muslim                                  the edition's `arabicnumber`, the
                                            Abdul Baqi number sunnah.com prints
                                            as its reference, e.g. 2902 is the
                                            fire of the Hijaz, while that
                                            edition's `hadithnumber` 2902 is a
                                            hadith about Hajj

A number that matches in neither is written down as missing and left out. A
missing hadith prints its number with no words under it, which is what the tab
did before; a wrongly matched one would put the Prophet's words on the wrong
event, so nothing is matched on a guess.
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
# Which field of an edition carries the number sunnah.com prints as its
# reference. Muslim is the one collection where the two counts differ.
NUMBER_FIELD = {"muslim": "arabicnumber"}
OUT = "hadith.json"
EXTRA = "hadith-extra.json"


def cited() -> dict[str, set[tuple[int, str]]]:
    """Every hadith the section files name, by collection: its number and its part.

    The part is sunnah.com's own letter where it prints one. One reference
    number in Muslim can cover several narrations, printed 157a, 157b, 157c, and
    an event means one of them; a reference with no letter means the page has
    only one hadith on it.
    """
    want: dict[str, set[tuple[int, str]]] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for ref in node.get("refs") or []:
                if isinstance(ref, dict) and ref.get("hadith"):
                    want.setdefault(ref["hadith"], set()).add((ref["number"], ref.get("part") or ""))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for path in sorted((data_path("timelines_dir") / "sections").glob("*.json")):
        walk(json.loads(path.read_text(encoding="utf-8")))
    return want


def edition(client: httpx.Client, name: str) -> list[dict]:
    reply = client.get(f"{EDITIONS}/{name}.json", timeout=120)
    reply.raise_for_status()
    return reply.json()["hadiths"]


def numbered(hadiths: list[dict], collection: str) -> dict[tuple[int, str], dict]:
    """The edition keyed the way sunnah.com prints a reference: number and letter.

    The Abdul Baqi number carries a part after the point (157.03), which counts
    the narrations sharing one reference number in the order sunnah.com letters
    them, so .01 is a, .03 is c. A reference with no letter is keyed with none
    and answers with the first narration, which is the whole of that page.
    """
    field = NUMBER_FIELD.get(collection, "hadithnumber")
    by_number: dict[tuple[int, str], dict] = {}
    for hadith in hadiths:
        whole, _, part = str(hadith.get(field) or "").partition(".")
        if not whole.isdigit():
            continue
        number = int(whole)
        by_number.setdefault((number, ""), hadith)
        if part.isdigit() and 1 <= int(part) <= 26:
            by_number.setdefault((number, chr(ord("a") + int(part) - 1)), hadith)
    return by_number


def named(collection: str, number: int, part: str) -> str:
    return f"{collection}:{number}{part}"


def collect(client: httpx.Client, collection: str, wanted: set[tuple[int, str]]) -> tuple[dict, list[str]]:
    arabic = numbered(edition(client, f"ara-{collection}"), collection)
    english = numbered(edition(client, f"eng-{collection}"), collection)
    found, missing = {}, []
    for number, part in sorted(wanted):
        text = (arabic.get((number, part)) or {}).get("text", "").strip()
        if not text:
            missing.append(named(collection, number, part))
            continue
        found[named(collection, number, part)] = {
            "arabic": text,
            "english": (english.get((number, part)) or {}).get("text", "").strip(),
        }
    return found, missing


def extra() -> dict[str, dict]:
    """Hadiths read from the sunnah.com page itself, because the mirror lacks them.

    Kept in a file of their own rather than typed into the written one: this run
    overwrites what it writes, and a hand-collected hadith sitting in there
    would be lost the next time anybody ran the script.
    """
    path = data_path("timelines_dir") / EXTRA
    if not path.exists():
        return {}
    return {
        key: {"arabic": value["arabic"], "english": value.get("english", "")}
        for key, value in json.loads(path.read_text(encoding="utf-8"))["hadith"].items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="say what would be fetched and stop")
    args = parser.parse_args()

    want = cited()
    total = sum(len(n) for n in want.values())
    print(f"{total} hadiths cited across {len(want)} collections: "
          + ", ".join(f"{k} {len(v)}" for k, v in sorted(want.items())))
    if args.check:
        return 0

    found, missing = {}, []
    with httpx.Client(follow_redirects=True) as client:
        for collection, numbers in sorted(want.items()):
            part, gone = collect(client, collection, numbers)
            found.update(part)
            missing.extend(gone)
            print(f"  {collection}: {len(part)} of {len(numbers)}")

    by_hand = extra()
    found.update({key: words for key, words in by_hand.items() if key in missing or key not in found})
    missing = [key for key in missing if key not in by_hand]
    print(f"  read from sunnah.com by hand: {len(by_hand)}")

    out = data_path("timelines_dir") / OUT
    out.write_text(json.dumps({
        "_about": [
            "The words of every hadith the timelines cite, Arabic and English.",
            "Written by backend/scripts/fetch_timeline_hadith.py; never edited by hand.",
            "Keyed collection:number, the number being the one sunnah.com prints as its reference,",
            "with its letter where that page prints several narrations under one number.",
            "A cited number missing from here prints as a number alone, as it did before.",
        ],
        "source": {
            "name": "fawazahmed0/hadith-api, from sunnah.com",
            "url": SOURCE,
            "fetched": datetime.now(timezone.utc).date().isoformat(),
            "by_hand": EXTRA,
        },
        "missing": missing,
        "hadith": dict(sorted(found.items())),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out} ({len(found)} hadiths, {len(missing)} missing)")
    for gone in missing:
        print(f"  missing: {gone}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
