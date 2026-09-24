"""Which books Daleel searches. The one place that list is written down.

This is the swap-seam. Search, ranking, the router and the panel all work in
terms of the Source protocol and none of them names a book. Adding one, a fiqh
work included, is: write the adapter, add it here, add it to data/sources.json,
rebuild the index. Nothing downstream changes.

Kept separate from search.py on purpose. A registry that also searched would
give every new book a chance to alter how every other book is found.
"""
from __future__ import annotations

from backend.services.daleel.model import Source
from backend.services.daleel.sources.maqayees import MaqayeesSource
from backend.services.daleel.sources.openiti import OpenItiSource
from backend.services.daleel.sources.quran import QuranSource
from backend.services.daleel.sources.jazariyya import JazariyyaSource
from backend.services.daleel.sources.lexicons import LexiconsSource, credits as lexicon_credits
from backend.services.daleel.sources.library import LibrarySource
from backend.services.daleel.sources.tasheel import TasheelSource
from backend.services.daleel.sources.wiktionary import WiktionarySource

# Order here is the order results are grouped in on screen, so the eye learns
# one shape. The Qur'an is first because it is the book the others explain.
SOURCES: tuple[Source, ...] = (
    QuranSource(),
    # The library, once per entry in sources.json that its books are credited
    # to. Adding a seventh commentary changes neither of these lines: which
    # books they yield is decided in data/quran/editions.json.
    LibrarySource("tafsir"),
    LibrarySource("qul"),
    LibrarySource("translation"),
    # How the Qur'an is recited, which belongs beside what it means and
    # before the grammar books: a question about a letter's sound is
    # answered here, not by Sibawayh's descendants.
    JazariyyaSource(),
    TasheelSource(),
    # The classical books, grouped rather than one entry each: see the note at
    # the top of sources/openiti.py for why thirty-four entries would empty the
    # page. Which books each holds is data/books/openiti-books.json.
    OpenItiSource("nahw-books"),
    OpenItiSource("fiqh-books"),
    MaqayeesSource(),
    # The classical dictionaries, one entry per credit they carry rather than a
    # written list of books. A dictionary added to data/lexicons.db appears here
    # on the next index build with nothing edited; only a book carrying a credit
    # sources.json has never heard of needs anything done, and that is a data
    # file, not this one.
    *(LexiconsSource(credit) for credit in lexicon_credits()),
    WiktionarySource(),
)

# Two of the app's data files are deliberately NOT searched here, and the
# reason is the same in both cases: what they hold is not a quotation.
#
#   nahw_rules/rules.json  its Arabic came out of a PDF backwards, so
#                          "هداية النحو" is stored as "وحنلا ةياده". The rule
#                          engine only ever matches it against itself, which is
#                          why that has never mattered; quoting it to a reader
#                          would put nonsense on the screen under a book's name.
#   sarf/patterns.json     a table of endings, not prose. There is no sentence
#                          in it that anyone would cite.
#
# Both are worth revisiting: rules.json needs re-extracting from the PDF, and
# only then is it quotable.


def by_id(source_id: str) -> Source | None:
    """The adapter for a source id, or None when nothing claims that id."""
    return next((s for s in SOURCES if s.id == source_id), None)
