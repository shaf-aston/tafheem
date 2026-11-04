"""One English line for each Lisan al-Arab and Taj al-Arus entry, kept once made.

Neither book has English, and a reader who cannot read them could not tell an
entry they wanted from one they did not. A line saying what the entry covers,
"cold; and the waist, the middle of a thing", answers that without pretending
to be a translation. They are made ahead of time by
scripts/dictionary/backfill_lexicon_gists.py, never on a reader's press, so the
shelf costs no model call to open.

One file, keyed "book:root", in the same keep-and-reread store as the Maqayees
English (root_english), so the two never disagree about how a file is written.
A root with no line kept simply shows none.
"""
from __future__ import annotations

from pathlib import Path

from backend.services.dictionary.root_english import _is_prose, _keep, _store

GISTS_FILE = Path(__file__).parent.parent.parent / "data" / "dictionary" / "lexicon_gists.json"

# The books a gist is made for: the Arabic ones. Lane is in English already, and
# Ibn Faris has his own English on his own card.
BOOKS = ("lisan", "taj")


def _key(book: str, root: str) -> str:
    return f"{book}:{root}"


def get(book: str, root: str) -> str | None:
    """The line kept for this book's entry on this root, if one has been made."""
    return _store(GISTS_FILE, _is_prose).get(_key(book, root)) or None


def put(book: str, root: str, gist: str) -> None:
    """Keep one line. Only the backfill script calls this."""
    gist = " ".join(gist.split())
    if book in BOOKS and root and gist:
        _keep(GISTS_FILE, _is_prose, _key(book, root), gist)
