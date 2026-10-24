"""Ear bench: the maths and the keep rule, on tiny sets checked by hand."""
import pytest

from backend.scripts.recitation.ear_bench import keep, measures
from backend.scripts.recitation.ear_bench.measures import Word


def _words(rows, rec="r"):
    return [Word(rec, i, s, slip) for i, (s, slip) in enumerate(rows)]


FOUR = _words([(0.1, True), (0.2, False), (0.3, True), (0.9, False)])


def test_perfect_separation_is_one():
    assert measures.auc(_words([(0.1, True), (0.2, True), (0.8, False), (0.9, False)])) == 1.0


def test_equal_sureness_is_half():
    assert measures.auc(_words([(0.5, True), (0.5, False), (0.5, False), (0.5, True)])) == 0.5


def test_at_cut_by_hand():
    # cut 0.25 reds words 0 and 1: one slip caught of two, one right word red of two
    got = measures.at_cut(FOUR, 0.25)
    assert (got.precision, got.recall, got.false_red) == (0.5, 0.5, 0.5)
    assert got.f1 == 0.5


def test_best_f1_finds_cut():
    f1, cut = measures.best_f1(FOUR)
    assert f1 == pytest.approx(0.8)  # red the first three: p 2/3, r 1
    assert 0.3 < cut < 0.9


def test_duplicate_word_raises():
    dup = FOUR + [FOUR[0]]
    with pytest.raises(ValueError):
        measures.unique(dup)
    with pytest.raises(ValueError):
        measures.gain(dup, dup, measures.auc, 10, 1)


def test_gain_mismatched_keys_raises():
    with pytest.raises(ValueError):
        measures.gain(FOUR, FOUR[:3] + [Word("r", 9, 0.9, False)], measures.auc, 10, 1)


def test_gain_against_itself_is_zero():
    two = FOUR + _words([(0.2, True), (0.8, False)], rec="s")
    assert measures.gain(two, two, measures.auc, 50, 1) == (0.0, 0.0)


FEWEST = 20


def test_verdict_keeps_clear_winner():
    base, new = keep.Grade(0.80, 0.50, 0.05, 30), keep.Grade(0.90, 0.60, 0.05, 30)
    assert keep.verdict(base, new, (0.05, 0.15), FEWEST) == (True, [])


def test_verdict_too_few_slips_single_reason():
    ok, why = keep.verdict(keep.Grade(0.8, 0.5, 0.05, 5), keep.Grade(0.9, 0.6, 0.05, 5), (0.05, 0.15), FEWEST)
    assert not ok and why == ["too few slips to judge: 5, needs 20"]


def test_verdict_refuses_when_gain_includes_zero():
    ok, why = keep.verdict(keep.Grade(0.8, 0.5, 0.05, 30), keep.Grade(0.9, 0.6, 0.05, 30), (-0.02, 0.1), FEWEST)
    assert not ok and len(why) == 1 and why[0].startswith("AUC gain could be chance")


def test_verdict_refuses_more_right_words_red_than_today():
    ok, why = keep.verdict(keep.Grade(0.8, 0.5, 0.05, 30), keep.Grade(0.9, 0.6, 0.06, 30), (0.05, 0.15), FEWEST)
    assert not ok and why == ["marks more right words red: 0.060 vs 0.050"]
