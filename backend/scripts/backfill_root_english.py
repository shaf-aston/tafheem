"""Put the Maqayees entries into English ahead of time, so nobody waits.

    python backend/scripts/backfill_root_english.py            # the whole book
    python backend/scripts/backfill_root_english.py --limit 20 # try twenty first
    python backend/scripts/backfill_root_english.py --lines    # one English line per Arabic line

Reads every entry the book has and asks the app's own AI backend to put it into
plain English, keeping each answer in data/maqayees/english_entries.json. The
card then shows English the moment it is opened, with no call and no wait.

With --lines it makes the Line by line view instead: every line of the rest of
each entry, in chunks the model can read, into data/maqayees/english_lines.json.
--workers sets how many roots are asked at once, in either mode.

Safe to stop at any point: it skips whatever has already been done, so running
it again picks up where it left off. Nothing here writes to the book itself.

A run takes hours and nobody is watching it, so one bad answer does not end it;
only a run of them does, which is what a used-up daily allowance looks like.

Which AI it uses is not this script's decision, it is whichever one the app is
configured for, so the answers match what the app would have produced anyway.
A model that stops answering ends the run and says how far it got, rather than
filling the file with failures.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import get_settings  # noqa: E402, needs the path above
from backend.services import ai as ai_service  # noqa: E402
from backend.services import root_english, root_gloss, root_meaning  # noqa: E402


def entries_to_do(limit: int | None, by_line: bool) -> list[tuple[str, str | list[str]]]:
    """The roots with an entry the book prints and no English kept yet, each
    with what to put into English: the body, or every line after the origin sense."""
    todo = []
    for root in root_meaning.roots():
        entry = root_meaning.lookup(root) or {}
        if by_line:
            lines, _ = root_gloss.line_budget(root_gloss.rest_of(entry), sys.maxsize)
            # The shipped file only: English a reader's press kept still has to ship.
            if lines and not root_english.has_shipped_lines(root, len(lines)):
                todo.append((root, lines))
        elif entry.get("body") and not root_english.get(root):
            todo.append((root, entry["body"]))
    return todo[:limit] if limit else todo


def chunks(lines: list[str], budget: int) -> list[list[str]]:
    """Whole lines grouped so each group stays within `budget` characters. A
    line longer than that is its own group: half a line is not translatable."""
    groups: list[list[str]] = []
    spent = 0
    for line in lines:
        if not groups or spent + len(line) > budget:
            groups.append([])
            spent = 0
        groups[-1].append(line)
        spent += len(line)
    return groups


max_waits = 20  # set from --max-waits


def ask_patiently(func, *args):
    """Call the AI; a rate limit is a wait, never a failure. The per-minute
    allowance refills, and the backend's own short retries do not outlast it."""
    for _ in range(max_waits + 1):
        try:
            return func(*args)
        except Exception as exc:  # noqa: BLE001
            text = str(exc)
            if "rate_limit" not in text and "429" not in text:
                raise
            found = re.search(r"try again in ([\d.]+)(ms|s)", text)
            seconds = (float(found[1]) / (1000 if found[2] == "ms" else 1)) if found else 15
            print(f"\nrate limit, waiting {seconds + 1:.1f}s", flush=True)
            time.sleep(seconds + 1)
    raise RuntimeError("still rate limited after waiting")


def make_prose(root: str, body: str) -> None:
    english = str(ask_patiently(ai_service.explain_root_entry, root, body).get("english", "")).strip()
    if not english:
        raise ValueError("the AI answered with nothing")
    root_english.put(root, english)


def english_for(root: str, chunk: list[str]) -> list[str]:
    """One English line per line of `chunk`. A model that keeps miscounting a
    chunk is asked about each half instead, down to single lines."""
    for _ in range(2):  # a miscounted answer gets one more go
        got = ask_patiently(ai_service.explain_root_entry_lines, root, chunk).get("lines")
        if (isinstance(got, list) and len(got) == len(chunk)
                and all(isinstance(g, str) and g.strip() for g in got)):
            return got
    if len(chunk) == 1:
        raise ValueError("could not line up a single line")
    print(f"\nsplit {len(chunk)} lines", flush=True)
    half = len(chunk) // 2
    return english_for(root, chunk[:half]) + english_for(root, chunk[half:])


