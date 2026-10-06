"""Say every Colloquial line once ahead of time, so a learner's tap plays a stored sound.

A line said for the first time takes 1-4 s to make on the server's CPU; a stored
one comes back in under 0.2 s. This walks every `arabic` text in the course and
asks services/speech.py for it, which stores what it makes. Stopping and running
again is safe: a stored line costs a file read.

    python -m backend.scripts.premake_speech [--limit N]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from backend.config import get_settings
from backend.services import speech

COURSE = Path(__file__).resolve().parents[1] / "data" / "colloquial"


def lines() -> list[str]:
    """Every distinct text the Colloquial tab can speak, tidied as the route tidies it."""
    found: set[str] = set()

    def walk(value) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("arabic"), str):
                found.add(speech.tidy(value["arabic"]))
            value = list(value.values())
        if isinstance(value, list):
            for item in value:
                walk(item)

    for unit in sorted(COURSE.glob("*/*.json")):
        walk(json.loads(unit.read_text(encoding="utf-8")))
    return sorted(text for text in found if text and len(text) <= get_settings().speech_max_chars)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="stop after this many lines (0 = all)")
    todo = lines()
    limit = parser.parse_args().limit
    todo = todo[:limit] if limit > 0 else todo
    start = time.monotonic()
    for done, text in enumerate(todo, 1):
        speech.say(text)
        if done % 100 == 0 or done == len(todo):
            spent = time.monotonic() - start
            print(f"{done}/{len(todo)} lines, {spent / 60:.0f} min, ~{spent / done * (len(todo) - done) / 3600:.1f} h left", flush=True)


if __name__ == "__main__":
    main()
