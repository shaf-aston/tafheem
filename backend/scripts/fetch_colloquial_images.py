"""Find a free picture for each Colloquial phrase, one careful step at a time.

    python -m backend.scripts.fetch_colloquial_images propose --unit 1 [--lesson 2]
    python -m backend.scripts.fetch_colloquial_images approve --unit 1 --lesson 2 --phrase 4 --pick 2

`propose` asks Openverse (free, no key) for a few candidates per phrase, using
only the phrase's own `search_term`, and writes them with their licences to a
review file. Nothing is downloaded and no lesson is touched. A phrase with no
`search_term` is listed as needing one, never guessed from its English.

Phrases are read from spine.json, the course outline every dialect shares, so
one picture serves the same phrase in every dialect.

`approve` downloads the one candidate you chose, saves it under
data/colloquial/images/<unit>/, records who made it and under what licence in
that folder's attribution.json, and sets the slot's `image` in the spine. A wrong
picture therefore never reaches a lesson without a person choosing it.

Plain stock-photo sources (STOCK) are asked first: their pictures are simple,
well lit and object-centred, where the open search is mostly holiday snapshots.
The open search only tops up a phrase the stock sources have too little for.

Single words work the same way, keyed by the word's id in words.json rather
than by position, since one picture serves the word in every topic that teaches it:

    python -m backend.scripts.fetch_colloquial_images propose-words --unit 2 [--lesson 2]
    python -m backend.scripts.fetch_colloquial_images approve-word --id apple --pick 1

To fill a whole course at once, `auto` proposes and then approves the first
candidate whose title names what was searched for, for every phrase and word that has a search_term and no
picture. Every picture it saves is listed in review/auto.json so a person can look
over them in one sitting and `reject` any that are wrong:

    python -m backend.scripts.fetch_colloquial_images auto
    python -m backend.scripts.fetch_colloquial_images reject --image words/apple.jpg

A word is only searched for when its line in words.json has a `search_term`;
"from" or "also" have nothing to show and simply never get one.

Only pictures licensed for commercial use and for modification are asked for, and
the 600 px thumbnail is fetched, never the full original.
"""
from __future__ import annotations

import argparse
import json
import re
from contextlib import suppress
import sys
from pathlib import Path

import httpx

from backend.config import data_path
from backend.services.colloquial import wordlist

API = "https://api.openverse.org/v1/images/"
HEADERS = {"User-Agent": "tafheem-colloquial/1.0 (https://tafheem-app.vercel.app; learning app image proposals)"}
LICENSES = "commercial,modification"
CANDIDATES_PER_PHRASE = 4
STOCK = "stocksnap,rawpixel"
TIMEOUT_SECONDS = 45
COMMONS = "https://commons.wikimedia.org/w/api.php"


def unit_name(number: int) -> str:
    return f"unit-{number:02d}"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "picture"


def candidate(result: dict) -> dict:
    """What a person needs to judge and credit one Openverse result."""
    keep = ("id", "title", "creator", "license", "license_version", "license_url", "foreign_landing_url")
    return {key: result.get(key) for key in keep} | {"thumbnail": result["thumbnail"]}


def commons(term: str, client: httpx.Client) -> list[dict]:
    """Wikimedia Commons, asked when Openverse is out of its daily allowance (200 a day
    without an account). Commons only holds freely licensed files, commercial use included."""
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
              "gsrsearch": f"{term} filemime:image/jpeg", "gsrlimit": CANDIDATES_PER_PHRASE,
              "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 600}
    reply = client.get(COMMONS, params=params)
    reply.raise_for_status()
    pages = sorted(reply.json().get("query", {}).get("pages", {}).values(), key=lambda page: page["index"])
    found = []
    for page in pages:
        info = page["imageinfo"][0]
        meta = {key: re.sub(r"<[^>]+>", "", value["value"]).strip() for key, value in info.get("extmetadata", {}).items()}
        found.append({"id": f"commons-{page['pageid']}", "title": page["title"].removeprefix("File:"),
                      "creator": meta.get("Artist"), "license": meta.get("LicenseShortName"),
                      "license_version": None, "license_url": meta.get("LicenseUrl"),
                      "foreign_landing_url": info.get("descriptionurl"), "thumbnail": info["thumburl"]})
    return found


