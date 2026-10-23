"""Ask Daleel a question from a terminal, with each step timed.

    python -m backend.services.daleel صبر
    python -m backend.services.daleel "الحمد لله" --book "مختصر القدوري" --limit 5
    python -m backend.services.daleel patience --json
    python -m backend.services.daleel صبر --explain     # the terms and the timings

Runs the same steps `search.search` runs, against the same daleel.db, without
the web server. The live API answers the same question:

    curl -G https://tafheem-app.vercel.app/api/daleel --data-urlencode "q=صبر"
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict

from backend.services.daleel import catalogue, search
from backend.services.daleel.index.connection import is_built


def main(argv: list[str] | None = None) -> int:
    args = _arguments(argv)
    if not is_built():
        print("daleel.db is not built: python backend/scripts/build_daleel_index.py", file=sys.stderr)
        return 1

    hits, timings, expansion = _timed(args.query, args.limit, catalogue.known_books(args.book))
    if args.json:
        print(json.dumps([asdict(hit) for hit in hits], ensure_ascii=False, indent=2))
        return 0
    if args.explain:
        for name in ("typed", "phrase", "related", "roots", "loose"):
            print(f"{name:>8}: {getattr(expansion, name) or '-'}")
        print("    took: " + "  ".join(f"{step} {ms:.1f}ms" for step, ms in timings.items()))
        print("          (the first expand of a run includes loading the dictionary)")
        print()
    for hit in hits:
        print(f"[{hit.match}] {hit.source} · {hit.book} · {hit.locator}")
        print(f"  {_underlined(hit.arabic, hit.arabic_marks)}")
        if hit.english:
            print(f"  {_underlined(hit.english, hit.english_marks)}")
    if not hits:
        print("no passage found")
    return 0


def _arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m backend.services.daleel", description=__doc__.split("\n")[0])
    parser.add_argument("query", help="the words to look for, Arabic or English")
    parser.add_argument("--book", action="append", default=[], help="search only this book (repeatable)")
    parser.add_argument("--limit", type=int, default=None, help="how many passages (default: the app's)")
    parser.add_argument("--json", action="store_true", help="print the hits as the API's JSON shape")
    parser.add_argument("--explain", action="store_true", help="print the search terms and step timings")
    return parser.parse_args(argv)


def _timed(query: str, limit: int | None, books: tuple[str, ...]):
    """`search.search`, with the milliseconds each of its steps took."""
    timings: dict[str, float] = {}
    clock = time.perf_counter()

    def lap(step: str) -> None:
        nonlocal clock
        now = time.perf_counter()
        timings[step] = (now - clock) * 1000
        clock = now

    hits = search.search(query, limit, books, lap)
    return hits, timings, search.expand_query(query)


def _underlined(text: str, spans) -> str:
    """The text with each marked word in [brackets], short enough for one line."""
    out, at = [], 0
    for start, end in spans:
        out += [text[at:start], "[", text[start:end], "]"]
        at = end
    out.append(text[at:])
    line = "".join(out).replace("\n", " ")
    return line if len(line) <= 200 else line[:200] + "…"


if __name__ == "__main__":
    raise SystemExit(main())
