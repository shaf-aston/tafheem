"""decode.heads always returns one projective tree, and the best one."""
import itertools

import numpy as np

from backend.services.syntax.decode import eisner, heads, is_projective_tree


def test_argmax_tree_is_kept():
    s = np.full((3, 3), -9.0)
    s[1, 0], s[2, 1] = 5, 5  # word 1 is root, word 2 hangs off it
    assert heads(s) == [0, 1]


def test_two_roots_become_one_tree():
    s = np.zeros((3, 3))
    s[1, 0], s[2, 0] = 5, 5  # argmax gives two roots
    assert is_projective_tree(heads(s))


def test_eisner_matches_brute_force():
    rng = np.random.default_rng(0)
    for _ in range(100):
        n = int(rng.integers(1, 6))
        s = rng.normal(size=(n + 1, n + 1))
        score = lambda h: sum(s[d + 1, h[d]] for d in range(n))
        trees = [h for h in itertools.product(range(n + 1), repeat=n) if is_projective_tree(list(h))]
        assert abs(score(eisner(s)) - max(map(score, trees))) < 1e-9
