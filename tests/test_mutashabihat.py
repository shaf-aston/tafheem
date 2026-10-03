"""Similar verses: the folding, the diff, the catalogue merge and the finder."""
from __future__ import annotations

from backend.scripts.build_mutashabihat import merge
from backend.services import mutashabihat


def test_fold_drops_marks_and_unifies_letters():
    assert mutashabihat.fold("الرَّحْمَٰنِ") == mutashabihat.fold("الرحمن")
    assert mutashabihat.fold("أَنزَلْنَا") == mutashabihat.fold("انزلنا")
    assert mutashabihat.fold("رَحْمَةً") == mutashabihat.fold("رحمه")
    assert mutashabihat.fold("هُدًى") == mutashabihat.fold("هدي")


def test_replacement_marks_both_sides():
    a = "قال ربي الله".split()
    b = "قال ربي الرحمن".split()
    assert mutashabihat.diff(a, b) == ([[2, 3]], [[2, 3]])


def test_addition_marks_only_the_longer_side():
    a = "قال ربي".split()
    b = "قال ربي العظيم".split()
    assert mutashabihat.diff(a, b) == ([], [[2, 3]])


def test_order_swap_is_marked():
    a = "السماء والارض".split()
    b = "الارض والسماء".split()
    spans_a, spans_b = mutashabihat.diff(a, b)
    assert spans_a and spans_b


def test_identical_verses_have_no_diff():
    words = "بسم الله الرحمن الرحيم".split()
    assert mutashabihat.diff(words, list(words)) == ([], [])


def test_marks_that_fold_to_nothing_do_not_shift_the_spans():
    # a pause sign is a token of its own in the text and must keep its place in the count
    a = ["قال", "ۖ", "ربي"]
    b = ["قال", "ۖ", "ربنا"]
    assert mutashabihat.diff(a, b) == ([[2, 3]], [[2, 3]])


def test_merge_rejects_duplicates_self_pairs_and_unknown_keys_and_counts_overlap():
    rows = [
        ("2:59", "7:162", "benchmark", "replacement"),
        ("7:162", "2:59", "benchmark", "replacement"),  # same pair, reversed
        ("2:59", "7:162", "waqar144", ""),               # same pair, other source: overlap
        ("2:1", "2:1", "waqar144", ""),
        ("2:1", "99:99", "waqar144", ""),
    ]
    pairs, rejected = merge(rows, {"2:59", "7:162", "2:1"})
    assert list(pairs) == [("2:59", "7:162")]
    assert pairs[("2:59", "7:162")] == {"sources": ["benchmark", "waqar144"], "change_type": "replacement"}
    assert rejected == {"duplicate": 1, "self-pair": 1, "unknown key": 1}


def test_candidates_finds_the_known_partner():
    assert "7:162" in mutashabihat.candidates("2:59", 5)


def test_partners_carry_text_diff_and_sources():
    found = {p["key"]: p for p in mutashabihat.partners("2:59")}
    twin = found["7:162"]
    assert twin["text"] == mutashabihat.texts()["7:162"]
    assert twin["diff_self"] and twin["diff_other"]
    assert "benchmark" in twin["sources"]
