"""
List the phrases of a colloquial unit that hold a word no reference knows.

    python -X utf8 -m backend.scripts.check_colloquial_words --unit 1

Only reports, in Arabic: it never edits a unit, and a listed phrase is a question
for a native speaker, not an error. The matching and the references are in
services/colloquial/wordcheck.py and its references.json.
"""
import argparse
import json
import re

from backend.config import data_path
from backend.services.colloquial import wordcheck


def main():
    ask = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ask.add_argument("--unit", type=int, required=True)
    ask.add_argument("--dialect", default="damascene")
    ask.add_argument("--source", action="append", help="limit to these references (default: all)")
    args = ask.parse_args()

    unit_file = data_path("colloquial_dir") / args.dialect / f"unit-{args.unit:02d}.json"
    unit = json.loads(unit_file.read_text(encoding="utf8"))
    phrases = [p for lesson in unit["lessons"] for p in lesson["phrases"]]
    words = {w for p in phrases for w in re.findall(r"[A-Za-z0-9']+", p["transliteration"])}
    lost = set(wordcheck.missing(sorted(words), args.source))

    print(f"{len(words)} distinct words, {len(lost)} in no reference")
    for p in phrases:
        if lost & set(re.findall(r"[A-Za-z0-9']+", p["transliteration"])):
            print(p["arabic"])


if __name__ == "__main__":
    main()