def search(term: str, client: httpx.Client) -> list[dict]:
    found: list[dict] = []
    try:
        for source in (STOCK, None):
            params = {"q": term, "license_type": LICENSES, "page_size": CANDIDATES_PER_PHRASE, "extension": "jpg",
                      "category": "photograph"}  # museum scans and drawings match titles, not meaning
            reply = client.get(API, params=params | ({"source": source} if source else {}))
            reply.raise_for_status()
            seen = {one["id"] for one in found}
            found += [candidate(r) for r in reply.json()["results"] if r["id"] not in seen]
            if len(found) >= CANDIDATES_PER_PHRASE:
                break
    except httpx.HTTPError:
        pass
    if not found:
        try:
            found = commons(term, client)
        except httpx.HTTPError:
            pass
    return found[:CANDIDATES_PER_PHRASE]


FILLER = {"a", "an", "the", "of", "and", "with", "in", "on", "at", "for", "to", "photo", "image", "free", "picture", "together"}


def words_of(text: str) -> set[str]:
    return {w.rstrip("s") for w in re.findall(r"[a-z]+", (text or "").lower())} - FILLER


def fitting(entry: dict, key: str = "search_term") -> int | None:
    """The first candidate whose title names something the search asked for, as a 1-based
    pick, or None. A stock search matches loose tags ("family photo together" brings
    penguins first), so an unchecked first result is often the wrong picture. Every word asked for
    must be in the title: one shared word let "tall man" through as a cigar label."""
    wanted = words_of(entry[key])
    return next((at for at, one in enumerate(entry["candidates"], start=1) if wanted <= words_of(one["title"])), None)


def paths(unit: str) -> tuple[Path, Path, Path]:
    """The spine, the unit's review file and its picture folder."""
    root = data_path("colloquial_dir")
    return root / "spine.json", root / "review" / f"{unit}.json", root / "images" / unit


def spine_text(spine: dict) -> str:
    """The spine as it is kept by hand: indented, but a list of plain values on one line."""
    def flat(m: re.Match) -> str:
        return json.dumps(json.loads(m.group(0)), ensure_ascii=False)
    body = json.dumps(spine, ensure_ascii=False, indent=2)
    return re.sub(r"\[(?:\s*\"[^\"\n]*\",?)+\s*\]", flat, body) + "\n"


def outline(spine: dict, unit: str) -> dict:
    return next(one for one in spine["units"] if one["unit"] == unit)


def propose(unit: str, lesson: int | None, client: httpx.Client) -> dict:
    spine_file, review_file, _ = paths(unit)
    lessons = outline(json.loads(spine_file.read_text(encoding="utf-8")), unit)["lessons"]
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


def approve(unit: str, lesson: int, phrase: int, pick: int, client: httpx.Client) -> str:
    spine_file, review_file, folder = paths(unit)
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

    spine = json.loads(spine_file.read_text(encoding="utf-8"))
    relative = f"{unit}/{name}"
    outline(spine, unit)["lessons"][lesson - 1]["phrases"][phrase - 1]["image"] = relative
    spine_file.write_text(spine_text(spine), encoding="utf-8")
    return relative


def _words_file() -> Path:
    return data_path("colloquial_dir") / wordlist.FILE


def propose_words(unit: str, lesson: int | None, client: httpx.Client) -> dict:
    """Candidates for every word of a unit's topics that has a search_term and no picture yet."""
    spine_file, _, _ = paths(unit)
    meanings = json.loads(_words_file().read_text(encoding="utf-8"))["words"]
    ids = [one for at, topic in enumerate(outline(json.loads(spine_file.read_text(encoding="utf-8")), unit)["lessons"], start=1)
           if not lesson or at == lesson for one in topic.get("words", [])]
    found, missing = {}, []
    for one in dict.fromkeys(ids):
        meaning = meanings.get(one, {})
        if meaning.get("image"):
            continue
        if not meaning.get("search_term"):
            missing.append(one)
            continue
        found[one] = {"english": meaning["english"], "search_term": meaning["search_term"],
                      "candidates": search(meaning["search_term"], client)}
    review = {"found": found, "needs_search_term": missing}
    review_file = data_path("colloquial_dir") / "review" / f"words-{unit}.json"
    review_file.parent.mkdir(parents=True, exist_ok=True)
    review_file.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return review


