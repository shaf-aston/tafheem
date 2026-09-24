"""Score the tarkeeb rules against the scholars' treebank, role by role.

The rules only run where the treebank is silent, so the treebank is the one
answer key there is for them. A claim is right when the treebank has a unit
with the same kind of role starting at the same word; spans are not compared,
because the two disagree about where attachments end. A jar-majroor the rules
call khabar and the treebank files as مُتَعَلِّقٌ (its khabar left unwritten) is a
difference of convention, counted apart.

Run from the project root, before and after a rule change:
    venv/Scripts/python backend/scripts/score_tarkeeb.py
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services import quran_corpus, tarkeeb, tarkeeb_store  # noqa: E402

TERMS = tarkeeb._rules()["terms"]
EXACT = {TERMS[k]["ar"]: k for k in ("fail", "naib_fail", "mafool", "mubtada", "khabar")}
ATTACHED = "مُتَعَلِّقٌ"
LETTER = re.compile("[ء-ي]")
KINDS = ["fail", "naib_fail", "mafool", "mubtada", "khabar", "ism of governor", "khabar of governor"]


def kind(role: str | None) -> str | None:
    if not role:
        return None
    if role in EXACT:
        return EXACT[role]
    if role.startswith("اِسْمُ "):
        return "ism of governor"
    if role.startswith("خَبَرُ "):
        return "khabar of governor"
    return None


def units(node: dict, at, out: set, raw: set | None = None) -> list[int]:
    """(first word, kind) for every scored unit; `raw` also keeps the wording.
    Only the treebank's side reads a word's pieces: it files لَمُشْرِكُونَ's role there."""
    if "word" in node:
        words = [node["word"]]
        for part in node.get("parts", ()) if raw is not None else ():
            if (first := at(node["word"])) is not None:
                raw.add((first, part.get("role")))
                if k := kind(part.get("role")):
                    out.add((first, k))
    else:
        words = [w for child in node.get("children", ()) for w in units(child, at, out, raw)]
    if words and (first := at(min(words))) is not None:
        if k := kind(node.get("role")):
            out.add((first, k))
        if raw is not None:
            raw.add((first, node.get("role")))
    return words


def main() -> None:
    ayahs = quran_corpus._db().execute("SELECT DISTINCT surah, ayah FROM segment").fetchall()
    recorded, claimed, right, convention = Counter(), Counter(), Counter(), Counter()
    scored = 0
    for surah, number in ayahs:
        tree = tarkeeb_store.for_ayah(surah, number)
        if not tree or not tree.get("tree"):
            continue
        words = quran_corpus.tags_for_ayah(surah, number)
        # The treebank adds elided words in brackets; the corpus has none.
        written = [i for i, w in enumerate(tree["words"]) if not w.startswith("(") and LETTER.search(w)]
        if len(written) != len(words):
            continue
        scored += 1
        gold, gold_raw = set(), set()
        units(tree["tree"], dict(zip(written, range(len(words)))).get, gold, gold_raw)
        recorded.update(k for _, k in gold)
        claims: set = set()
        units(tarkeeb.tree_for(words)["tree"], lambda i: i, claims)
        for first, k in claims:
            claimed[k] += 1
            if (first, k) in gold:
                right[k] += 1
            elif "khabar" in k and (first, ATTACHED) in gold_raw:
                convention[k] += 1

    print(f"{scored} ayahs scored\n")
    print(f"{'role':20} {'recorded':>9} {'claimed':>8} {'right':>6} {'of claims':>10} {'of recorded':>12}")
    for k in KINDS:
        share = f"{right[k] / claimed[k]:.0%}" if claimed[k] else "-"
        found = f"{right[k] / recorded[k]:.0%}" if recorded[k] else "-"
        print(f"{k:20} {recorded[k]:9} {claimed[k]:8} {right[k]:6} {share:>10} {found:>12}")
    total, good, jm = sum(claimed.values()), sum(right.values()), sum(convention.values())
    print(f"\n{good} of {total} claims right ({good / total:.1%}), "
          f"{good / sum(recorded.values()):.1%} of recorded roles found; "
          f"{total - good - jm} wrong, {jm} more are jar-majroor khabars the treebank files as {ATTACHED}")


if __name__ == "__main__":
    main()
