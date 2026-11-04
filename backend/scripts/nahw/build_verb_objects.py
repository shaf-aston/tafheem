"""Build data/nahw_rules/verb_objects.json: the verbs that take a noun as their object.

A describing word in nasb after a verb and its doer is a hal (جاء زيد راكبا) unless the
verb wants an object and has none. Then the word is that object, standing for the noun it
describes, left out (Ibn Aqil V3 p205: يجوز حذف المنعوت وإقامة النعت مقامه … أن اعمل سابغات
أي دروعا سابغات). Whether a verb wants one is read off how the Qur'an uses it, from the same
treebank build_tarkeeb.py reads: a verb is kept when a noun is its مفعول به in at least
SHARE of its uses. A pronoun object does not count: جَاءَهُمْ is no sign that جاء زيد راكبا
wants a thing named after it.

    venv/Scripts/python backend/scripts/nahw/build_verb_objects.py Quranic.csv
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.scripts.nahw.build_tarkeeb import read_rows  # noqa: E402
from backend.services.nahw.book import RULES, book_spelling  # noqa: E402

SHARE = Fraction(1, 3)
FEWEST_USES = 3  # fewer and one odd ayah decides
OUT = RULES / "verb_objects.json"


def counts(treebank: Path) -> tuple[Counter, Counter]:
    """Each verb lemma's uses, and how many of them have a noun as their object."""
    uses: Counter[str] = Counter()
    objects: Counter[str] = Counter()
    for sentences in read_rows(treebank).values():
        for rows in sentences:
            by_id = {row["token_id"]: row for row in rows}
            for row in rows:
                if row["pos"] == "V":
                    uses[book_spelling(row["lemma_ar"])] += 1
                head = by_id.get(row["ref_token_id"])
                if row["rel_label"] == "Obj" and row["pos"] != "PRON" and head and head["pos"] == "V":
                    objects[book_spelling(head["lemma_ar"])] += 1
    return uses, objects


def build(treebank: Path) -> None:
    uses, objects = counts(treebank)
    verbs = sorted(v for v, n in uses.items() if v and n >= FEWEST_USES and objects[v] >= SHARE * n)
    OUT.write_text(json.dumps({
        "about": f"Verbs a noun is the object of in at least {SHARE} of their Qur'an uses "
                 f"(at least {FEWEST_USES}); made by scripts/nahw/build_verb_objects.py from the Quranic Treebank.",
        "verbs": verbs}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(verbs)} of {len(uses)} verbs take a noun object")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: build_verb_objects.py <Quranic.csv>")
    build(Path(sys.argv[1]))
