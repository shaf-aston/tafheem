"""Which words of a quotation the screen marks as the reason it came back.

The screen does no matching of its own, so these offsets are the whole story:
they must land on the word as printed, with its vowels and its Uthmani
spelling, by the same rule that ranked the passage.
"""
from backend.services.daleel.match.marks import marks


def marked(text, *terms):
    return [text[start:end] for start, end in marks(text, terms)]


def test_the_printed_word_is_marked_with_its_vowels():
    assert marked("إِنَّ ٱللَّهَ مَعَ ٱلصَّـٰبِرِينَ", "صابرين") == ["ٱلصَّـٰبِرِينَ"]


def test_the_uthmani_spelling_is_found_from_the_plain_one():
    assert marked("وَأَقِيمُوا۟ ٱلصَّلَوٰةَ", "الصلاة") == ["ٱلصَّلَوٰةَ"]


def test_a_phrase_is_marked_as_one():
    assert marked("Seek help in the name of God", "in the name of") == ["in the name of"]


def test_lamma_is_not_marked_for_ma():
    assert marked("فلما جاء ما كان", "ما") == ["ما"]


def test_nothing_to_mark():
    assert marks("", ("ما",)) == ()
    assert marks("كتاب", ()) == ()


def test_the_fast_fold_says_what_the_letter_by_letter_one_says():
    from backend.services.daleel.match.marks import (
        _folded_letter_by_letter,
        _folded_with_origin,
    )

    for text in (
        "إِنَّ ٱللَّهَ مَعَ ٱلصَّـٰبِرِينَ",
        "وَأَقِيمُوا۟ ٱلصَّلَوٰةَ وَءَاتُوا۟ ٱلزَّكَوٰةَ",
        "عَلَىٰ هُدًى مِّن رَّبِّهِمْ",
        "God is with the patient صبر",
        "",
    ):
        for written in (False, True):
            assert _folded_with_origin(text, written) == _folded_letter_by_letter(text, written)
