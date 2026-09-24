"""The Qur'an's library: every commentary and translation, as quotations.

One adapter for all of them, because they all have one shape. It replaces the
adapter that read one tafsir out of its own database, and that is the point:
the seventh book costs nothing here, only a line in the manifest.

Which books reach the index is decided in `data/quran/editions.json`, one flag
per book. A brief commentary is worth searching. A multi-volume one is worth
reading and costs far more to index than searching it is worth, so it is read
and not searched, and the manifest says which is which.

The locator carries the book's name as well as the ayah, which is not decoration.
Several books share one entry in sources.json, so the badge names the library
rather than the book; the address printed beside every quotation is then the
thing that says which of them said it. "تفسير الجلالين 2:255" is how a person
would cite it anyway.

No roots are worked out here. The Qur'an's own passages carry roots because the
corpus tagged every word by hand; asking the dictionary for the root of every
word of every commentary would be millions of lookups for a book whose Arabic is
already searchable letter by letter through the folded text.
"""
from __future__ import annotations

from typing import Iterable

from backend.services import quran_library
from backend.services.daleel.model import Passage


class LibrarySource:
    """Every searchable book credited to one entry in sources.json.

    One instance per credit, because the badge, the confidence and the footer
    all resolve from that key and a book must not be shown under the wrong one.
    Ibn Kathir came from Quran.com and the rest come from QUL; they are two
    different claims about where a quotation is from, so they stay two sources.

    A credit with no installed searchable books yields nothing, which is the
    ordinary state before anything has been downloaded, not an error.
    """

    def __init__(self, credit: str) -> None:
        self.id = credit

    def passages(self) -> Iterable[Passage]:
        for edition in quran_library.searchable(self.id):
            arabic = edition["language"] == "ar"
            for passage_id, text in quran_library.passages_of(edition["id"]):
                yield Passage(
                    source=self.id,
                    book=edition["name"],
                    locator=f"{edition['name']} {passage_id}",
                    # The book's own language decides which column it belongs
                    # in. An Arabic commentary put in the English column would
                    # be searched as English and found by nothing.
                    arabic=text if arabic else "",
                    english="" if arabic else text,
                )
