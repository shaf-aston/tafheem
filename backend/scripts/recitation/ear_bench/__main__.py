"""Print each ear's grade on each set, and with two ears whether the second is kept. Writes recitation_checks/bench.txt.

IqraEval (955 slips) decides; the marked recordings no ear trained on (35 slips, too few to show a gain) can only refuse.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.config import data_path, get_settings
from backend.services.recitation.checker import aggregate
from backend.scripts.recitation.ear_bench import iqra, keep, measures
from backend.scripts.recitation.ear_bench.words import RIGHT, SLIPS, labelled
from backend.scripts.recitation.paths import CHECKS
from backend.scripts.recitation.rescore_recitation import run as rescore

KNOBS = json.loads((Path(__file__).parent / "bench.json").read_text(encoding="utf-8"))
RECITE = Path(__file__).resolve().parents[4] / "frontend" / "src" / "config" / "recite.json"
REPORT = CHECKS / "bench.txt"
DECIDES = "IqraEval"


def graded_words(ayahs: dict, model: str) -> list[measures.Word]:
    """Slips and right words in clean recordings; tajweed-only and unmarked-beside-a-slip have no clean truth."""
    rule = get_settings().recitation_sure_of_word
    return measures.unique(
        measures.Word(w.recording, w.at, aggregate(w.probs, rule), w.group in SLIPS)
        for w in labelled(ayahs, model) if w.group in SLIPS or w.group == RIGHT)


def grade(words: list[measures.Word], cut: float) -> keep.Grade:
    at = measures.at_cut(words, cut)
    return keep.Grade(measures.auc(words), at.f1, at.false_red, sum(w.slip for w in words))


def lines_for(name: str, words: list[measures.Word], cut: float) -> list[str]:
    lo, hi = measures.interval(words, measures.auc, KNOBS["draws"], KNOBS["seed"])
    at = measures.at_cut(words, cut)
    f1, best = measures.best_f1(words)
    return [f"{name}: {len(words):,} words, {sum(w.slip for w in words)} slips",
            f"  AUC {measures.auc(words):.3f} (95% {lo:.3f} to {hi:.3f})",
            f"  at the app's cut {cut}: precision {at.precision:.2f}, recall {at.recall:.2f}, "
            f"F1 {at.f1:.2f}, right words red {at.false_red:.1%}",
            f"  best F1 {f1:.2f} at cut {best:.3f}"]


def judged(words: list[measures.Word]) -> list[measures.Word]:
    return [w for w in words if w.recording.startswith(tuple(KNOBS["judged-on"]))]


def sets(ayahs: dict, model: str) -> dict[str, list[measures.Word]]:
    """Every set an ear is graded on, the deciding one first. Each scores the clips this ear has not heard yet."""
    rescore(ayahs, None, model)
    return {DECIDES: iqra.graded_words(model, get_settings().recitation_sure_of_word),
            "marked recordings never trained on": judged(graded_words(ayahs, model))}


def compared(old: list[measures.Word], new: list[measures.Word], cut: float):
    """Both ears' grades, the 95% gains, and how many words both were graded on."""
    keys = {(w.recording, w.at) for w in old} & {(w.recording, w.at) for w in new}
    old, new = ([w for w in ws if (w.recording, w.at) in keys] for ws in (old, new))
    gains = keep.Gains(*(measures.gain(old, new, metric, KNOBS["draws"], KNOBS["seed"]) for metric in (
        measures.auc, lambda ws: measures.at_cut(ws, cut).f1, lambda ws: measures.at_cut(ws, cut).false_red)))
    return grade(old, cut), grade(new, cut), gains, len(keys)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", help="one ear to grade, or OLD NEW; the ear in config by default")
    args = parser.parse_args()
    models = args.models or [get_settings().recitation_model]
    if len(models) > 2:
        raise SystemExit("one ear, or two to compare")
    ayahs = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    cut = json.loads(RECITE.read_text(encoding="utf-8"))["wrong-below"]
    by_model = {m: sets(ayahs, m) for m in models}
    out = []
    for m, graded in by_model.items():
        for name, words in graded.items():
            out += lines_for(f"{m}, {name}", words, cut)
        out += [""]
    if len(models) == 2:
        why = []
        for name in by_model[models[0]]:
            base, new, gains, shared = compared(*(by_model[m][name] for m in models), cut)
            out += [f"{name}, {metric} change on {shared:,} shared words: {lo:+.3f} to {hi:+.3f}"
                    for metric, (lo, hi) in gains._asdict().items()]
            why += [f"{name}: {w}" for w in (keep.verdict(base, new, gains, KNOBS["fewest-slips"])[1]
                                             if name == DECIDES else keep.harms(base, new, gains))]
        out += ["KEEP" if not why else "DROP: " + "; ".join(why)]
    text = "\n".join(out) + "\n"
    REPORT.write_text(text, encoding="utf-8")
    print(text)
    if len(models) == 2 and why:
        raise SystemExit(1)  # a caller (cloud.py --ship) stops on a DROP


if __name__ == "__main__":
    main()
