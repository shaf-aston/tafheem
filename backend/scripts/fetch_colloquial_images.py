"""Find a free picture for each Colloquial phrase, one careful step at a time.

    python -m backend.scripts.fetch_colloquial_images propose --unit 1 [--lesson 2]
    python -m backend.scripts.fetch_colloquial_images approve --unit 1 --lesson 2 --phrase 4 --pick 2

`propose` asks Openverse (free, no key) for a few candidates per phrase, using
only the phrase's own `search_term`, and writes them with their licences to a
review file. Nothing is downloaded and no lesson is touched. A phrase with no
`search_term` is listed as needing one, never guessed from its English.

`approve` downloads the one candidate you chose, saves it under
data/colloquial/images/<dialect>/<unit>/, records who made it and under what
licence in that folder's attribution.json, and sets the phrase's `image`. A wrong
picture therefore never reaches a lesson without a person choosing it.

Only pictures licensed for commercial use and for modification are asked for, and
the 600 px thumbnail is fetched, never the full original.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import httpx

from backend.config import data_path

API = "https://api.openverse.org/v1/images/"
HEADERS = {"User-Agent": "tafheem-colloquial/1.0 (learning app; image proposals)"}
LICENSES = "commercial,modification"
CANDIDATES_PER_PHRASE = 4
TIMEOUT_SECONDS = 20


def unit_name(number: int) -> str:
    return f"unit-{number:02d}"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "picture"


def candidate(result: dict) -> dict:
    """What a person needs to judge and credit one Openverse result."""
    keep = ("id", "title", "creator", "license", "license_version", "license_url", "foreign_landing_url")
    return {key: result.get(key) for key in keep} | {"thumbnail": result["thumbnail"]}


def search(term: str, client: httpx.Client) -> list[dict]:
    reply = client.get(
        API,
        params={"q": term, "license_type": LICENSES, "page_size": CANDIDATES_PER_PHRASE, "extension": "jpg"},
    )
    reply.raise_for_status()
    return [candidate(result) for result in reply.json()["results"]]


def paths(dialect: str, unit: str) -> tuple[Path, Path, Path]:
    """The unit file, its review file and its picture folder."""
    root = data_path("colloquial_dir")
    return root / dialect / f"{unit}.json", root / "review" / f"{dialect}-{unit}.json", root / "images" / dialect / unit


def propose(dialect: str, unit: str, lesson: int | None, client: httpx.Client) -> dict:
    unit_file, review_file, _ = paths(dialect, unit)
    lessons = json.loads(unit_file.read_text(encoding="utf-8"))["lessons"]
    found, missing = [], []
    for lesson_at, one in enumerate(lessons, start=1):
        if lesson and lesson_at != lesson:
            continue
        for phrase_at, phrase in enumerate(one["phrases"], start=1):
            where = {"lesson": lesson_at, "phrase": phrase_at, "english": phrase["english"]}
            if phrase.get("image"):
                continue
            if not phrase.get("search_term"):
                missing.append(where)
                continue
            found.append(where | {"search_term": phrase["search_term"], "candidates": search(phrase["search_term"], client)})
    review = {"found": found, "needs_search_term": missing}
    review_file.parent.mkdir(parents=True, exist_ok=True)
    review_file.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return review


def approve(dialect: str, unit: str, lesson: int, phrase: int, pick: int, client: httpx.Client) -> str:
    unit_file, review_file, folder = paths(dialect, unit)
    review = json.loads(review_file.read_text(encoding="utf-8"))
    entry = next(e for e in review["found"] if (e["lesson"], e["phrase"]) == (lesson, phrase))
    chosen = entry["candidates"][pick - 1]
    picture = client.get(chosen["thumbnail"], follow_redirects=True)
    picture.raise_for_status()

    name = f"l{lesson:02d}-p{phrase:02d}-{slug(entry['search_term'])}.jpg"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(picture.content)
    sidecar = folder / "attribution.json"
    credits = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {}
    credits[name] = {k: v for k, v in chosen.items() if k != "thumbnail"} | {"search_term": entry["search_term"]}
    sidecar.write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")

    data = json.loads(unit_file.read_text(encoding="utf-8"))
    relative = f"{dialect}/{unit}/{name}"
    data["lessons"][lesson - 1]["phrases"][phrase - 1]["image"] = relative
    unit_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return relative


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=("propose", "approve"))
    ap.add_argument("--dialect", default="damascene")
    ap.add_argument("--unit", type=int, required=True)
    ap.add_argument("--lesson", type=int)
    ap.add_argument("--phrase", type=int)
    ap.add_argument("--pick", type=int)
    args = ap.parse_args(argv)
    unit = unit_name(args.unit)
    with httpx.Client(headers=HEADERS, timeout=TIMEOUT_SECONDS) as client:
        if args.action == "propose":
            review = propose(args.dialect, unit, args.lesson, client)
            print(f"{len(review['found'])} phrases with candidates, {len(review['needs_search_term'])} need a search_term")
        else:
            if not (args.lesson and args.phrase and args.pick):
                sys.exit("approve needs --lesson, --phrase and --pick")
            print("saved", approve(args.dialect, unit, args.lesson, args.phrase, args.pick, client))


if __name__ == "__main__":
    main()
