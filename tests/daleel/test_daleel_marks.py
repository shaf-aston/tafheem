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
