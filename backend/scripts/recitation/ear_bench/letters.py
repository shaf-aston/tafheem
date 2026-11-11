"""The ear letter by letter: which letters, with which vowel, it misses or wrongly reds.

Two tables from IqraEval scores already on disk (no model is run):

  slips caught  - each planted slip, filed by the letter it hit and that letter's
                  vowel (fatha, damma, kasra, long, shadda, or sukun after a
                  fatha/damma/kasra); caught = its word is red at the app's cut.
  right letters - every letter of every clean clip, filed the same way; red = the
                  ear's piece holding that letter is below the cut, so the letter
                  alone would turn a right word red.

    python -m backend.scripts.recitation.ear_bench.letters [--model repo@rev]
"""
from __future__ import annotations

import argparse
import difflib
import json
from collections import defaultdict
from pathlib import Path

from tokenizers import Tokenizer

from backend.config import get_settings
from backend.scripts.recitation.ear_bench.iqra import clips, slipped_word
from backend.scripts.recitation.ear_bench.spliced import META
from backend.scripts.recitation.paths import CHECKS
from backend.scripts.recitation.rescore_recitation import pieces_path
from backend.services.recitation import checker
from backend.services.recitation.spelling import LETTERS, as_heard

RECITE = Path(__file__).resolve().parents[4] / "frontend" / "src" / "config" / "recite.json"
REPORT = CHECKS / "letters-by-vowel-{}.txt"
FEW = 10  # a cell with fewer cases prints, marked, but is not ranked

SOUND = dict(zip("bt^jHxd*rzs$SDTZEgfqklmnhwy<", "بتثجحخدذرزسشصضطظعغفقكلمنهويء"))
SHORT = {"a": "fatha", "u": "damma", "i": "kasra"}
MARK = {"َ": "fatha", "ُ": "damma", "ِ": "kasra",
        "ً": "fatha", "ٌ": "damma", "ٍ": "kasra"}


def _vowel(p: str) -> str | None:
    """'fatha' / 'long fatha' / ... for a vowel sound, None for a consonant."""
    v = p.lower()
    if v in SHORT:
        return SHORT[v]
    if len(v) == 2 and v[0] == v[1] and v[0] in SHORT:
        return "long " + SHORT[v[0]]
    return None


def _letter(p: str) -> str:
    return SOUND.get(p[0], p)


def sound_context(sounds: list[str], k: int) -> str:
    """The vowel state of consonant sounds[k]: its own vowel, or sukun after the one before."""
    nxt = sounds[k + 1] if k + 1 < len(sounds) else None
    own = _vowel(nxt) if nxt else None
    shadda = "shadda " if len(sounds[k]) == 2 else ""
    if own:
        return shadda + own
    before = next((_vowel(s) for s in reversed(sounds[:k]) if _vowel(s)), None)
    return shadda + "sukun after " + (before.replace("long ", "") if before else "nothing")


def slip_cell(meant: list[str], said: list[str]) -> tuple[str, str, str]:
    """(kind, letter, context) of a clip's first change."""
    how, i1, i2, j1, j2 = next(o for o in difflib.SequenceMatcher(None, meant, said, autojunk=False).get_opcodes()
                               if o[0] != "equal" and not (o[0] == "delete" and o[1] >= len(meant) - 2))
    if how == "insert":
        return "sound added", " ".join(said[j1:j2]), "-"
    a = meant[i1]
    if _vowel(a):
        carrier = _letter(meant[i1 - 1]) if i1 else "-"
        to = _vowel(said[j1]) if how == "replace" and j1 < len(said) else None
        # a vs A is the same vowel, heavy or light (tafkheem); a vs aa is its length.
        kind = ("vowel dropped" if how == "delete" else "heavy/light" if to == _vowel(a)
                else "vowel length" if to and to.split()[-1] == _vowel(a).split()[-1] else "vowel swapped")
        return kind, carrier, f"{_vowel(a)} -> {to or 'none'}"
    kind = "letter dropped" if how == "delete" else "letter swapped"
    return kind, _letter(a), sound_context(meant, i1)


def written_context(word: str, i: int) -> str:
    """The vowel state of letter word[i] as the ear's spelling writes it."""
    marks = []
    j = i + 1
    while j < len(word) and word[j] not in LETTERS:
        marks.append(word[j])
        j += 1
    shadda = "shadda " if "ّ" in marks else ""
    own = next((MARK[m] for m in marks if m in MARK), None)
    if own:
        return shadda + own
    if "ْ" in marks:
        before = next((MARK[c] for c in reversed(word[:i]) if c in MARK), None)
        return shadda + "sukun after " + (before or "word start")
    return "long-vowel letter"


def letter_sures(tok: Tokenizer, word: str, lead: str, probs: list[float]) -> list[tuple[str, str, float]] | None:
    """(letter, context, sureness of the piece holding it) for each letter of one word."""
    enc = tok.encode(lead + word, add_special_tokens=False)
    if len(enc.ids) != len(probs):
        return None
    out = []
    for i, ch in enumerate(word):
        if ch not in LETTERS:
            continue
        at = i + len(lead)
        piece = next((t for t, (s, e) in enumerate(enc.offsets) if s <= at < e), None)
        if piece is not None:
            out.append((ch, written_context(word, i), probs[piece]))
    return out