def make_lines(root: str, lines: list[str]) -> None:
    english: list[str] = []
    for chunk in chunks(lines, get_settings().root_entry_truncate_chars):
        english += english_for(root, chunk)
    root_english.put_lines(root, english, shipped=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="stop after this many entries")
    parser.add_argument(
        "--pause", type=float, default=0.0,
        help="seconds to wait between entries, for a service with a rate limit",
    )
    parser.add_argument(
        "--give-up-after", type=int, default=3,
        help="stop once this many entries in a row have failed",
    )
    parser.add_argument("--lines", action="store_true", help="make the line-by-line English")
    parser.add_argument("--workers", type=int, default=4, help="roots asked at once")
    parser.add_argument(
        "--max-waits", type=int, default=20,
        help="rate-limit waits allowed per call before it counts as a failure",
    )
    parser.add_argument(
        "--model",
        help="use this model instead of the configured one. Each model has its own "
             "daily allowance, so once one is spent the book can carry on under "
             "another rather than waiting for tomorrow.",
    )
    parser.add_argument(
        "--account", type=int, default=0,
        help="which Groq account to spend: 0 is the shared key, 1.. the listening "
             "keys. The allowance is per account per model, so one process per "
             "pair runs the book in a day.",
    )
    args = parser.parse_args()
    global max_waits
    max_waits = args.max_waits

    if args.account:
        settings = get_settings()
        own = [key for key in settings.listening_keys if key != settings.groq_api_key.strip()]
        if args.account > len(own):
            print(f"Only {len(own)} listening keys are set, so there is no account {args.account}.")
            return 1
        settings.groq_api_key = own[args.account - 1]

    if args.model:
        # This process exists to run the book through once. Nothing else reads
        # the setting here, and the running app is untouched by it.
        get_settings().groq_model = args.model

    if not ai_service.is_ai_available():
        print("No AI backend is reachable, so nothing can be put into English.")
        print("Set GROQ_API_KEY in .env, or run:  ollama pull qwen2.5:3b")
        return 1

    # The book is read here, not at import: nothing has started a server, so
    # nothing has loaded it yet, and status() on an unread book says "missing".
    root_meaning.load()
    if root_meaning.status() != root_meaning.READY:
        print("The classical entries are not loaded, run build_root_meanings.py first.")
        return 1

    todo = entries_to_do(args.limit, args.lines)
    kept = root_english.count_lines if args.lines else root_english.count
    print(f"{kept()} already done, {len(todo)} to go, using {ai_service.get_backend_name()}")

    make = make_lines if args.lines else make_prose

    def run(root, payload):
        make(root, payload)
        if args.pause:
            time.sleep(args.pause)

    done, failed, in_a_row = 0, 0, 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run, root, payload): root for root, payload in todo}
        for future in as_completed(futures):
            root = futures[future]
            if future.exception():
                print(f"\n{root}: {future.exception()}")
                failed += 1
                in_a_row += 1
                # A run of failures is what a spent daily allowance looks like. One
                # on its own is a bad answer, and the next entry may be fine; a
                # run of hours must not end on the first of those.
                if in_a_row >= args.give_up_after:
                    print(f"\n{in_a_row} in a row failed, stopping there. Run this again "
                          "later; everything done so far is kept.")
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                continue
            done += 1
            in_a_row = 0
            print(f"\r{done}/{len(todo)}  {root}   ", end="", flush=True)

    print(f"\n{done} entries put into English"
          + (f", {failed} could not be" if failed else "")
          + f". {kept()} kept in total, "
          f"{len(todo) - done - failed} of this run left.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
