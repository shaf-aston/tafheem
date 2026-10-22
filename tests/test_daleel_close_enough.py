"""A guess at a misspelling is shown only when it is near the best guess.

Every book is promised a place, so without a floor each one sent its best
guess however poor: الرحييم came back as al-Fatihah and ten passages sharing
one run of letters with it.
"""
from backend.services.daleel.expand import Expansion
from backend.services.daleel.search import _close_enough, rank_of


def row(fold, source="corpus"):
    return (source, "", "1:1", fold, "", "", fold)


def test_far_guesses_are_dropped_and_near_ones_kept():
    expansion = Expansion(typed=("الرحييم",), related=(), roots=(), loose=("الرحييم",))
    rows = [row("بسم الله الرحمن الرحيم"), row("الرحى تدور", "lane"), row("عبد الرحيم", "wiktionary")]
    kept = [r[3] for _, r in _close_enough(sorted(((rank_of(r, expansion), r) for r in rows), key=lambda i: i[0]), expansion)]
    assert "الرحى تدور" not in kept
    assert {"بسم الله الرحمن الرحيم", "عبد الرحيم"} <= set(kept)


def test_clean_finds_are_never_touched():
    expansion = Expansion(typed=("صبر",), related=(), roots=(), loose=("صبر",))
    rows = [row("صبر جميل")]
    assert len(_close_enough([(rank_of(r, expansion), r) for r in rows], expansion)) == 1


def test_a_word_with_something_joined_on_is_as_near_as_without():
    """والرحيم and الرحيم، were scored two letters away and dropped."""
    expansion = Expansion(typed=("الرحييم",), related=(), roots=(), loose=("الرحييم",))
    rows = [row("عبد الرحيم"), row("وهو الغفور الرحيم،", "qul"), row("والرحيم بعباده", "lane")]
    assert len(_close_enough(sorted(((rank_of(r, expansion), r) for r in rows), key=lambda i: i[0]), expansion)) == 3
