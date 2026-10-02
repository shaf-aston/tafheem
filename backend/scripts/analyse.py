"""Type a sentence, read what the Analyse page would show: one line per word, then the tree.

Sentences come from the command line, or one per line on stdin (safer for
Arabic in a Windows shell). Offline it runs the route itself with the AI step
off; --api asks a running app instead, e.g. the live one.

    venv/Scripts/python -m backend.scripts.analyse "لَمْ يَكْتُبْ الوَلَدُ"
    venv/Scripts/python -m backend.scripts.analyse --api https://tafheem-app.vercel.app < sentences.txt
    venv/Scripts/python -m backend.scripts.analyse --json "قُمْ"

The raw route with curl, the sentence in a UTF-8 file so the shell cannot mangle it:

    curl -s https://tafheem-app.vercel.app/api/analyze -H "content-type: application/json" --data-binary @s.json
    (s.json holds {"sentence": "..."})
"""
from __future__ import annotations

import argparse
import json
import sys

from backend.scripts.score_iraab import routed


def tree_lines(node: dict | None, words: list[str], depth: int = 0) -> list[str]:
    """The bracket tree, one bracket per line, indented by depth; a gap says so."""
    if not node:
        return []
    named = [part for part in (node.get("role"), node.get("label")) if part]
    name = " / ".join(named) or ("(gap)" if node.get("gap") else "")
    said = f"  {words[node['word']]}" if node.get("word") is not None else ""
    own = [f"{'  ' * depth}{name}{said}"]
    return own + [line for child in node.get("parts", []) + node.get("children", [])
                  for line in tree_lines(child, words, depth + 1)]


def report(answer: dict) -> str:
    rows = [answer["sentence"] + (f"   ({answer['summary']})" if answer.get("summary") else "")]
    for i, w in enumerate(answer["words"], 1):
        rows.append(" | ".join([str(i), w["word"], w.get("role") or "-", w.get("case") or "-",
                                w.get("sign") or "-", w.get("reason") or ""]))
    tree = answer.get("tree")
    rows += tree_lines(tree["tree"], tree["words"]) if tree else ["(no tree)"]
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("sentences", nargs="*", help="sentences to read; none means one per line on stdin")
    parser.add_argument("--api", help="ask the app at this address instead of running the route here")
    parser.add_argument("--json", action="store_true", help="print the raw answer")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    sentences = args.sentences or [line.strip() for line in sys.stdin if line.strip()]
    if not sentences:
        parser.error("give a sentence, or pipe some in")
    for sentence in sentences:
        answer = routed(sentence, args.api)
        print(json.dumps(answer, ensure_ascii=False, indent=1) if args.json else report(answer), end="\n\n")


if __name__ == "__main__":
    main()
