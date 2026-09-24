"""Reading one verse of Quran.com's answer, without the network.

The paging and the reading used to be one function, so what the payload means
could only be checked by fetching it. These cases are the shape the API actually
returns: real words, the ayah-end marker that is printed as a trailing word, and
the odd entries a long harvest hits.

Each language is a separate pass over the same words, so the last cases here are
about the two passes meeting on the word they both gloss.
"""
from __future__ import annotations

from backend.scripts.build_quran_meanings import Harvest, meaning_rows, read_verse


def empty() -> Harvest:
    return Harvest({}, [], [])


def word(**fields) -> dict:
    return {"char_type_name": "word", **fields}


def read(surah: int, verse: dict, into: Harvest, language: str = "en", printed: bool = True) -> None:
    """read_verse with the first pass's arguments, which is what most cases are."""
    read_verse(surah, verse, into, language, printed)


def test_a_word_fills_both_the_spelling_and_the_english():
    found = empty()
    read(1, {
        "verse_key": "1:2",
        "words": [word(text_uthmani="ٱلْحَمْدُ", translation={"text": "All praises"})],
    }, found)
    assert found.uthmani == [(1, 2, 1, "ٱلْحَمْدُ")]
    assert found.meanings == {(1, 2, 1): {"en": "All praises"}}
    assert found.ends == []


def test_the_ayah_end_marker_is_its_own_row_and_takes_no_position():
    """The marker is punctuation the API prints as a word. Numbering it would
    push every later word one out of step with the corpus."""
    found = empty()
    read(1, {
        "verse_key": "1:1",
        "words": [
            word(text_uthmani="بِسْمِ", translation={"text": "In the name"}),
            {"char_type_name": "end", "text_uthmani": "١"},
            word(text_uthmani="ٱللَّهِ", translation={"text": "of Allah"}),
        ],
    }, found)
    assert found.ends == [(1, 1, "١")]
    assert [row[2] for row in found.uthmani] == [1, 2]


def test_a_marker_falls_back_to_plain_text_when_it_has_no_uthmani():
    found = empty()
    read(2, {"verse_key": "2:5", "words": [{"char_type_name": "end", "text": "٥"}]}, found)
    assert found.ends == [(2, 5, "٥")]


def test_anything_that_is_neither_a_word_nor_an_end_is_skipped():
    found = empty()
    read(2, {
        "verse_key": "2:1",
        "words": [{"char_type_name": "pause", "text_uthmani": "ۖ"}],
    }, found)
    assert found == empty()


def test_a_word_with_no_english_still_gets_its_spelling():
    """A particle often has no gloss. Dropping the whole word would leave a hole
    in the printed ayah."""
    found = empty()
    read(2, {"verse_key": "2:2", "words": [word(text_uthmani="لَا", translation={"text": "  "})]}, found)
    assert found.uthmani == [(2, 2, 1, "لَا")]
    assert found.meanings == {}


def test_a_missing_verse_key_files_the_ayah_as_zero_rather_than_guessing():
    found = empty()
    read(3, {"words": [word(text_uthmani="ا", translation={"text": "a"})]}, found)
    assert found.uthmani == [(3, 0, 1, "ا")]


def test_two_verses_pile_into_the_same_harvest():
    """The paging loop reads many pages into one Harvest; each verse restarts
    its own word numbering and nothing carries over."""
    found = empty()
    for ayah in (1, 2):
        read(9, {
            "verse_key": f"9:{ayah}",
            "words": [word(text_uthmani="ا", translation={"text": "a"})],
        }, found)
    assert found.meanings == {(9, 1, 1): {"en": "a"}, (9, 2, 1): {"en": "a"}}


def test_two_harvests_do_not_share_their_lists():
    """A mutable default on the NamedTuple would make every Harvest the same
    three lists, and the second surah would be appended to the first."""
    first, second = empty(), empty()
    read(1, {"verse_key": "1:1", "words": [word(text_uthmani="ا", translation={"text": "a"})]}, first)
    assert second == Harvest({}, [], [])


def test_the_second_language_lands_on_the_same_word():
    """The Urdu pass fetches the same surah again. Both glosses have to end up on
    one row, which is why the harvest is keyed by position and not a flat list."""
    found = empty()
    verse = {"verse_key": "1:1", "words": [word(text_uthmani="بِسْمِ", translation={"text": "In the name"})]}
    read(1, verse, found)
    read_verse(1, {
        "verse_key": "1:1",
        "words": [word(text_uthmani="بِسْمِ", translation={"text": "ساتھ نام"})],
    }, found, "ur", printed=False)
    assert found.meanings == {(1, 1, 1): {"en": "In the name", "ur": "ساتھ نام"}}
    assert meaning_rows(found) == ([(1, 1, 1, "In the name", "ساتھ نام")], 0)


def test_a_later_pass_does_not_print_the_spelling_twice():
    """The Arabic is the same whichever language was asked for, so only the first
    pass collects it. Without this the uthmani rows would double."""
    found = empty()
    verse = {
        "verse_key": "1:1",
        "words": [
            word(text_uthmani="بِسْمِ", translation={"text": "x"}),
            {"char_type_name": "end", "text_uthmani": "١"},
        ],
    }
    read(1, verse, found)
    read_verse(1, verse, found, "ur", printed=False)
    assert found.uthmani == [(1, 1, 1, "بِسْمِ")]
    assert found.ends == [(1, 1, "١")]


def test_a_word_with_urdu_but_no_english_is_dropped_and_counted():
    """Every reader of the table selects `en`. Storing an empty English would say
    the word means nothing, rather than that nobody recorded it."""
    found = empty()
    read_verse(1, {
        "verse_key": "1:3",
        "words": [word(text_uthmani="ٱلرَّحِيمِ", translation={"text": "رحم والا"})],
    }, found, "ur", printed=False)
    assert meaning_rows(found) == ([], 1)


def test_a_word_the_urdu_pass_missed_is_stored_with_no_urdu():
    """A gap stays a gap: NULL says nobody glossed it, which is not the same as
    an empty meaning."""
    found = empty()
    read(1, {"verse_key": "1:4", "words": [word(text_uthmani="مَٰلِكِ", translation={"text": "Master"})]}, found)
    assert meaning_rows(found) == ([(1, 4, 1, "Master", None)], 0)