def approve_word(word: str, pick: int, client: httpx.Client) -> str:
    """Save the chosen candidate for one word, credit it, and point the word at it."""
    reviews = sorted((data_path("colloquial_dir") / "review").glob("words-*.json"))
    entry = next(found[word] for review in reviews if word in (found := json.loads(review.read_text(encoding="utf-8"))["found"]))
    chosen = entry["candidates"][pick - 1]
    picture = client.get(chosen["thumbnail"], follow_redirects=True)
    picture.raise_for_status()

    folder = data_path("colloquial_dir") / "images" / "words"
    name = f"{slug(word)}.jpg"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(picture.content)
    sidecar = folder / "attribution.json"
    credits = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {}
    credits[name] = {k: v for k, v in chosen.items() if k != "thumbnail"} | {"search_term": entry["search_term"]}
    sidecar.write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")

    whole = json.loads(_words_file().read_text(encoding="utf-8"))
    whole["words"][word]["image"] = f"words/{name}"
    _words_file().write_text(wordlist.text(whole["words"], whole.get("_about", "")), encoding="utf-8")
    return f"words/{name}"


def auto(client: httpx.Client) -> list[str]:
    """Approve the first candidate everywhere a search_term has no picture yet."""
    spine = json.loads(paths("unit-01")[0].read_text(encoding="utf-8"))
    saved: list[str] = []
    for one in spine["units"]:
        unit = one["unit"]
        for entry in propose(unit, None, client)["found"]:
            if pick := fitting(entry):
                with suppress(httpx.HTTPError):  # one dead thumbnail never stops the run
                    saved.append(approve(unit, entry["lesson"], entry["phrase"], pick, client))
        for word, entry in propose_words(unit, None, client)["found"].items():
            # A word is matched on itself: its search_term may add a hint ("lion wild
            # animal") that a good picture's title would not carry.
            if (pick := fitting(entry, "english")) and not json.loads(_words_file().read_text(encoding="utf-8"))["words"][word].get("image"):
                with suppress(httpx.HTTPError):
                    saved.append(approve_word(word, pick, client))
    log = data_path("colloquial_dir") / "review" / "auto.json"
    earlier = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []
    log.write_text(json.dumps(earlier + saved, indent=2), encoding="utf-8")
    return saved


def reject(image: str) -> None:
    """Undo one picture: delete the file, its credit, and every slot pointing at it."""
    root = data_path("colloquial_dir")
    folder, name = (root / "images" / image).parent, Path(image).name
    (folder / name).unlink(missing_ok=True)
    sidecar = folder / "attribution.json"
    if sidecar.exists():
        credits = json.loads(sidecar.read_text(encoding="utf-8"))
        credits.pop(name, None)
        sidecar.write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
    spine_file = root / "spine.json"
    spine = json.loads(spine_file.read_text(encoding="utf-8"))
    for unit in spine["units"]:
        for lesson in unit["lessons"]:
            for phrase in lesson["phrases"]:
                if phrase.get("image") == image:
                    del phrase["image"]
    spine_file.write_text(spine_text(spine), encoding="utf-8")
    whole = json.loads(_words_file().read_text(encoding="utf-8"))
    for meaning in whole["words"].values():
        if meaning.get("image") == image:
            del meaning["image"]
    _words_file().write_text(wordlist.text(whole["words"], whole.get("_about", "")), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=("propose", "approve", "propose-words", "approve-word", "auto", "reject"))
    ap.add_argument("--unit", type=int)
    ap.add_argument("--id")
    ap.add_argument("--lesson", type=int)
    ap.add_argument("--phrase", type=int)
    ap.add_argument("--pick", type=int)
    ap.add_argument("--image")
    args = ap.parse_args(argv)
    if args.action == "reject":
        if not args.image:
            sys.exit("reject needs --image")
        return reject(args.image)
    if args.action == "auto":
        with httpx.Client(headers=HEADERS, timeout=TIMEOUT_SECONDS) as client:
            print(len(auto(client)), "pictures saved; see review/auto.json")
        return
    if args.action != "approve-word" and not args.unit:
        sys.exit(f"{args.action} needs --unit")
    unit = unit_name(args.unit) if args.unit else ""
    with httpx.Client(headers=HEADERS, timeout=TIMEOUT_SECONDS) as client:
        if args.action == "propose-words":
            review = propose_words(unit, args.lesson, client)
            print(f"{len(review['found'])} words with candidates, {len(review['needs_search_term'])} have no search_term")
        elif args.action == "approve-word":
            if not (args.id and args.pick):
                sys.exit("approve-word needs --id and --pick")
            print("saved", approve_word(args.id, args.pick, client))
        elif args.action == "propose":
            review = propose(unit, args.lesson, client)
            print(f"{len(review['found'])} phrases with candidates, {len(review['needs_search_term'])} need a search_term")
        else:
            if not (args.lesson and args.phrase and args.pick):
                sys.exit("approve needs --lesson, --phrase and --pick")
            print("saved", approve(unit, args.lesson, args.phrase, args.pick, client))


if __name__ == "__main__":
    main()
