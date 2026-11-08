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
BASE, NEW = keep.Grade(0.80, 0.50, 0.05, 30), keep.Grade(0.90, 0.60, 0.05, 30)
# 95% ranges of new minus current: AUC surely up, F1 surely up, right words red surely down.
SURE_WIN = keep.Gains(auc=(0.05, 0.15), f1=(0.01, 0.1), false_red=(-0.02, -0.01))


def test_verdict_keeps_clear_winner():
    assert keep.verdict(BASE, NEW, SURE_WIN, FEWEST) == (True, [])


def test_verdict_too_few_slips_single_reason():
    ok, why = keep.verdict(keep.Grade(0.8, 0.5, 0.05, 5), keep.Grade(0.9, 0.6, 0.05, 5), SURE_WIN, FEWEST)
    assert not ok and why == ["too few slips to judge: 5, needs 20"]


def test_verdict_refuses_when_gain_includes_zero():
    ok, why = keep.verdict(BASE, NEW, SURE_WIN._replace(auc=(-0.02, 0.1)), FEWEST)
    assert not ok and len(why) == 1 and why[0].startswith("AUC gain could be chance")


def test_verdict_refuses_surely_more_right_words_red():
    ok, why = keep.verdict(BASE, NEW, SURE_WIN._replace(false_red=(0.005, 0.02)), FEWEST)
    assert not ok and len(why) == 1 and why[0].startswith("surely marks more right words red")


def test_verdict_refuses_surely_lower_f1():
    ok, why = keep.verdict(BASE, NEW, SURE_WIN._replace(f1=(-0.05, -0.01)), FEWEST)
    assert not ok and len(why) == 1 and why[0].startswith("F1 surely lower")


def test_verdict_noise_in_harm_does_not_block():
    """F1 lower and more right words red on average, but each range spans zero: chance, so the sure AUC gain still keeps it."""
    worse = keep.Grade(0.90, 0.45, 0.06, 30)
    assert keep.verdict(BASE, worse, SURE_WIN._replace(f1=(-0.04, 0.02), false_red=(-0.01, 0.03)), FEWEST) == (True, [])


def test_harms_alone_refuse_on_a_set_too_small_to_decide():
    assert keep.harms(BASE, NEW, SURE_WIN._replace(false_red=(0.01, 0.02))) != []
    assert keep.harms(BASE, NEW, SURE_WIN._replace(auc=(-0.5, 0.5))) == []
