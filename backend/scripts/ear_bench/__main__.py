"""Print each ear's grade, and with two ears whether the second is kept. Writes recitation_checks/bench.txt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.config import data_path, get_settings
from backend.services.recitation.listen import aggregate
from backend.scripts.ear_bench import keep, measures
from backend.scripts.ear_bench.words import RIGHT, SLIPS, labelled
from backend.scripts.rescore_recitation import HERE

KNOBS = json.loads((Path(__file__).parent / "bench.json").read_text(encoding="utf-8"))
RECITE = Path(__file__).resolve().parents[3] / "frontend" / "src" / "config" / "recite.json"
REPORT = HERE / "bench.txt"


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", help="one ear to grade, or OLD NEW; the ear in config by default")
    args = parser.parse_args()
    models = args.models or [get_settings().recitation_model]
    if len(models) > 2:
        raise SystemExit("one ear, or two to compare")
    ayahs = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    cut = json.loads(RECITE.read_text(encoding="utf-8"))["sure-at"]
    by_model = {m: graded_words(ayahs, m) for m in models}
    out = []
    for m, words in by_model.items():
        out += lines_for(f"{m}, every marked recording", words, cut)
        out += lines_for(f"{m}, never trained on", judged(words), cut) + [""]
    if len(models) == 2:
        old, new = (judged(by_model[m]) for m in models)
        keys = {(w.recording, w.at) for w in old} & {(w.recording, w.at) for w in new}
        old, new = ([w for w in ws if (w.recording, w.at) in keys] for ws in (old, new))
        lo, hi = measures.gain(old, new, measures.auc, KNOBS["draws"], KNOBS["seed"])
        kept, why = keep.verdict(grade(old, cut), grade(new, cut), (lo, hi),
                                 KNOBS["fewest-slips"])
        out += [f"AUC gain on {len(keys):,} shared words never trained on: {lo:+.3f} to {hi:+.3f}",
                "KEEP" if kept else "DROP: " + "; ".join(why)]
    text = "\n".join(out) + "\n"
    REPORT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
