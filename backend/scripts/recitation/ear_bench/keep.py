"""Keep-or-drop rule for a candidate ear. It is kept only if it separates slips
better than the current ear beyond chance on the set that decides, and is not
surely worse at the app's cut on any set: F1 surely lower or more right words
surely red each refuse it. Every test is on a 95% range of new minus current,
so noise neither passes nor blocks an ear. Pure, no I/O.
"""
from __future__ import annotations

from typing import NamedTuple

Range = tuple[float, float]  # 95% range of new minus current


class Grade(NamedTuple):
    auc: float
    f1: float         # at the app's cut
    false_red: float  # at the app's cut
    slips: int


class Gains(NamedTuple):
    auc: Range
    f1: Range
    false_red: Range


def verdict(base: Grade, new: Grade, gains: Gains, fewest_slips: int) -> tuple[bool, list[str]]:
    """The set that decides: a sure gain in separating slips, and no sure harm."""
    if new.slips < fewest_slips:
        return False, [f"too few slips to judge: {new.slips}, needs {fewest_slips}"]
    why = harms(base, new, gains)
    if gains.auc[0] <= 0:
        why.insert(0, f"AUC gain could be chance: range {gains.auc[0]:.3f} to {gains.auc[1]:.3f}")
    return not why, why


def harms(base: Grade, new: Grade, gains: Gains) -> list[str]:
    """What surely got worse at the app's cut. A set too small to show a gain can still show this."""
    why = []
    if gains.f1[1] < 0:
        why.append(f"F1 surely lower: {new.f1:.3f} vs {base.f1:.3f}, change {gains.f1[0]:+.3f} to {gains.f1[1]:+.3f}")
    if gains.false_red[0] > 0:
        why.append(f"surely marks more right words red: {new.false_red:.3f} vs {base.false_red:.3f}, "
                   f"change {gains.false_red[0]:+.3f} to {gains.false_red[1]:+.3f}")
    return why
