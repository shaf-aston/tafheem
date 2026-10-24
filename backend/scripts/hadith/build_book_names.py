"""The Arabic name of every hadith book, read from the cached sunnah.com book pages into data/hadith/book_names.json.

    python backend/scripts/hadith/build_book_names.py

Run by hand after fetch_rijal.py. The file is kept in git because the server has no page cache;
build_hadith_index.py puts it into hadith.db's book table. A book with no name shows its English alone.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services.hadith.rijal import cache, parse  # noqa: E402


def main() -> int:
    names: dict[str, dict[str, str]] = {}
    for collection, book, page in cache.book_pages():
        if name := parse.book_name(cache.read(page)):
            names.setdefault(collection, {})[str(book)] = name
    out = data_path("hadith_dir") / "book_names.json"
    out.write_text(json.dumps(names, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{sum(map(len, names.values()))} book names from {len(names)} collections into {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
