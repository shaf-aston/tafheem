"""Read the entries of al-'Ala'i's al-Mukhtalitin (narrators whose memory changed late in life). Pure.

An entry is headed by the man's name; what follows is the scholar's own
sentences, kept whole as the quote. Which of his students heard before or after
the change is not read. A heading joins by the Taqrib's name rule, and by a nisba
of his where it goes on past the name, to one narrator or none (names.join, by
"headed"); any entry that does not goes to the gap table.
"""
from __future__ import annotations

import re

from backend.services.hadith.usul.books import Entry

# The digitiser's row of dots where a page of the edition has no text.
_BLANK = re.compile(r"(?:\.\s){3,}\.?")


def quote(entry: Entry) -> str:
    """The entry's sentences as the book has them, an omitted stretch shown as an ellipsis."""
    return " ".join(_BLANK.sub("… ", entry.text).split())