def table(title: str, cells: dict, head: str, sort_key) -> list[str]:
    rows = sorted(cells.items(), key=sort_key)
    out = ["", title, head]
    for (a, b, c), (n, hit) in rows:
        mark = "  (few)" if n < FEW else ""
        out.append(f"{a:<15} {b:<3} {c:<26} {n:>5} {hit / n:>6.0%}{mark}")
    return out


def cases(which: str):
    """(words, slipped word or None, (kind, letter, context), row) for each clip of a set."""
    if which == "spliced":
        for row in map(json.loads, META.open(encoding="utf-8")):
            yield as_heard(row["sentence"]), row["k"], (row.get("kind"), row.get("letter"), row.get("context")), row
        return
    for row in clips():
        words = as_heard(row["sentence"].replace("@", ""))
        k = slipped_word(row, words)
        cell = slip_cell(row["phoneme_ref"].split(), row["phoneme_mis"].split()) if k is not None else (None,) * 3
        yield words, k, cell, row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    settings = get_settings()
    parser.add_argument("--model", default=settings.recitation_model)
    parser.add_argument("--rule", default=settings.recitation_sure_of_word)
    parser.add_argument("--set", choices=("iqra", "spliced"), default="iqra",
                        help="iqra: IqraEval's 97 real slips; spliced: spliced.py's many per letter")
    args = parser.parse_args()
    cut = json.loads(RECITE.read_text(encoding="utf-8"))["wrong-below"]
    scored = pieces_path(args.model).with_name(f"{args.set}-" + pieces_path(args.model).name)
    if not scored.exists():
        raise SystemExit(f"{scored.name} missing: score {args.set} with {args.model} first")
    probs = {r["id"]: r["probs"] for r in map(json.loads, scored.open(encoding="utf-8"))}
    repo, _, rev = args.model.partition("@")
    tok_file = next((Path.home() / ".cache" / "huggingface" / "hub" / f"models--{repo.replace('/', '--')}"
                     / "snapshots").glob(f"{rev or '*'}*/tokenizer.json"))
    tok = Tokenizer.from_file(str(tok_file))

    slips, right = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    by_kind, by_ctx = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    unmatched = 0
    for words, k, (kind, letter, ctx), row in cases(args.set):
        if row["id"] not in probs:
            continue
        if k is not None:
            caught = checker.aggregate(probs[row["id"]][k], args.rule) < cut
            for cells, key in ((slips, (kind, letter, ctx)), (by_kind, (kind, "", "")),
                               (by_ctx, (kind, "", ctx.split(" -> ")[0]))):
                cells[key][0] += 1
                cells[key][1] += caught
            continue
        for i, (w, p) in enumerate(zip(words, probs[row["id"]])):
            got = letter_sures(tok, w, "" if i == 0 else " ", p)
            if got is None:
                unmatched += 1
                continue
            for ch, ctx, s in got:
                for key in ((ch, "", ctx), ("all letters", "", ctx), (ch, "", "any")):
                    right[key][0] += 1
                    right[key][1] += s < cut

    total = sum(n for n, _ in by_kind.values())
    caught = sum(h for _, h in by_kind.values())
    lines = [
        f"Ear {args.model}, rule {args.rule}, cut {cut}. Set {args.set}, {total} slips, {caught / total:.0%} caught.",
        "caught = slipped word red; red = right letter's piece below the cut. (few) = under "
        f"{FEW} cases, too few to judge. {unmatched} right words skipped (pieces did not line up).",
    ]
    head = f"{'kind':<15} {'':<3} {'context':<26} {'n':>5} {'caught':>6}"
    lines += table("SLIPS BY KIND", by_kind, head, lambda x: -x[1][0])
    lines += table("SLIPS BY KIND AND VOWEL", by_ctx, head, lambda x: (x[0][0], -x[1][0]))
    lines += table("SLIPS BY LETTER AND VOWEL (worst caught first)", slips, head,
                   lambda x: (x[1][0] < FEW, x[1][1] / x[1][0], -x[1][0]))
    rhead = f"{'letter':<15} {'':<3} {'context':<26} {'n':>5} {'red':>6}"
    lines += table("RIGHT LETTERS BY VOWEL (all letters)", {k: v for k, v in right.items() if k[0] == "all letters"},
                   rhead, lambda x: -x[1][1] / x[1][0])
    lines += table("RIGHT LETTERS BY LETTER", {k: v for k, v in right.items() if k[2] == "any"},
                   rhead, lambda x: -x[1][1] / x[1][0])
    lines += table("RIGHT LETTERS BY LETTER AND VOWEL (reddest first)",
                   {k: v for k, v in right.items() if k[0] != "all letters" and k[2] != "any"},
                   rhead, lambda x: (x[1][0] < FEW, -x[1][1] / x[1][0]))
    REPORT.with_name(REPORT.name.format(args.set)).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
