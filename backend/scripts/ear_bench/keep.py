"""Keep-or-drop rule for a candidate ear. It is kept only if it separates slips
better than the current ear, beyond chance, without marking more right
words red than it does. Pure, no I/O.
"""
from __future__ import annotations

from typing import NamedTuple


class Grade(NamedTuple):
    auc: float
    f1: float         # at the app's cut
    false_red: float  # at the app's cut
    slips: int


def verdict(
    base: Grade, new: Grade, auc_gain: tuple[float, float], fewest_slips: int
) -> tuple[bool, list[str]]:
    if new.slips < fewest_slips:
        return False, [f"too few slips to judge: {new.slips}, needs {fewest_slips}"]
    why = []
    lo, hi = auc_gain
    if lo <= 0:
        why.append(f"AUC gain could be chance: range {lo:.3f} to {hi:.3f}")
    if new.f1 <= base.f1:
        why.append(f"F1 did not improve: {new.f1:.3f} vs {base.f1:.3f}")
    if new.false_red > base.false_red:
        why.append(f"marks more right words red: {new.false_red:.3f} vs {base.false_red:.3f}")
    return not why, why
