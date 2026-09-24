"""Every book of text hung on the ayahs: the tafsirs and the translations.

This module is the only thing that opens library.db, the same rule
quran_corpus.py, quran_meanings.py and quran_layout.py follow for their own files.

One book is an *edition*. They all have one shape, so one file holds all of them
and this one module reads all of them. A hundred editions cost no more code than
one, which is the whole reason the library exists rather than a tafsir module, a
translation module, and a new module per book after that.

A tafsir does not comment one ayah at a time. It commonly takes a run of them
together, 78:1-10 is one passage, so a passage is stored once and records which
ayahs it covers. Asking about any ayah of a run returns that whole passage and
says which ayahs it was written about, because a reader handed commentary on ten
ayahs is entitled to know that is what they are reading.

Built by scripts/import_quran_editions.py. If it has never been run the file is
simply absent, `is_built()` is False, and the app shows no books at all rather
than an empty panel. A missing file is a valid state; it means "not imported yet".

The text is plain, with markup already stripped at import. Nothing here puts HTML
back, so nothing downstream has to defend against it.
"""
from __future__ import annotations

from backend.config import data_path
from backend.services.readonly_db import ReadOnlyDb

# Everything about a book except its text. Listed once here so the two queries
# below and the API cannot drift apart on which columns a book is described by.
_ABOUT = ("id, kind, language, name, short, author, licence, origin, credit, "
          "indexed, confidence, passages, ayahs")


def is_built() -> bool:
    return data_path("quran_library_path").exists()


_db = ReadOnlyDb(lambda: data_path("quran_library_path"))


def editions() -> list[dict]:
    """Every installed book, in the order the manifest names them.

    Not cached. It was, and the cache was wrong in the one case that matters: a
    machine where the library has not been imported yet answers "no books", and
    caching that answer means importing them changes nothing until the server is
    restarted. Ten rows out of an open connection is not worth a stale answer.
    """
    db = _db()
    if db is None:
        return []
    return [dict(row) for row in db.execute(f"SELECT {_ABOUT} FROM edition ORDER BY ordinal")]


def of_kind(kind: str) -> list[dict]:
    """Just the tafsirs, or just the translations, in manifest order."""
    return [edition for edition in editions() if edition["kind"] == kind]


def searchable(credit: str) -> list[dict]:
    """The books Daleel may search inside, of one credit, in manifest order.

    Which books those are is a decision per book in the manifest, not a rule:
    a brief commentary is worth having in the search index and a multi-volume
    one costs far more to index than it is worth searching.
    """
    return [
        edition for edition in editions()
        if edition["indexed"] and edition["credit"] == credit
    ]


def passages_of(edition_id: str):
    """One book's passages, streamed, as (how to cite it, the text).

    Streamed rather than returned: the index builder walks every book in turn
    and a long commentary is hundreds of megabytes of prose.
    """
    db = _db()
    if db is None:
        return
    for row in db.execute(
        "SELECT id, text FROM passage WHERE edition = ? ORDER BY id", (edition_id,)
    ):
        yield row["id"], row["text"]


def for_surah(surah: int, edition_id: str) -> dict[int, str]:
    """One book's text for a whole surah, keyed by ayah.

    A whole surah at once rather than an ayah at a time, because the reading view
    shows every ayah of it: al-Baqarah asked one ayah at a time is 286 requests,
    which is the thing the surah endpoint was built to stop doing. The scan walks
    (edition, surah) straight down the covers primary key.

    Ayahs the book says nothing about are simply absent from the result, which is
    what lets the caller draw a line only where there is one.
    """
    db = _db()
    if db is None:
        return {}
    rows = db.execute(
        """
        SELECT covers.ayah AS ayah, passage.text AS text
        FROM covers
        JOIN passage ON passage.edition = covers.edition AND passage.id = covers.passage
        WHERE covers.edition = ? AND covers.surah = ?
        """,
        (edition_id, surah),
    )
    return {row["ayah"]: row["text"] for row in rows}


def for_ayah(surah: int, ayah: int, ids: list[str] | None = None) -> list[dict]:
    """What every book says about one ayah, in manifest order.

    `ids` narrows it to particular books; None means all of them. An id nobody
    has installed simply returns nothing for that book, rather than an error: the
    reader's saved choice must not be able to break the page after a book is
    removed from the manifest.
    """
    db = _db()
    if db is None:
        return []

    # Narrowed in the query, not after it. The panel shows one book at a time, so
    # filtering in Python meant SQLite fetched all ten passages for this ayah and
    # nine of them were dropped: with a full Arabic commentary among them that is
    # most of the work of the lookup, done for nothing.
    narrow = ""
    args: list = [surah, ayah]
    if ids is not None:
        if not ids:
            return []
        narrow = f" AND covers.edition IN ({','.join('?' * len(ids))})"
        args.extend(ids)

    found = {
        row["edition"]: row
        for row in db.execute(
            f"""
            SELECT covers.edition AS edition, covers.passage AS passage, passage.text AS text
            FROM covers
            JOIN passage ON passage.edition = covers.edition AND passage.id = covers.passage
            WHERE covers.surah = ? AND covers.ayah = ?{narrow}
            """,  # noqa: S608, the only thing interpolated is one ? per id
            args,
        )
    }
    if not found:
        return []

    # Which other ayahs each of those passages was written about. One query for
    # all of them: the join walks (edition, surah) down the covers primary key,
    # so this does not become a query per book.
    spans: dict[str, list[int]] = {}
    for row in db.execute(
        f"""
        SELECT run.edition AS edition, run.ayah AS ayah
        FROM covers AS here
        JOIN covers AS run
          ON run.edition = here.edition
         AND run.passage = here.passage
         AND run.surah = here.surah
        WHERE here.surah = ? AND here.ayah = ?{narrow.replace("covers.", "here.")}
        ORDER BY run.edition, run.ayah
        """,  # noqa: S608, the only thing interpolated is one ? per id
        args,
    ):
        spans.setdefault(row["edition"], []).append(row["ayah"])

    # Only what a panel needs to draw one passage. The rest of a book's
    # description, its licence and where it came from, is asked for once from
    # `editions()` rather than repeated on every ayah the reader opens.
    return [
        {
            "edition": edition["id"],
            "kind": edition["kind"],
            "language": edition["language"],
            "name": edition["name"],
            "author": edition["author"],
            "credit": edition["credit"],
            "confidence": edition["confidence"],
            "surah": surah,
            "ayah": ayah,
            "passage": found[edition["id"]]["passage"],
            "text": found[edition["id"]]["text"],
            "covers": spans.get(edition["id"], [ayah]),
        }
        for edition in editions()
        if edition["id"] in found
    ]
