"""Arc scores -> heads that always form one projective tree.

Argmax alone can give two roots or a cycle; Eisner's algorithm finds the best
projective tree instead. Argmax is kept when it is already one, so a good parse
is never changed. Parser-agnostic: takes a score matrix, knows nothing of ONNX.
"""
from __future__ import annotations

import numpy as np


def heads(scores: np.ndarray) -> list[int]:
    """scores[d, h]: how well word d (1..n) hangs off h (0 = root). Row 0 unused."""
    best = [int(h) for h in np.argmax(scores[1:], axis=-1)]
    return best if is_projective_tree(best) else eisner(scores)


def is_projective_tree(hs: list[int]) -> bool:
    n = len(hs)
    if sum(h == 0 for h in hs) != 1:
        return False
    for d in range(1, n + 1):  # every word reaches the root without a cycle
        seen, h = set(), d
        while h:
            if h in seen:
                return False
            seen.add(h)
            h = hs[h - 1]
    for d, h in enumerate(hs, 1):  # no arc crosses another
        lo, hi = sorted((d, h))
        if any(not lo <= hs[k - 1] <= hi for k in range(lo + 1, hi)):
            return False
    return True


def eisner(scores: np.ndarray) -> list[int]:
    """Best projective tree with a single root word, O(n^3)."""
    n = scores.shape[0] - 1
    s = scores.T  # s[h, d]
    neg = -np.inf
    # [i, j, dir]: dir 0 = head on the right (j), 1 = head on the left (i)
    comp = np.full((n + 1, n + 1, 2), neg)
    inc = np.full((n + 1, n + 1, 2), neg)
    comp_bp = np.zeros((n + 1, n + 1, 2), int)
    inc_bp = np.zeros((n + 1, n + 1, 2), int)
    for i in range(n + 1):
        comp[i, i] = 0
    for width in range(1, n + 1):
        for i in range(n + 1 - width):
            j = i + width
            spans = comp[i, i:j, 1] + comp[i + 1:j + 1, j, 0]
            k = int(np.argmax(spans))
            inc[i, j, 0] = spans[k] + s[j, i]
            inc[i, j, 1] = spans[k] + s[i, j]
            inc_bp[i, j] = i + k
            left = comp[i, i:j, 0] + inc[i:j, j, 0]
            k = int(np.argmax(left))
            comp[i, j, 0], comp_bp[i, j, 0] = left[k], i + k
            right = inc[i, i + 1:j + 1, 1] + comp[i + 1:j + 1, j, 1]
            k = int(np.argmax(right))
            comp[i, j, 1], comp_bp[i, j, 1] = right[k], i + 1 + k
    # the root takes exactly one child: pick it, then build each side
    hs = [0] * n
    r = max(range(1, n + 1), key=lambda r: comp[1, r, 0] + comp[r, n, 1] + s[0, r])
    _complete(1, r, 0, comp_bp, inc_bp, hs)
    _complete(r, n, 1, comp_bp, inc_bp, hs)
    return hs


def _complete(i, j, d, comp_bp, inc_bp, hs):
    if i == j:
        return
    k = comp_bp[i, j, d]
    if d == 0:
        _complete(i, k, 0, comp_bp, inc_bp, hs)
        _incomplete(k, j, 0, comp_bp, inc_bp, hs)
    else:
        _incomplete(i, k, 1, comp_bp, inc_bp, hs)
        _complete(k, j, 1, comp_bp, inc_bp, hs)


def _incomplete(i, j, d, comp_bp, inc_bp, hs):
    if d == 0:
        hs[i - 1] = j
    else:
        hs[j - 1] = i
    k = inc_bp[i, j, d]
    _complete(i, k, 1, comp_bp, inc_bp, hs)
    _complete(k + 1, j, 0, comp_bp, inc_bp, hs)
