"""Download the narrator pages for hadith books from sunnah.com, once, for the Hadith tab.

    python backend/scripts/fetch_rijal.py muslim 24     one book
    python backend/scripts/fetch_rijal.py muslim        every book of a collection
    python backend/scripts/fetch_rijal.py --all         every collection

Run by hand. Saves each page gzipped under rijal_pages_dir (books/ and
narrators/), skips what is already there, and then fetches every narrator
the cached book pages name, and no one else. build_rijal.py reads the cache.

sunnah.com refuses plain HTTP clients, so this asks as a browser (curl_cffi).
Pace, timeout and retries are in data/rijal/rijal.json. A block or a page that
keeps failing stops the run loudly; run it again and it resumes from the cache.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from curl_cffi import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services.hadith import loader  # noqa: E402
from backend.services.rijal import cache, parse  # noqa: E402


class Fetcher:
    def __init__(self) -> None:
        self.knobs = json.loads((data_path("rijal_dir") / "rijal.json").read_text(encoding="utf-8"))
        self.session = requests.Session(impersonate=self.knobs["impersonate"])
        self.fetched = 0

    def get(self, path: str) -> str:
        """The page, or "" when the site has none. Anything else the site says after the last retry stops the run."""
        for attempt in range(1, self.knobs["retries"] + 1):
            time.sleep(self.knobs["pace_seconds"] * attempt)
            reply = self.session.get(self.knobs["site"] + path, timeout=self.knobs["timeout_seconds"])
            if reply.status_code == 200:
                self.fetched += 1
                return reply.text
            if reply.status_code == 404:
                return ""
        raise SystemExit(f"stopped: {path} answered {reply.status_code} {self.knobs['retries']} times; run again later to resume")

    def save(self, file: Path, path: str) -> None:
        if not file.exists():
            cache.write(file, self.get(path))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("collection", nargs="?")
    parser.add_argument("book", nargs="?", type=int)
    parser.add_argument("--all", action="store_true", help="every collection")
    args = parser.parse_args()
    if not args.all and not args.collection:
        parser.error("name a collection, or --all")

    ids = [c for c, *_ in loader.collections()] if args.all else [args.collection]
    if any(loader.collection_name(c) is None for c in ids):
        print(f"not a collection in hadith.db: {', '.join(ids)}")
        return 1
    fetcher = Fetcher()
    for collection in ids:
        for book in [args.book] if args.book else [b["number"] for b in loader.books(collection)]:
            fetcher.save(cache.book_path(collection, book), f"/{collection}/{book}")

    wanted = {who for _, _, page in cache.book_pages()
              for chain in parse.book_chains(cache.read(page)) for who, _ in chain["names"]}
    for n, who in enumerate(sorted(wanted), 1):
        fetcher.save(cache.narrator_path(who), f"/narrator/{who}")
        if n % 50 == 0:
            print(f"  {n}/{len(wanted)} narrators")
    print(f"fetched {fetcher.fetched} pages; {len(wanted)} narrators named by the cached books")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
