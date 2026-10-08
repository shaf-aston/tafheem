"""Say every line the app can speak once ahead of time, so a learner's tap plays a stored sound.

A line said for the first time takes 1-4 s to make on the server's CPU; a stored
one comes back in under 0.2 s. This walks every `arabic` text in the Colloquial
course, every quiz word with no reciter's recording, and every quiz example
sentence, and asks services/speech.py for each, which stores what it makes.
Stopping and running again is safe: a stored line costs a file read. It runs
in its own process, so on the live server it shares the CPU with learners'
presses rather than giving way to them.

    python -m backend.scripts.premake_speech [--limit N] [--again LETTERS]

`--again` makes once more every line holding any of LETTERS, for when the way
those letters are said has changed (2026-10-08: the small alif, `--again ٰ`).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from backend.config import get_settings
from backend.services import speech

COURSE = Path(__file__).resolve().parents[1] / "data" / "colloquial"
# The quiz's files, as the page loads them (frontend lib/speak.js and QuizExample.jsx).
WORDS = Path(__file__).resolve().parents[2] / "frontend" / "public" / "words"


def spoken_sentence(arabic: str) -> str:
    """An example sentence as QuizExample.jsx hands it to the voice: without the braces round its word."""
    return arabic.replace("{", "").replace("}", "")


def lines() -> list[str]:
    """Every distinct text the server voice can be asked for, tidied as the route tidies it."""
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

    # A quiz word with a reciter's recording plays that from quran.com, never this voice.
    recorded = json.loads((WORDS / "word_audio.json").read_text(encoding="utf-8"))
    for word in json.loads((WORDS / "words.json").read_text(encoding="utf-8"))["words"]:
        if word["ar"] not in recorded:
            found.add(speech.tidy(word["ar"]))
    for arabic, _english in json.loads((WORDS / "sentences.json").read_text(encoding="utf-8"))["sentences"].values():
        found.add(speech.tidy(spoken_sentence(arabic)))
    # Whatever a reciter says (lib/speak.js tries recordings first) never reaches this voice.
    found -= set(recorded)
    return sorted(text for text in found if text and len(text) <= get_settings().speech_max_chars)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="stop after this many lines (0 = all)")
    parser.add_argument("--again", default="", help="make again every line holding any of these letters")
    args = parser.parse_args()
    todo = lines()
    todo = todo[:args.limit] if args.limit > 0 else todo
    for text in todo:
        if any(letter in text for letter in args.again):
            speech.forget(text)
    start = time.monotonic()
    for done, text in enumerate(todo, 1):
        speech.say(text, pressed=False)
        if done % 100 == 0 or done == len(todo):
            spent = time.monotonic() - start
            print(f"{done}/{len(todo)} lines, {spent / 60:.0f} min, ~{spent / done * (len(todo) - done) / 3600:.1f} h left", flush=True)


if __name__ == "__main__":
    main()
