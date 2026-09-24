"""Which quotation goes first, and how honestly each one is labelled.

Ranking decides what a reader sees at the top, and the loose tier decides
whether a probable typo-fix is allowed to look like a clean find. Both are
pure functions of a row and the expansion, so both are checked here against
rows written out by hand rather than against whatever the index happens to
hold today.

Several of these pin behaviour that was wrong when first run, and the comment
on each says what it was, so it is clear the case is real and not invented.
"""
from backend.services.daleel.expand import Expansion
from backend.services.daleel.search import rank_of

TIER = 0
ROOT_TIER = 3
LOOSE_TIER = 4


def row(fold, roots="", english="", locator="1:1", source="corpus", book="Quranic Arabic Corpus"):
    """The index's row: source, book, locator, arabic, english, roots, fold."""
    return (source, book, locator, fold, english, roots, fold)


def only(word):
    return Expansion(typed=(word,), related=(), roots=(), loose=())


def test_all_terms_present_beats_some():
    expansion = Expansion(typed=("كتاب", "علم"), related=(), roots=(), loose=())
    assert rank_of(row("كتاب علم"), expansion) < rank_of(row("كتاب رجل"), expansion)


def test_the_typed_word_beats_a_synonym_of_it():
    """The fix for searching كتب and getting Ibn Faris on رسم at the top."""
    expansion = Expansion(typed=("كتب",), related=("رسم",), roots=(), loose=())
    typed = rank_of(row("كتب عليكم"), expansion)
    synonym = rank_of(row("رسم الشيء"), expansion)
    assert typed[0] == 0
    assert synonym[0] == 2
    assert typed < synonym


def test_a_word_match_beats_a_root_match():
    expansion = Expansion(typed=("كتاب",), related=(), roots=("كتب",), loose=())
    word = rank_of(row("هذا كتاب", roots="كتب"), expansion)
    root_only = rank_of(row("هو كاتب", roots="كتب"), expansion)
    assert word[0] == 0 and root_only[0] == ROOT_TIER
    assert word < root_only


def test_a_root_match_beats_a_loose_match():
    expansion = Expansion(typed=("كتاب",), related=(), roots=("كتب",), loose=("كتاب",))
    root = rank_of(row("كاتب", roots="كتب"), expansion)
    loose = rank_of(row("كتب شيء", roots="شيء"), expansion)
    assert root[0] == ROOT_TIER and loose[0] == LOOSE_TIER
    assert root < loose


def test_an_attached_prefix_still_counts_as_using_the_word():
    """Arabic joins its prefixes on, so بالصبر is how an ayah says الصبر.

    Demanding a space on both sides ranked Ibn Faris above al-Baqarah 2:45,
    which is the verse everybody means when they search الصبر.
    """
    expansion = only("الصبر")
    prefixed = rank_of(row("واستعينوا بالصبر والصلاة"), expansion)
    buried = rank_of(row("كلام كثير جدا هنا وبعده الصبر وكلام اخر بعده"), expansion)
    assert prefixed < buried


def test_a_suffix_makes_it_a_different_word():
    """كتبي is not كتب, so a dictionary headword must not beat the verse."""
    expansion = only("كتب")
    verse = rank_of(row("كتب عليكم الصيام"), expansion)
    headword = rank_of(row("كتبي"), expansion)
    assert verse < headword


def test_an_earlier_hit_beats_a_later_one():
    expansion = only("علم")
    assert rank_of(row("علم كثير جدا هنا"), expansion) < rank_of(row("كثير جدا هنا علم"), expansion)


def test_a_root_is_matched_whole_not_as_a_substring():
    """كتب must not match a longer root that merely contains those letters."""
    expansion = Expansion(typed=(), related=(), roots=("كتب",), loose=())
    assert rank_of(row("x", roots="كتب"), expansion)[0] == ROOT_TIER
    assert rank_of(row("x", roots="اكتبر"), expansion)[0] == LOOSE_TIER


def test_an_english_only_passage_can_still_match():
    """Ibn Kathir carries no Arabic, so ranking must read the English too."""
    expansion = Expansion(typed=("patience",), related=(), roots=(), loose=())
    assert rank_of(row("", english="The Virtue of Patience"), expansion)[0] == 0


def test_loose_rows_are_ordered_by_how_much_they_share():
    """Among "did you mean" results, more shared runs means more likely meant."""
    expansion = Expansion(typed=("الرحييم",), related=(), roots=(), loose=("الرحييم",))
    close = rank_of(row("الرحيم"), expansion)
    distant = rank_of(row("الرجل"), expansion)
    assert close[0] == LOOSE_TIER and distant[0] == LOOSE_TIER
    assert close < distant


def test_root_matches_are_ordered_by_how_many_roots_they_share():
    """A root hit has no position to sort on, so it must sort on something else.

    It used to fall through to the word-match ordering, where both remaining
    numbers came out as the passage length: an ordering that was really just
    shortest-wins, which put bare dictionary headwords above whole ayahs.
    """
    expansion = Expansion(typed=("x",), related=(), roots=("كتب", "علم"), loose=())
    both = rank_of(row("aaa", roots="كتب علم"), expansion)
    one = rank_of(row("aaa", roots="كتب"), expansion)
    assert both[0] == ROOT_TIER and one[0] == ROOT_TIER
    assert both < one


def test_a_root_hit_beats_a_loose_hit_even_when_longer():
    expansion = Expansion(typed=("qqq",), related=(), roots=("كتب",), loose=("qqq",))
    root = rank_of(row("a much longer passage here", roots="كتب"), expansion)
    loose = rank_of(row("qq", roots=""), expansion)
    assert root[0] == ROOT_TIER and loose[0] == LOOSE_TIER
    assert root < loose
