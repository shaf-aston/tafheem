"""How often the typed-sentence analyser names a word's role the way a book does.

The answer key is either the book examples the Tarkeeb view draws (data/tarkeeb/examples):
every word there carries the role the book gave it; or --set checked, fresh
sentences no rule was written against (data/nahw_rules/checked_sentences.json). Each sentence goes through
the route a typed one does (routed below), and each word's
role is compared by family (data/nahw_rules/answer_key.json), since the app
writes "مبتدأ (مرفوع)" where the book writes مُبْتَدَأٌ.

Offline by default. --api scores what the running app returns instead, which is
what a reader actually sees.

--set fresh is the yardstick for tuning: sentences with one exact role per typed
word (data/nahw_rules/fresh_sentences.json), split into "tune" (may be looked at)
and "hold" (never looked at while tuning). Offline it runs the router itself. It also counts
confident wrong answers, gaps, and places where a card and the picture disagree.
--set exam is the same format, a larger set per Tasheel chapter, written and keyed
blind by two separate readers and kept where they agreed; all held out.
--set hadith is the same format again: sayings found word for word in the hadith
collections, keyed the same way, some typed again without vowels.
--set rules has one new sentence per Tasheel rule (the "rule" field is its number
in the rule audit), in vocabulary the other sets do not use; a debatable key was dropped.
Rows in these two may carry "signs", the sign the book gives chosen words (word
index to sign), so the case line is scored as well as the role.

The other sets score roles only: the books record no case field, and reading case
back off the harakat would score the reader's vowels, not the analyser.

    venv/Scripts/python -m backend.scripts.score_iraab
    venv/Scripts/python -m backend.scripts.score_iraab --set fresh
    venv/Scripts/python -m backend.scripts.score_iraab --api http://127.0.0.1:8000 --show 20
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import urllib.request
from collections import Counter
from functools import partial
from pathlib import Path

from backend.services.arabic_text import bare_letters, strip_diacritics, words
from backend.services.nahw_book import book_file, family_cards, named_roles, role_table

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


def fresh_sentences() -> list[dict]:
    """One exact role per typed word; the vocabulary is fixed by the test."""
    return json.loads((DATA.parent / KEY["sources"]["fresh"]).read_text(encoding="utf-8"))


def held_out(name: str) -> list[dict]:
    """A set in the fresh format that nothing was tuned on, so all of it is "hold"."""
    rows = json.loads((DATA.parent / KEY["sources"][name]).read_text(encoding="utf-8"))
    return [{**row, "split": "hold"} for row in rows]


SETS = {"books": book_sentences, "checked": checked_sentences, "fresh": fresh_sentences,
        **{name: partial(held_out, name) for name in ("exam", "hadith", "rules")}}
# the sets keyed one exact role per typed word, scored by score_exact
EXACT = ("fresh", "exam", "hadith", "rules")


def sign_matches(have: str | None, want: str) -> bool:
    """The card's sign is the book's, or the book's followed by the card's note
    ("الواو، جمع مذكر سالم" answers الواو)."""
    have = strip_diacritics(have or "").strip()
    return have == want or have.startswith(want + "،")


def analysed(sentence: str, api: str | None) -> list[dict]:
    return routed(sentence, api)["words"]


def post(api: str, sentence: str) -> dict:
    # takes the bare address or the full .../api/analyze one
    base = api.rstrip("/").removesuffix("/api/analyze")
    req = urllib.request.Request(f"{base}/api/analyze", data=json.dumps({"sentence": sentence}).encode(),
                                 headers={"content-type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


def routed(sentence: str, api: str | None) -> dict:
    """The whole /api/analyze answer; offline, from the router itself."""
    if api:
        return post(api, sentence)
    from backend.models.analyze import AnalyzeRequest
    from backend.routers.analyze import analyze_sentence
    return asyncio.run(analyze_sentence(AnalyzeRequest(sentence=sentence))).model_dump()


def plain_role(role: str | None) -> str:
    """A role with harakat and any trailing note in brackets removed. A dash or
    anything else with no letter at all is the app saying "no role": blank."""
    plain = re.sub(r"\s*\(.*?\)", "", strip_diacritics(role or "")).strip()
    if plain.startswith("فعل "):  # the cards say "فعل ماض"; the key has one word for any verb
        return "فعل"
    return plain if any(c.isalpha() for c in plain) else ""


def tree_leaves(node: dict | None) -> list[dict]:
    if not node:
        return []
    own = [node] if node.get("word") is not None else []
    return own + [leaf for child in node.get("children") or [] for leaf in tree_leaves(child)]


# The picture names a unit's head by what it is to its unit; the card keeps the
# word's job in the sentence. These are the picture's own wording, not a clash:
# the roles roles.json gives no card colour (مضاف، موصوف، اسم موصول).
UNIT_WORDING = {role for role, (key, _) in role_table().items() if key is None}


def _particle_names() -> set[str]:
    """Every name a particle's family card or reading gives it (لا النافية، أداة استثناء): the
    picture's finer name for a card's حرف."""
    names = set()
    for _, card in family_cards():
        names |= {card["named"], card.get("chart", ""), *card.get("named_as", {}).values()}

    def leaves(node: dict) -> None:
        names.add(node.get("named", ""))
        for child in node.get("children", []):
            leaves(child)
    leaves(book_file("particle_tree.json")["tree"])
    return {plain_role(name) for name in names if name}


PARTICLE_NAMES = _particle_names()
HARF = plain_role(named_roles().harf)


def disagreements(cards: list[dict], tree: dict | None) -> list[tuple[int, str, str]]:
    """(word, card role, leaf role) for each tree leaf whose role differs from its card.

    Compared after stripping harakat. Not counted: a leaf or card with no role (a
    gap); a leaf in the picture's own wording (UNIT_WORDING); a leaf naming its card's role finer.
    """
    if not tree or len(tree.get("words") or []) != len(cards):
        return []
    out = []
    for leaf in tree_leaves(tree.get("tree")):
        card, pic = plain_role(cards[leaf["word"]].get("role")), plain_role(leaf.get("role"))
        if not card or not pic or pic in UNIT_WORDING:
            continue
        # the picture may name a governor finer than its card (حرف نصب for حرف), never otherwise
        if card == HARF and pic in PARTICLE_NAMES:
            continue
        if card != pic and not pic.startswith(card + " "):
            out.append((leaf["word"], card, pic))
    return out


def score_exact(name: str, api: str | None, show: int) -> None:
    """Score a set keyed one exact role per word. A blank card role is a gap; any other
    role that is not the key is confident wrong. Roles are compared exactly, harakat aside."""
    stats: dict[str, Counter] = {}
    bad_lines, clashes = [], []
    for ex in SETS[name]():
        answer = routed(ex["sentence"], api)
        cards, key = answer["words"], ex["key"]
        aligned = len(cards) == len(key)
        row = Counter(sentences=1)
        wrong = []
        if not aligned:
            wrong.append(f"words did not line up: got {len(cards)}, key {len(key)}")
        for i, want in enumerate(key):
            have = plain_role(cards[i].get("role")) if aligned else ""
            row["roles"] += 1
            if have == want:
                row["right"] += 1
            elif have:
                row["confident_wrong"] += 1
                wrong.append(f"{strip_diacritics(cards[i]['word'])}: {have} (key {want})")
            else:
                row["gaps"] += 1
                wrong.append(f"word {i + 1}: blank (key {want})")
        for i, want in ex.get("signs", {}).items() if aligned else ():
            card = cards[int(i)]
            row["signs"] += 1
            if sign_matches(card.get("sign"), want):
                row["signs_right"] += 1
            else:
                wrong.append(f"{strip_diacritics(card['word'])}: sign {card.get('sign') or 'none'} (key {want})")
        clash = disagreements(cards, answer.get("tree")) if aligned else []
        row["disagree"] = len(clash)
        clashes += [f"{ex['id']:>6}  {cards[i]['word']}: card {c}, tree {t}" for i, c, t in clash]
        row["whole"] = int(aligned and row["right"] == row["roles"])
        if wrong:
            bad_lines.append(f"{ex['id']:>6}  {ex['sentence']}  | " + " | ".join(wrong))
        for group in ("all", ex["split"], f"chapter: {ex['chapter']}"):
            stats.setdefault(group, Counter()).update(row)

    def line(name: str, c: Counter) -> str:
        pct = f"{c['right'] / c['roles']:.0%}" if c["roles"] else "-"
        signs = f"  signs {c['signs_right']}/{c['signs']}" if c["signs"] else ""
        return (f"{name:<28} roles {c['right']}/{c['roles']} = {pct:>4}  whole {c['whole']}/{c['sentences']}  "
                f"confident wrong {c['confident_wrong']}  gaps {c['gaps']}  card/tree disagree {c['disagree']}{signs}")

    print(f"{name.capitalize()} set" + (f" via {api}" if api else " (local)"))
    for name in ("all", "tune", "hold"):
        if name in stats:
            print(line(name, stats[name]))
    print("Per chapter:")
    for name in sorted(k for k in stats if k.startswith("chapter: ")):
        print(line(name[len("chapter: "):], stats[name]))
    print("Wrong sentences (got vs key):")
    print(*bad_lines, sep="\n")
    if show:
        print("Card/tree disagreements:")
        print(*clashes[:show], sep="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", help="score the running app at this address instead of the offline path")
    parser.add_argument("--set", choices=SETS, default="books", help="which answer key to score against")
    parser.add_argument("--show", type=int, default=10, help="how many wrong words to print")
    args = parser.parse_args()
    if args.show < 0:
        parser.error("--show cannot be negative")

    if args.set in EXACT:
        return score_exact(args.set, args.api, args.show)
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
