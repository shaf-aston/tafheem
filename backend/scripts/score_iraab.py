"""How often the typed-sentence analyser names a word's role the way a book does.

The answer key is either the book examples the Tarkeeb view draws (data/tarkeeb/examples):
every word there carries the role the book gave it; or --set checked, fresh
sentences no rule was written against (data/nahw_rules/checked_sentences.json). Each sentence goes through
the same path a typed one does, morphology then rule_engine, and each word's
role is compared by family (data/nahw_rules/answer_key.json), since the app
writes "مبتدأ (مرفوع)" where the book writes مُبْتَدَأٌ.

Offline by default. --api scores what the running app returns instead, AI
fallback included, which is what a reader actually sees; it spends AI calls.

Only roles are scored: the books record no case field, and reading case back
off the harakat would score the reader's vowels, not the analyser.

    venv/Scripts/python -m backend.scripts.score_iraab
    venv/Scripts/python -m backend.scripts.score_iraab --api http://127.0.0.1:8000 --show 20
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from collections import Counter
from pathlib import Path

from backend.services import morphology, rule_engine, syntax
from backend.services.arabic_text import bare_letters, words

DATA = Path(__file__).resolve().parent.parent / "data"
KEY = json.loads((DATA / "nahw_rules" / "answer_key.json").read_text(encoding="utf-8"))
TERMS = sorted(
    ((bare_letters(term), family) for family, terms in KEY["families"].items() for term in terms),
    key=lambda pair: -len(pair[0]),
)


def family(role: str | None) -> str | None:
    """The family a role belongs to, by the longest term it contains."""
    folded = bare_letters(role or "")
    return next((fam for term, fam in TERMS if term in folded), None)


def book_sentences() -> list[dict]:
    """Every book example as its sentence and the book's role for each word."""
    out = []
    for path in sorted((DATA.parent / KEY["sources"]["books"]).glob("*.json")):
        for ex in json.loads(path.read_text(encoding="utf-8"))["examples"]:
            roles: dict[int, str] = {}

            def walk(node: dict) -> None:
                if node.get("word") is not None:
                    roles[node["word"]] = node.get("role") or ""
                for child in (node.get("children") or []) + (node.get("parts") or []):
                    walk(child)

            walk(ex["tree"])
            out.append({"id": ex["id"], "sentence": ex["sentence"], "words": ex["words"],
                        "roles": [roles.get(i, "") for i in range(len(ex["words"]))]})
    return out


def checked_sentences() -> list[dict]:
    """Fresh sentences written for testing, kept only where three separate
    readings agreed on every word; nothing was tuned on them."""
    path = DATA.parent / KEY["sources"]["checked"]
    return [{"id": f"c{i}", **ex} for i, ex in enumerate(json.loads(path.read_text(encoding="utf-8")), 1)]


SETS = {"books": book_sentences, "checked": checked_sentences}


def analysed(sentence: str, api: str | None) -> list[dict]:
    if not api:
        # the same two steps the route runs: the rules, then the parser over them
        rules = rule_engine.analyze(sentence, morphology.analyze_sentence(sentence))
        return syntax.with_parser_roles(rules, syntax.read(sentence)["roles"])["words"]
    req = urllib.request.Request(f"{api}/api/analyze", data=json.dumps({"sentence": sentence}).encode(),
                                 headers={"content-type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())["words"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", help="score the running app at this address instead of the offline path")
    parser.add_argument("--set", choices=SETS, default="books", help="which answer key to score against")
    parser.add_argument("--show", type=int, default=10, help="how many wrong words to print")
    args = parser.parse_args()
    if args.show < 0:
        parser.error("--show cannot be negative")

    right = total = 0
    unmapped, misaligned, confusions, misses = Counter(), [], Counter(), []
    for ex in SETS[args.set]():
        got = analysed(ex["sentence"], args.api)
        if [bare_letters(w) for w in words(ex["sentence"])] != [bare_letters(w["word"]) for w in got] \
                or len(got) != len(ex["words"]):
            misaligned.append(ex["id"])
            continue
        for word, want_role, mine in zip(ex["words"], ex["roles"], got):
            want = family(want_role)
            if want is None:
                unmapped[want_role] += 1
                continue
            have = family(mine.get("role"))
            total += 1
            if have == want:
                right += 1
            else:
                confusions[(want, have)] += 1
                misses.append(f"{ex['id']:>10}  {word}  book: {want_role}  app: {mine.get('role')}")

    print(f"Roles right: {right}/{total} = {right / total:.0%}" if total else "Nothing scored.")
    print(f"Sentences skipped, words did not line up: {len(misaligned)} {misaligned[:10]}")
    if unmapped:
        print(f"Book roles with no family (not scored): {dict(unmapped)}")
    print("Most common mix-ups (book -> app):")
    for (want, have), n in confusions.most_common(10):
        print(f"  {n:>3}  {want} -> {have}")
    print(*misses[: args.show], sep="\n")


if __name__ == "__main__":
    main()
