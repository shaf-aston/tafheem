"""Maths for grading an ear: how well its per-word sureness separates slipped
words from words said right. A word is red when its sureness is below the cut.
Pure functions, no I/O.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Callable, Iterable, NamedTuple


class Word(NamedTuple):
    recording: str  # words in one recording are correlated
    at: int         # word position in that recording
    sure: float     # 0..1, how sure the ear is the word was said
    slip: bool      # True = reviewer marked a real slip


class AtCut(NamedTuple):
    precision: float
    recall: float
    f1: float
    false_red: float  # share of right words marked red


def unique(words: Iterable[Word]) -> list[Word]:
    seen: set[tuple[str, int]] = set()
    out = list(words)
    for w in out:
        key = (w.recording, w.at)
        if key in seen:
            raise ValueError(f"duplicate word {key}")
        seen.add(key)
    return out


def _div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _f1(tp: int, red: int, slips: int) -> tuple[float, float, float]:
    p, r = _div(tp, red), _div(tp, slips)
    return p, r, _div(2 * p * r, p + r)


def _split(words: list[Word]) -> tuple[int, int]:
    slips = sum(w.slip for w in words)
    return slips, len(words) - slips


def auc(words: Iterable[Word]) -> float:
    ws = sorted(words, key=lambda w: w.sure)
    slips, rights = _split(ws)
    if not slips or not rights:
        raise ValueError("auc needs at least one slip and one right word")
    rank_sum, i = 0.0, 0
    while i < len(ws):  # tied sureness share the average rank
        j = i
        while j < len(ws) and ws[j].sure == ws[i].sure:
            j += 1
        rank_sum += (i + 1 + j) / 2 * sum(w.slip for w in ws[i:j])
        i = j
    slip_above = rank_sum - slips * (slips + 1) / 2  # pairs where slip > right
    return 1 - slip_above / (slips * rights)


def at_cut(words: Iterable[Word], cut: float) -> AtCut:
    ws = list(words)
    slips, rights = _split(ws)
    red = [w for w in ws if w.sure < cut]
    tp = sum(w.slip for w in red)
    p, r, f = _f1(tp, len(red), slips)
    return AtCut(p, r, f, _div(len(red) - tp, rights))


def best_f1(words: Iterable[Word]) -> tuple[float, float]:
    ws = list(words)
    best = (0.0, 0.0)
    for v in sorted({w.sure for w in ws}):
        cut = float(v) + 1e-9  # just above v, so v itself is red
        f = at_cut(ws, cut).f1
        if f > best[0]:
            best = (f, cut)
    return best


def _range(vals: list[float]) -> tuple[float, float]:
    vals.sort()
    return vals[round(0.025 * (len(vals) - 1))], vals[round(0.975 * (len(vals) - 1))]


def _resample(
    sets: list[list[Word]], draws: int, seed: int, stat: Callable[[list[list[Word]]], float]
) -> tuple[float, float]:
    """Whole recordings drawn with replacement, same draw applied to every set."""
    by_rec = [defaultdict(list) for _ in sets]
    for groups, ws in zip(by_rec, sets):
        for w in ws:
            groups[w.recording].append(w)
    recs = sorted(by_rec[0])
    rng = random.Random(seed)
    vals: list[float] = []
    for _ in range(draws * 10):
        picked = [rng.choice(recs) for _ in recs]
        drawn = [[w for r in picked for w in groups[r]] for groups in by_rec]
        if any(0 in _split(d) for d in drawn):
            continue
        vals.append(stat(drawn))
        if len(vals) == draws:
            return _range(vals)
    raise ValueError("resamples keep lacking slips or right words")


def interval(
    words: Iterable[Word], metric: Callable[[list[Word]], float], draws: int, seed: int
) -> tuple[float, float]:
    return _resample([unique(words)], draws, seed, lambda d: metric(d[0]))


def gain(
    base: Iterable[Word], new: Iterable[Word],
    metric: Callable[[list[Word]], float], draws: int, seed: int,
) -> tuple[float, float]:
    b, n = unique(base), unique(new)
    if {(w.recording, w.at) for w in b} != {(w.recording, w.at) for w in n}:
        raise ValueError("base and new cover different words")
    return _resample([b, n], draws, seed, lambda d: metric(d[1]) - metric(d[0]))
