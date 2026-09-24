"""Reading the origin sense out of a whole-entry translation.

The gloss under the Arabic used to come from a model reading a photograph of the
page. Where the whole entry has been translated from the typed Arabic, its
opening sentence says the same thing and was made properly, so it is used
instead, and the badge over it changes with it. Every case here is a shape the
real translations take.
"""

import json

import pytest

from backend.services import root_gloss

REAL = [
    ("The letters hamza, bā', and dāl, in their formation, point to length of time and to "
     "wildness. They say al-abad is time, eternity.",
     "The letters hamza, bā', and dāl, in their formation, point to length of time and to "
     "wildness."),
    # He closes the enumeration with a full stop and states the sense after it.
    ("The letters bā', ḥā' and rā'. Al-Khalīl said: the sea was called baḥr because of its "
     "spreading out. One says baḥrun ujājun.",
     "The letters bā', ḥā' and rā'. Al-Khalīl said: the sea was called baḥr because of its "
     "spreading out."),
    # Some entries open "As for…"; that already says something.
    ("As for the letters bā', rā' and hamza, they are two roots. The first is creating.",
     "As for the letters bā', rā' and hamza, they are two roots."),
]


@pytest.mark.parametrize("translation, opening", REAL)
def test_the_opening_sentence_is_the_origin_sense(translation, opening):
    assert root_gloss.opening_of(translation) == opening


def test_a_full_stop_inside_a_name_does_not_end_the_sentence():
    """This text is full of stops that end nothing, al-Khalīl, Abū 'Ubayd."""
    whole = "The letters kāf, tā' and bā' point to gathering, said Abū 'Ubayd. Then he added more."
    assert root_gloss.opening_of(whole).endswith("said Abū 'Ubayd.")


def test_only_the_first_paragraph_is_ever_read():
    """What follows the opening paragraph is the words built on the sense, not
    the sense, including the numbered list, which must never become the gloss."""
    whole = "The letters ʿayn, qāf and dāl point to tying.\n1. al-ʿaqd, the knot.\n2. al-ʿaqīda."
    assert root_gloss.opening_of(whole) == "The letters ʿayn, qāf and dāl point to tying."


@pytest.mark.parametrize("nothing", ["", "   ", "\n\n"])
def test_nothing_in_gives_nothing_out(nothing):
    """No translation is not a blank gloss to print, it is the older gloss's turn."""
    assert root_gloss.opening_of(nothing) == ""


def test_every_stored_translation_yields_an_opening_that_says_something():
    """A standing check on the real store: no root may end up with a gloss that
    only names the letters the reader just typed.

    Unless the book itself says no more. عشط is one line long in the printed
    edition, "the letters ayn, shin and ta" and nothing after it, and no
    reading of that entry can produce a meaning it does not contain. Those are
    allowed through, and only those: a gloss that says nothing has to be matched
    by an entry that says nothing.
    """
    from backend.services.root_english import STORE_FILE

    if not STORE_FILE.is_file():
        pytest.skip("no translations kept on this machine yet")
    kept = json.loads(STORE_FILE.read_text(encoding="utf-8"))
    silent = [
        root for root, whole in kept.items()
        if root_gloss._says_only_the_letters(root_gloss.opening_of(whole))
        and not root_gloss._says_only_the_letters(whole)
    ]
    assert not silent, silent
