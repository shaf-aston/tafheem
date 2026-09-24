"""Which rule for "was this word said" marks the fewest correct recitations.

    python backend/scripts/sweep_sureness.py
    python backend/scripts/sweep_sureness.py --heard downloads/heard-letters.jsonl

--heard swaps in another model's transcripts (time_placing.py --save), which
move both the stretch that is judged and the "page did not find it" half of red.

Needs rescore_recitation.py run first. No model runs and no sound: it reads the
pieces that run wrote down and tries every rule against the reviewers' marks, so
a question that used to cost an hour of model time costs seconds.

Two things are being chosen, together:

  how a word's pieces become one number   worst (its least sure piece, which is
                                          what the app did), mean, worst-but-one
  what that number has to beat            the threshold

Judged on four shares, and the first is the complaint this exists to fix:

  marked though right      words in a recording the reviewer found nothing
                           wrong with, that the rule says were not said. Every
                           one is a reader told they slipped when they did not.
  marked for tajweed only  words the reviewer marked for tajweed and nothing
                           else. The word itself was right, and the app says it
                           does not judge tajweed, so these are wrong marks too.
  word slips caught        words the reviewer marked as a wrong letter or word.
  vowel slips caught       words the reviewer marked as a wrong vowel. Nearly
                           all of these are al-Ikhlas, so read them as a guide.

The bar the plan set: under 3 in 100 marked though right, with vowel slips
still caught at least as often as the app catches them today (85%).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path, get_settings  # noqa: E402
from backend.services.recitation.listen import aggregate  # noqa: E402
from backend.services.recitation.place import reach  # noqa: E402
from backend.services.recitation.spelling import as_heard  # noqa: E402
from backend.scripts.rescore_recitation import HERE, pieces_path  # noqa: E402
from backend.scripts.score_recitation_checker import (  # noqa: E402
    NEIGHBOURS, RESULTS, marks_to_places, page_verdict, stretch,
)

RULES = ("worst", "worst-but-one", "mean")
# The rule and flag-below of each level in frontend/src/recite.json.
LEVELS = {"beginner": 0.7, "standard": 0.95}
CUTS = (0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95)
SWEEP = HERE / "sweep.txt"
# What every rule is measured against: what the page does today, and the bar.
BAR_MARKED, BAR_VOWELS = 0.03, 0.85


def scored_by_app(ayahs: dict, key: str, heard: str) -> tuple[int, int] | None:
    """Which of the ayah's words the app would check by sound, as recitation.check
    does: placed on the ayah and its neighbours, run on to the end of the ayah it
    stops in. None when it does not place, and then nothing is checked by sound."""
    surah, ayah = map(int, key.split(":"))
    words, start = [], 0
    for n in range(ayah - NEIGHBOURS, ayah + NEIGHBOURS + 1):
        if n == ayah:
            start = len(words)
        words += as_heard(ayahs.get(f"{surah}:{n}", ""))
    end = start + len(as_heard(ayahs[key]))
    span = reach(words, heard.split())
    if span is None:
        return None
    first, last = span
    if start <= last - 1 < end:
        last = end
    return max(first, start) - start, max(min(last, end) - start, 0)


def groups(ayahs: dict, model: str, heard: dict | None = None):
    """(group name, the word's pieces, the page found it, the app checks it by
    sound) for every word both files agree on; the last is None when the app
    cannot place the recording at all.

    Placing is worked out again from the transcript rather than trusted from
    either file, so the two always speak about the same words.
    """
    reviewed = {}
    for line in RESULTS.open(encoding="utf-8"):
        row = json.loads(line)
        if "skipped" not in row:
            reviewed[row["id"]] = row
    out = []
    for line in pieces_path(model).open(encoding="utf-8"):
        got = json.loads(line)
        row = reviewed.get(got["id"])
        if row is None or len(got["probs"]) != len(row["words"]):
            continue
        page = row["page"]
        if heard is not None:
            if got["id"] not in heard:
                continue
            row = {**row, "heard": heard[got["id"]]}
            page = page_verdict(row["words"], row["heard"])
        marked = marks_to_places(row["words"], row["marks"])
        clean = not row["marks"]
        first, last = stretch(ayahs, row["ayah"], row["heard"])[3]
        app = scored_by_app(ayahs, row["ayah"], row["heard"])
        for i in range(first, min(last, len(got["probs"]))):
            kind = marked.get(i)
            if kind == "tajweed":
                name = "marked for tajweed only"
            elif kind:
                name = f"{kind} slips"
            elif clean:
                name = "right, in a clean recording"
            else:
                name = "unmarked, in a recording with a slip"
            out.append((name, got["probs"][i], page[i], app and app[0] <= i < app[1]))
    return out


def table(rows, model: str) -> str:
    """Every rule at every threshold, as shares of each group counted NOT said."""
    total = defaultdict(int)
    page_flags = defaultdict(int)
    for name, _probs, said, _app in rows:
        total[name] += 1
        page_flags[name] += not said
    names = ["right, in a clean recording", "marked for tajweed only",
             "letter or word slips", "vowel slips", "unmarked, in a recording with a slip"]
    names = [n for n in names if total[n]]
    head = f"{'rule':>14}{'cut':>7}" + "".join(f"{n.split(',')[0][:20]:>22}" for n in names)
    # How many words each share is a share of. Without this a 8.8% on 34 words
    # reads exactly like a 8.8% on 6,000, and the small groups are where a
    # single word moves the number by three points.
    counted = f"{'out of':>14}{'':>7}" + "".join(f"{total[n]:>22,}" for n in names)
    lines = [f"{len(rows)} words judged, heard by {model}", "",
             "Share of each group the rule says was NOT said. For the first two lower is",
             "better, they are words that were right; for the slips higher is better.",
             "The second line is how many words are in each group: the two slip columns",
             "rest on few enough words that one word moves them several points.", "",
             head, counted,
             f"{'the page today':>14}{'':>7}"
             + "".join(f"{page_flags[n] / total[n]:>22.1%}" for n in names)]
    best = None
    for rule in RULES:
        scored = [(name, aggregate(probs, rule)) for name, probs, _, _ in rows]
        for cut in CUTS:
            flagged = defaultdict(int)
            for name, s in scored:
                flagged[name] += s < cut
            share = {n: flagged[n] / total[n] for n in names}
            lines.append(f"{rule:>14}{cut:>7}" + "".join(f"{share[n]:>22.1%}" for n in names))
            wrong = share["right, in a clean recording"]
            vowels = share.get("vowel slips", 0)
            if wrong <= BAR_MARKED and vowels >= BAR_VOWELS and (best is None or vowels > best[2]):
                best = (rule, cut, vowels, wrong)
    lines += ["", f"The bar: at most {BAR_MARKED:.0%} marked though right, "
                  f"vowel slips still caught {BAR_VOWELS:.0%} of the time."]
    lines.append(f"Best rule that clears it, judging by sound alone: {best[0]} under {best[1]}, "
                 f"{best[3]:.1%} marked though right, {best[2]:.1%} of vowel slips caught."
                 if best else "Nothing clears it by sound alone. Nothing is claimed; the rows are above.")
    return "\n".join(lines + ["", ""] + red(rows, names, total) + ["", ""]
                     + as_the_app(rows, names, total)) + "\n"


def red(rows, names, total) -> list[str]:
    """What the page would actually show, which is the number the reader sees.

    A word is only shown red when both parts say so: the page did not find it
    in what the ear wrote down, AND the ear is less sure of it than flag-below.
    So this sweeps flag-below, the one number that decides a red mark, and
    reports the share of each group shown red. That is the shipping behaviour,
    where the table above is the sound check on its own.
    """
    lines = ["Shown RED by the page: the transcript missed the word and the sound check",
             "is under flag-below. Orange is not counted here; orange accuses nobody.", "",
             f"{'rule':>14}{'flag-below':>12}" + "".join(f"{n.split(',')[0][:20]:>22}" for n in names)]
    for rule in RULES:
        scored = [(name, aggregate(probs, rule), said) for name, probs, said, _ in rows]
        for cut in CUTS:
            flagged = defaultdict(int)
            for name, s, said in scored:
                flagged[name] += not said and s < cut
            lines.append(f"{rule:>14}{cut:>12}"
                         + "".join(f"{flagged[n] / total[n]:>22.1%}" for n in names))
    return lines


def as_the_app(rows, names, total) -> list[str]:
    """RED as the reader sees it, per level, placing the way the app does.

    The table above judges the whole ayah whatever the transcript; the app does
    not. A word the app has no sureness for, because the recording did not
    place or the word is past the stretch, is orange at worst, never red
    (follow.bySound). Red is decided by sound alone once a word is checked.
    """
    checked = sum(bool(app) for *_, app in rows) / len(rows)
    # Every cut, not only the two in use. Changing anything about how the ear
    # listens moves these numbers, and then the question is which cut puts the
    # reader back where they were: that is a row to read off, not a guess. The
    # two cuts the app ships are named in the margin.
    inuse = {cut: level for level, cut in LEVELS.items()}
    lines = [f"RED as the app shows it, worst-but-one. Words checked by sound: {checked:.1%}", "",
             f"{'flag-below':>14}{'in use':>12}" + "".join(f"{n.split(',')[0][:20]:>22}" for n in names)]
    for cut in sorted(set(CUTS) | set(LEVELS.values())):
        flagged = defaultdict(int)
        for name, probs, _said, app in rows:
            flagged[name] += bool(app) and aggregate(probs, "worst-but-one") < cut
        lines.append(f"{cut:>14}{inuse.get(cut, ''):>12}"
                     + "".join(f"{flagged[n] / total[n]:>22.1%}" for n in names))
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", help="which model's pieces to read; the one in config by default")
    parser.add_argument("--heard", type=Path,
                        help="transcripts to place by instead of results.jsonl's, relative to recitation_checks")
    args = parser.parse_args()
    model = args.model or get_settings().recitation_model
    if not pieces_path(model).exists():
        raise SystemExit(f"No pieces for {model}. Run rescore_recitation.py first.")
    ayahs = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    heard, out = None, SWEEP
    if args.heard:
        lines = (HERE / args.heard).read_text(encoding="utf-8").splitlines()
        heard = {r["id"]: r["heard"] for r in map(json.loads, lines)}
        out = SWEEP.with_name(f"sweep-{args.heard.stem}.txt")
    text = table(groups(ayahs, model, heard), model)
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
