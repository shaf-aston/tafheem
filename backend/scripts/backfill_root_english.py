"""Put the Maqayees entries into English ahead of time, so nobody waits.

    python backend/scripts/backfill_root_english.py            # the whole book
    python backend/scripts/backfill_root_english.py --limit 20 # try twenty first

Reads every entry the book has and asks the app's own AI backend to put it into
plain English, keeping each answer in data/maqayees/english_entries.json. The
card then shows English the moment it is opened, with no call and no wait.

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
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import get_settings  # noqa: E402, needs the path above
from backend.services import ai as ai_service  # noqa: E402
from backend.services import root_english, root_meaning  # noqa: E402


def entries_to_do(limit: int | None) -> list[tuple[str, str]]:
    """The roots with an entry the book prints and no English kept yet."""
    todo = []
    for root in root_meaning.roots():
        body = (root_meaning.lookup(root) or {}).get("body", "")
        if body and not root_english.get(root):
            todo.append((root, body))
    return todo[:limit] if limit else todo


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
    parser.add_argument(
        "--model",
        help="use this model instead of the configured one. Each model has its own "
             "daily allowance, so once one is spent the book can carry on under "
             "another rather than waiting for tomorrow.",
    )
    args = parser.parse_args()

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

    todo = entries_to_do(args.limit)
    print(f"{root_english.count()} already done, {len(todo)} to go, using {ai_service.get_backend_name()}")

    done, failed, in_a_row = 0, 0, 0
    for root, body in todo:
        try:
            answer = ai_service.explain_root_entry(root, body)
            english = str(answer.get("english", "")).strip()
        except Exception as exc:  # noqa: BLE001, one bad entry is not the end
            print(f"\n{root}: {exc}")
            english = ""

        if not english:
            failed += 1
            in_a_row += 1
            # A run of failures is what a spent daily allowance looks like. One
            # on its own is a bad answer, and the next entry may be fine; a
            # run of hours must not end on the first of those.
            if in_a_row >= args.give_up_after:
                print(f"\n{in_a_row} in a row failed, stopping there. Run this again "
                      "later; everything done so far is kept.")
                break
            continue

        root_english.put(root, english)
        done += 1
        in_a_row = 0
        print(f"\r{done}/{len(todo)}  {root}   ", end="", flush=True)
        if args.pause:
            time.sleep(args.pause)

    print(f"\n{done} entries put into English"
          + (f", {failed} could not be" if failed else "")
          + f". {root_english.count()} kept in total, "
          f"{len(todo) - done - failed} of this run left.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
