"""Make the one-line English gist of every Lisan al-Arab and Taj al-Arus entry.

    python backend/scripts/dictionary/backfill_lexicon_gists.py             # both books
    python backend/scripts/dictionary/backfill_lexicon_gists.py --limit 20  # try twenty first
    python backend/scripts/dictionary/backfill_lexicon_gists.py --book lisan

Reads each entry from data/lexicons.db (build_lexicons.py makes it) and asks
the app's own AI backend for one line saying what the entry covers, kept in
data/dictionary/lexicon_gists.json. The shelf shows the line under the book's
name; a root with no line shows none.

Safe to stop at any point: it skips whatever is already kept. A run of failures
in a row ends it (a spent daily allowance looks like that); one alone does not.
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.services import ai as ai_service  # noqa: E402, needs the path above
from backend.services.dictionary import lexicon_gists, lexicons  # noqa: E402

TITLES = {"lisan": "Lisan al-Arab", "taj": "Taj al-Arus"}


def entries_to_do(books: list[str], limit: int | None) -> list[tuple[str, str, str]]:
    """(book, root, entry) for every entry with no line kept yet. A book that
    returns to a root in a later volume is asked once, on its first entry."""
    todo, seen = [], set()
    for book in books:
        for root, text in lexicons.entries_of_book(book):
            if (book, root) in seen or lexicon_gists.get(book, root):
                continue
            seen.add((book, root))
            todo.append((book, root, text))
            if limit and len(todo) >= limit:
                return todo
    return todo


def make(book: str, root: str, text: str) -> None:
    gist = str(ai_service.gist_lexicon_entry(TITLES[book], root, text).get("gist", "")).strip()
    if not gist:
        raise ValueError("the AI answered with nothing")
    lexicon_gists.put(book, root, gist)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", choices=lexicon_gists.BOOKS, help="only this book")
    parser.add_argument("--limit", type=int, help="stop after this many entries")
    parser.add_argument("--pause", type=float, default=0.0, help="seconds between entries")
    parser.add_argument("--give-up-after", type=int, default=3, help="stop after this many failures in a row")
    parser.add_argument("--workers", type=int, default=4, help="entries asked at once")
    args = parser.parse_args()

    if not ai_service.is_ai_available():
        print("No AI backend is reachable. Set GROQ_API_KEY in .env, or run:  ollama pull qwen2.5:3b")
        return 1
    if lexicons.status() != lexicons.READY:
        print("data/lexicons.db is not built, run build_lexicons.py first.")
        return 1

    todo = entries_to_do([args.book] if args.book else list(lexicon_gists.BOOKS), args.limit)
    print(f"{len(todo)} to go, using {ai_service.get_backend_name()}")

    def run(book, root, text):
        make(book, root, text)
        if args.pause:
            time.sleep(args.pause)

    done, failed, in_a_row = 0, 0, 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run, *job): job[:2] for job in todo}
        for future in as_completed(futures):
            book, root = futures[future]
            if future.exception():
                print(f"\n{book} {root}: {future.exception()}")
                failed += 1
                in_a_row += 1
                if in_a_row >= args.give_up_after:
                    print(f"\n{in_a_row} in a row failed, stopping. Run again later; what is done is kept.")
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                continue
            done += 1
            in_a_row = 0
            print(f"\r{done}/{len(todo)}  {book} {root}   ", end="", flush=True)

    print(f"\n{done} lines made" + (f", {failed} failed" if failed else "") + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
