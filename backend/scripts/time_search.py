"""How long a search actually takes, as numbers rather than an opinion.

    python backend/scripts/time_search.py
    python backend/scripts/time_search.py --runs 3 --out timings-offline.json

Runs a fixed list of Arabic queries against each search path and prints the
median and the 90th percentile in milliseconds. Run it once with the internet
on and once with it off: the offline run is not a failed run, it is the number
that says how long a reader waits before the app gives up, which is governed by
`quran_timeout_seconds` in backend/config.py.

The queries are fixed on purpose. A timing you can compare next month is worth
more than a timing of whatever was typed today, so changing this list makes the
old numbers incomparable; add to the end rather than editing what is there.

One number here is not the app's number: the first dictionary query includes
reading the 5 MB file, about 1.2 seconds, because this script does not run the
server's startup. The running app reads it while it is starting, before anyone
can search, so nobody ever waits for it. Read the first row of the dictionary
sections as "load plus search" and the rest as the search alone.

Nothing here touches the running server: it imports the same functions the
server calls, so what is measured is the search itself and not the HTTP round
trip to localhost.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services import dictionary_service  # noqa: E402, needs the path above
from backend.config import get_settings  # noqa: E402
from backend.services import quran_search  # noqa: E402

# Ten words a learner would really search: common Qur'anic nouns and verbs, one
# two-letter word (أب) because a trigram index cannot see those, and one word
# typed with its diacritics because that is how a beginner copies it out.
_ARABIC = [
    "الرحمن",
    "كتاب",
    "صبر",
    "علم",
    "نور",
    "رزق",
    "أب",
    "الصلاة",
    "غفور",
    "الرَّحِيم",
]

# For the dictionary's other half. Ordinary English, one very common word ("the")
# because it matches almost every definition and is the slow case.
_ENGLISH = ["book", "write", "mercy", "light", "the"]


def _clear_dictionary_cache() -> None:
    """Forget the repeat-search cache, so what is timed is a real search.

    Without this the second run of a query is answered from memory in about a
    microsecond and the median says the dictionary is instant. That number is
    true of a repeat search and false of the first one, and the first one is the
    one a reader waits for.
    """
    dictionary_service._arabic_matches.cache_clear()
    dictionary_service._english_matches.cache_clear()


def _pinned(source: str):
    """Search with quran_search_source set to one value, as a .env would set it."""
    def call(query: str):
        get_settings().quran_search_source = source
        return quran_search.search(query, 20)
    return call


def _time(call, argument: str, runs: int, before=None) -> dict:
    """One query, run `runs` times. Errors are timed too, they cost a wait."""
    elapsed: list[float] = []
    results = 0
    error = ""
    for _ in range(runs):
        if before:
            before()
        started = time.perf_counter()
        try:
            results = len(call(argument))
        except Exception as exc:  # noqa: BLE001, any failure is a timing worth having
            error = f"{type(exc).__name__}: {exc}"
        elapsed.append((time.perf_counter() - started) * 1000)

    ordered = sorted(elapsed)
    return {
        "query": argument,
        "results": results,
        "error": error,
        "median_ms": round(statistics.median(ordered), 1),
        "p90_ms": round(ordered[min(int(len(ordered) * 0.9), len(ordered) - 1)], 1),
    }


def _run(name: str, call, queries: list[str], runs: int, before=None) -> dict:
    print(f"\n{name}")
    rows = [_time(call, query, runs, before) for query in queries]
    for row in rows:
        note = f"  {row['error']}" if row["error"] else ""
        print(f"  {row['query']:<12} {row['median_ms']:>8.1f} ms median"
              f"  {row['p90_ms']:>8.1f} ms p90  {row['results']:>3} results{note}")

    medians = [row["median_ms"] for row in rows]
    overall = round(statistics.median(medians), 1)
    print(f"  {'ALL':<12} {overall:>8.1f} ms median of medians")
    return {"path": name, "runs": runs, "overall_median_ms": overall, "queries": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=5, help="How many times each query is run")
    parser.add_argument("--out", default="search-timings.json", help="Where the numbers are written")
    args = parser.parse_args()

    # The queries are Arabic and a Windows console defaults to cp1252, which
    # cannot print them: without this the script dies on its first result line
    # having already paid for the searches.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.runs < 1:
        print("--runs must be at least 1")
        return 1

    # Each way of answering is asked for through the setting a reader would use,
    # not by reaching inside the module for one of its two halves. That keeps the
    # script honest: it times what the app can actually be told to do.
    paths = [
        _run("quran search (online, Quran.com)", _pinned("online"), _ARABIC, args.runs),
        _run("quran search (local index, no network)", _pinned("local"), _ARABIC, args.runs),
        _run("quran search (auto, whichever answers)", _pinned("auto"), _ARABIC, args.runs),
        _run("dictionary search (Arabic side)",
             dictionary_service.search_arabic, _ARABIC, args.runs, _clear_dictionary_cache),
        _run("dictionary search (English side)",
             dictionary_service.search_english, _ENGLISH, args.runs, _clear_dictionary_cache),
    ]

    Path(args.out).write_text(json.dumps(paths, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWritten to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
