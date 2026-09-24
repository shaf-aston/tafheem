"""The one-line origin sense in English, taken from the entry's own translation.

There are two English glosses of a root's origin sense in this app and they are
not worth the same. One was read off a photograph of the printed page by a model
and has never been proofread, it is badged a guess, and it is wrong where the
Arabic beside it is not. The other is the first sentence of the whole-entry
translation, which was made from the typed Arabic with the Arabic in front of it
and read back by a second reader against it.

They say the same thing, because Ibn Faris always opens an entry the same way:
he names the root's letters and states the one sense they share. So wherever the
whole entry has been translated, the better gloss already exists and costs
nothing, this reads it out.

No file, no model, no network: one sentence in, one sentence out. Whether a root
has a translation at all is the caller's business, not this module's.
"""
from __future__ import annotations

import re
import unicodedata

# A full stop ends a sentence only where a new one begins. This text is full of
# stops that end nothing, al-Khalīl, Abū 'Ubayd, transliterated words; so the
# split needs the capital, quote or brace that starts the sentence after it.
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Zʻʿ'\"{(‘“])")

# "The letters bā', ḥā' and rā'." on its own tells the reader the letters they
# just typed. Ibn Faris sometimes closes the enumeration with a full stop and
# states the sense in the sentence after, so that sentence is taken as well; 
# the same question the builder asks of the Arabic, asked here of the English:
# once the letter names and the words joining them are struck out, is anything
# left? The names are the transliteration the translation brief prescribes,
# compared with the length marks and hamza signs off, so bā' and ba are one word.
_LETTER_NAMES = frozenset("""
    hamza alif ba ta tha jim ha kha dal dhal ra zay za sin shin sad dad
    ayn ghayn fa qaf kaf lam mim nun waw ya weak
""".split())
_JOINING = frozenset("""
    the letter letters and or as for know that they are is a an of with after
    them it this these two three four five
""".split())
_MARKS = re.compile(r"[̀-ͯ'ʻʼʿ‘’ʾ`]")


def _says_only_the_letters(sentence: str) -> bool:
    """Whether a sentence names the root's letters and nothing more."""
    plain = _MARKS.sub("", unicodedata.normalize("NFD", sentence.lower()))
    words = re.findall(r"[a-z]+", plain)
    return bool(words) and not (set(words) - _LETTER_NAMES - _JOINING)


def opening_of(translation: str) -> str:
    """The origin sense out of a whole-entry translation, or "" if there is none.

    The opening paragraph is the origin sense, the brief the translation is made
    to says so, and its first sentence is the statement itself; what follows is
    already the words built on it.

    Sixteen entries have no opening statement at all: Ibn Faris names the letters
    and goes straight to the words built on them. For those the first word he
    defines is the nearest thing to an origin sense the entry has, so the search
    runs on into the lines below rather than showing a reader the letters they
    just typed.
    """
    taken = ""
    for line in translation.strip().split("\n"):
        line = line.strip().lstrip("0123456789.) ")
        if not line:
            continue
        # Each line starts the search again. Carrying "The letters fa, dal and
        # jim." onto the front of the definition below it would show the reader
        # the letters they just typed and then the answer, which is the thing
        # this function exists to stop.
        taken = ""
        for sentence in _SENTENCE.split(line):
            taken = f"{taken} {sentence}".strip()
            if not _says_only_the_letters(taken):
                return taken
    return taken
