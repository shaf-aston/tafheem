"""Join the entries of al-'Ala'i's al-Mukhtalitin (narrators whose memory changed late in life) to narrators. Pure.

An entry is headed by the man's name; what follows is the scholar's own
sentences, kept whole as the quote. Which of his students heard before or after
the change is not read. A heading joins by the Taqrib's name rule, and by a nisba
of his where it goes on past the name, to one narrator or none (names.Index.headed);
any entry that does not is returned with why.
"""
from __future__ import annotations

import re

from backend.services.hadith.usul import names
from backend.services.hadith.usul.books import Entry

# The digitiser's row of dots where a page of the edition has no text.
_BLANK = re.compile(r"(?:\.\s){3,}\.?")


def quote(entry: Entry) -> str:
    """The entry's sentences as the book has them, an omitted stretch shown as an ellipsis."""
    return " ".join(_BLANK.sub("… ", entry.text).split())


def join(entries: dict[int, Entry], people: list[names.Person], size: int, window: int) -> tuple[dict[int, int], dict[int, str]]:
    """({entry key: narrator id}, {entry key: why not}): the man the heading names, when it names one."""
    index = names.Index(people, size)
    return names.one_to_one({key: [p.id for p in index.headed(names.words(entry.head), window)] for key, entry in entries.items()},
                            exclusive=False)
