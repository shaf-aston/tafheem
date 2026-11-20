"""Say every line the app can speak once ahead of time, so a learner's tap plays a stored sound.

A line said for the first time takes 1-4 s to make on the server's CPU; a stored
one comes back in under 0.2 s. This walks every `arabic` text in the Colloquial
course (each dialect by its own speaker), every quiz word with no reciter's recording, and every quiz example
sentence, and asks services/speech.py for each, which stores what it makes.
Stopping and running again is safe: a stored line costs a file read. It runs
in its own process, so on the live server it shares the CPU with learners'
presses rather than giving way to them.

    python -m backend.scripts.speech.premake_speech [--limit N] [--again LETTERS]

`--again` makes once more every line holding any of LETTERS, for when the way
those letters are said has changed (2026-10-08: the small alif, `--again ٰ`).
"""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.config import get_settings
from backend.services import speech
from backend.services.colloquial import loader as colloquial

# The quiz's files, as the page loads them (frontend lib/speech/speak.js and QuizExample.jsx).
WORDS = Path(__file__).resolve().parents[3] / "frontend" / "public" / "words"


def spoken_sentence(arabic: str) -> str:
    """An example sentence as QuizExample.jsx hands it to the voice: without the braces round its word."""
    return arabic.replace("{", "").replace("}", "")


def said() -> list[tuple[str, str | None]]:
    """Every distinct (text, voice) the server can be asked for, tidied as the route tidies it.
    A dialect's lines go to its own speakers (colloquial.voice_of: a dialogue line by its cast,
    the rest by the dialect's first man), everything else to the usual order (None)."""
    found: set[tuple[str, str | None]] = set()

    def walk(value, accent: str) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("arabic"), str):
                found.add((speech.tidy(value["arabic"]), colloquial.voice_of(accent, value.get("cast"))))
            value = list(value.values())
        if isinstance(value, list):
            for item in value:
                walk(item, accent)

    # The course as the page gets it, so a line's cast is the one the page sends.
    for dialect in colloquial.catalogue()["dialects"]:
        for card in dialect["units"]:
            if card["written"]:
                walk(colloquial.unit(dialect["key"], card["unit"]), dialect["key"])

    # A quiz word with a reciter's recording plays that from quran.com, never this voice.
    recorded = json.loads((WORDS / "word_audio.json").read_text(encoding="utf-8"))
    for word in json.loads((WORDS / "words.json").read_text(encoding="utf-8"))["words"]:
        if word["ar"] not in recorded:
            found.add((speech.tidy(word["ar"]), None))
    for arabic, _english in json.loads((WORDS / "sentences.json").read_text(encoding="utf-8"))["sentences"].values():
        found.add((speech.tidy(spoken_sentence(arabic)), None))
    # Whatever a reciter says (lib/speech/speak.js tries recordings first, with no accent) never reaches this voice.
    found = {(text, voice) for text, voice in found if voice or text not in recorded}
    return sorted((pair for pair in found if pair[0] and len(pair[0]) <= get_settings().speech_max_chars), key=lambda p: (p[0], p[1] or ""))


def lines() -> list[str]:
    """Every distinct text the server can be asked to say, by any voice."""
    return sorted({text for text, _voice in said()})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="stop after this many lines (0 = all)")
    parser.add_argument("--workers", type=int, default=6,
                        help="lines asked at once; the online voices answer in parallel, this machine's own voice still takes one at a time")
    parser.add_argument("--again", default="", help="make again every line holding any of these letters")
    args = parser.parse_args()
    todo = said()
    todo = todo[:args.limit] if args.limit > 0 else todo
    # Dialect lines (online voices, in parallel) first; this machine's own voice takes one line
    # at a time, so its lines mixed in left every worker waiting on it (2026-11-20: 60 lines/min, not 420).
    todo.sort(key=lambda pair: pair[1] is None)
    for text, _voice in todo:
        if any(letter in text for letter in args.again):
            speech.forget(text)
    if args.workers < 1:
        parser.error("--workers must be 1 or more")
    start = time.monotonic()
    already = sum(any(speech.stored(v, text).exists() for v in speech.order(voice)) for text, voice in todo)
    print(f"{already}/{len(todo)} lines already stored", flush=True)

    def make(pair: tuple[str, str | None]) -> None:
        try:
            speech.say(pair[0], pressed=False, first=pair[1])
        except RuntimeError:  # no voice right now: a tap makes it later, the run goes on
            print(f"skipped {pair[0]!r}: no voice could say it", flush=True)

    with ThreadPoolExecutor(args.workers) as pool:
        for done, _ in enumerate(pool.map(make, todo), 1):
            if done % 100 == 0 or done == len(todo):
                spent = time.monotonic() - start
                print(f"{done}/{len(todo)} lines, {spent / 60:.0f} min, ~{spent / done * (len(todo) - done) / 3600:.1f} h left", flush=True)

if __name__ == "__main__":
    main()
