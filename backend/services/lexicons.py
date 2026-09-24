"""What the classical dictionaries say about a root, read from data/lexicons.db.

The only thing that opens that database. It is built once by
scripts/build_lexicons.py, which is also where the books, their licences and the
reason each one is readable at all are written down.

This is not root_meaning and does not replace it. That module answers one
question in one sentence, what these three letters have meant since the
beginning, and it answers it from one book. This one hands over whole entries
from several books at once, which is a different thing: a reference to read, not
a headline to show. They sit side by side in the Dictionary tab for that reason.

Nothing here writes, and nothing here shortens an entry. A book that says a great
deal about a root says all of it; how much of that is shown at once is the page's
business, not this module's.
"""
from __future__ import annotations

import logging
import sqlite3
import zlib
from pathlib import Path
from typing import Iterator

from backend.services.arabic_text import normalize_root
from backend.services.root_meaning import read_fold
from backend.services.readonly_db import ReadOnlyDb

logger = logging.getLogger(__name__)

DATABASE = Path(__file__).parent.parent / "data" / "lexicons.db"

# The one table of which letters count as the same, أ and ا, ى and ي. It lives
# beside the root book because that book was the first to need it, and it is read
# from there rather than copied here: two tables that disagree about the alphabet
# would send the same root to two different entries.
_FOLD_BESIDE = Path(__file__).parent.parent / "data" / "maqayees"

MISSING, BROKEN, READY = "missing", "broken", "ready"

_fold: dict[int, int] | None = None

_db = ReadOnlyDb(lambda: DATABASE)


def status() -> str:
    """MISSING when the book was never built, BROKEN when it will not open."""
    if not DATABASE.exists():
        return MISSING
    try:
        _db().execute("SELECT 1 FROM entry LIMIT 1").fetchone()
        return READY
    except sqlite3.Error as exc:
        logger.warning("lexicons.db is there but will not be read: %s", exc)
        return BROKEN


def books() -> list[dict]:
    """Every dictionary held, in the order they should be shown."""
    db = _db()
    if db is None:
        return []
    try:
        rows = db.execute(
            "SELECT b.id, b.title, b.english, b.author, b.died, b.language,"
            "       b.source, COUNT(DISTINCT e.root) AS roots"
            "  FROM book b LEFT JOIN entry e ON e.book = b.id"
            " GROUP BY b.id ORDER BY b.ord"
        ).fetchall()
    except sqlite3.Error:
        return []
    return [dict(row) for row in rows]


def credits() -> list[str]:
    """Which entries in data/sources.json the books here are credited to.

    Read from the books themselves rather than written down a second time, which
    is what makes a new dictionary searchable in Daleel without a line of code:
    build_lexicons.py puts the book in, this finds it, and the Daleel registry
    grows a source for it. A book credited to something already listed costs
    nothing at all; a book with a new credit needs that credit adding to
    sources.json, which is data.
    """
    db = _db()
    if db is None:
        return []
    try:
        rows = db.execute(
            "SELECT source FROM book GROUP BY source ORDER BY MIN(ord)"
        ).fetchall()
    except sqlite3.Error as exc:
        logger.warning("could not read which books are here: %s", exc)
        return []
    return [row["source"] for row in rows]


def entries_by_credit(credit: str) -> Iterator[tuple[str, str, str]]:
    """(book title, root, entry) for every entry credited to one source.

    Streamed one row at a time: these three books are sixty-six million
    characters between them, and the index build reads all of it.
    """
    db = _db()
    if db is None:
        return
    try:
        rows = db.execute(
            "SELECT b.title, e.head, e.body"
            "  FROM entry e JOIN book b ON b.id = e.book"
            " WHERE b.source = ? ORDER BY b.ord, e.rowid",
            (credit,),
        )
        for title, head, body in rows:
            yield title, head, zlib.decompress(body).decode("utf-8")
    except sqlite3.Error as exc:
        logger.warning("could not read the books credited to %r: %s", credit, exc)


def _folded(key: str) -> str:
    global _fold
    if _fold is None:
        _fold = read_fold(_FOLD_BESIDE)
    return key.translate(_fold) if _fold else key


def entries_for(root: str) -> list[dict]:
    """Every book's entry for this root, best-attested spelling first.

    The letters typed answer for themselves first. Only a book with nothing
    under them is asked again under a folded spelling, so a root a book really
    does hold can never be answered by a different one that merely looks like
    it. And a folded spelling that two different roots share, هنأ and هنا, is
    refused outright rather than settled by whichever was written first: a
    reader shown the wrong root's entry has no way of knowing.
    """
    db = _db()
    key = normalize_root(root)
    if db is None or not key:
        return []

    try:
        rows = db.execute(
            "SELECT b.id, b.title, b.english, b.author, b.died, b.language,"
            "       b.source, b.ord,"
            "       e.head, e.body, e.root"
            "  FROM entry e JOIN book b ON b.id = e.book"
            " WHERE e.root = ? ORDER BY b.ord, LENGTH(e.body) DESC",
            (key,),
        ).fetchall()
        answered = {row["id"] for row in rows}

        # The second way in, for a reader who writes امر where the book wrote
        # أمر. One book at a time: Lisan may hold the exact spelling while Lane
        # holds only the folded one, and the reader should get both.
        loose = db.execute(
            "SELECT b.id, b.title, b.english, b.author, b.died, b.language,"
            "       b.source, b.ord,"
            "       e.head, e.body, e.root"
            "  FROM entry e JOIN book b ON b.id = e.book"
            " WHERE e.folded = ?"
            "   AND (SELECT COUNT(DISTINCT root) FROM entry"
            "         WHERE folded = e.folded AND book = e.book) = 1"
            " ORDER BY b.ord, LENGTH(e.body) DESC",
            (_folded(key),),
        ).fetchall()
    except sqlite3.Error as exc:
        logger.warning("could not read the dictionaries for %r: %s", root, exc)
        return []

    # Merged, then put back into the books' own order. Without this a book that
    # happened to hold the exact spelling would jump ahead of the ones that only
    # matched folded, and the shelf would reorder itself from root to root.
    found = sorted(
        list(rows) + [row for row in loose if row["id"] not in answered],
        key=lambda row: (row["ord"], -len(row["body"])),
    )
    # One card per book, not per entry. A book returns to a root in a later
    # volume, Lane adds a supplement to كتب and Lisan says more about هنا, and
    # shown as separate rows those are two cards with the same name and the same
    # author, which reads as the page having repeated itself. They are the same
    # book on the same root, so they are one entry with a break between them.
    shelf: dict[str, dict] = {}
    for row in found:
        said = zlib.decompress(row["body"]).decode("utf-8")
        if row["id"] in shelf:
            shelf[row["id"]]["text"] += "\n\n" + said
            continue
        shelf[row["id"]] = {
            "book": row["id"],
            "title": row["title"],
            "english": row["english"],
            "author": row["author"],
            "died": row["died"],
            "language": row["language"],
            "source": row["source"],
            # The spelling this book files it under, sent only when it differs
            # from what was typed, so the page can say "filed under أمر" rather
            # than leaving the reader wondering why the letters changed.
            "filed_under": row["head"] if row["root"] != key else None,
            "text": said,
        }
    return list(shelf.values())
