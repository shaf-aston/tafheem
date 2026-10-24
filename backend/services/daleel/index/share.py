"""Each source's share of the matches: its best few, so one big book cannot fill the page.

Two ways of cutting it, which pick the same passages:

- `best_per_source`, the ordinary one. Every source's passages are one unbroken
  run of rowids, because the build writes one source after another, so which
  source a rowid is in is found by stepping along a dozen run starts, and each
  source keeps its best few in a heap of that size. One pass over the matches,
  O(M log k) for M matches and k a share, and nothing is sorted whole.
- The SQL one, through `passage_meta` with a window function. Right whatever
  order the index was written in, and the only one that can narrow to books,
  so it is used for a book filter and for an index whose runs are broken.
"""
from __future__ import annotations

import bisect
import heapq
import logging
import sqlite3
from typing import NamedTuple

from backend.services.text import fts

from backend.services.daleel.index.connection import db, has_table
from backend.services.daleel.index.row import COLUMNS, IndexedPassage

log = logging.getLogger(__name__)


def fairly(
    conn: sqlite3.Connection, match: str, per_source: int, books: tuple[str, ...] = (),
) -> list[IndexedPassage]:
    """The best `per_source` passages each source has for that match, in one question.

    The matching is left to the trigram index, which answers in rowids and
    never unpacks a passage; only the rows that survive the share are fetched
    in full.

    The share is cut by FTS5's own relevance score, not by passage order. Cut
    by order, a source with many matches kept its earliest ones and its best
    was often never ranked: over sixteen questions on the real index, 112 of
    156 sources kept their best passage that way and 149 do now. Putting
    passages holding every typed word first was tried too and kept only 121.
    """
    if not books and (spans := source_spans(conn)):
        return best_per_source(conn, match, per_source, spans)

    only, chosen = fts.only_in("book", books)
    return list(map(IndexedPassage._make, conn.execute(
        f"SELECT {COLUMNS} FROM ("
        f" SELECT m.id, row_number() OVER (PARTITION BY m.source ORDER BY f.rank, m.id) AS place"
        f" FROM (SELECT rowid AS id, rank FROM passage WHERE passage MATCH ?) f"
        f" JOIN passage_meta m ON m.id = f.id{only}"
        f") share JOIN passage p ON p.rowid = share.id WHERE share.place <= ?",
        (match, *chosen, per_source),
    )))


class Spans(NamedTuple):
    """Where each source's run of rowids starts, in rowid order."""

    starts: tuple[int, ...]
    sources: tuple[str, ...]


def source_spans(conn: sqlite3.Connection) -> Spans | None:
    """This index's source runs, read once per build of the file."""
    return db.per_build(conn, _read_spans)


def _read_spans(conn: sqlite3.Connection) -> Spans | None:
    """The source runs of this index, or None when they are not unbroken.

    None sends the search to passage_meta, which is right whatever the order,
    so an index written some other way is slower rather than wrong.
    """
    if not has_table(conn, "passage_meta"):
        return None
    runs = conn.execute(
        "SELECT min(id), max(id), count(*), source FROM passage_meta GROUP BY source ORDER BY min(id)"
    ).fetchall()
    if not runs:
        return None
    if any(last - first + 1 != count for first, last, count, _ in runs):
        log.warning("passage rowids are not one run per source; searching via passage_meta")
        return None
    return Spans(tuple(run[0] for run in runs), tuple(run[3] for run in runs))


def best_per_source(
    conn: sqlite3.Connection, match: str, per_source: int, spans: Spans,
) -> list[IndexedPassage]:
    """The `per_source` best-scored matches of each source, then those rows in full.

    FTS5 scores lower as better, and rowid breaks a tie, as the SQL version
    orders them; the heap keeps the worst of the best on top to be replaced.
    Handed back a source at a time in the order of their names, as the SQL
    version's window hands them back, so a tie later on falls the same way.
    """
    kept: list[list[tuple[float, int]]] = [[] for _ in spans.starts]
    ends = (*spans.starts[1:], float("inf"))
    # FTS5 hands rowids back in order, so the source almost always stays the
    # same as the last match's: its run is found by binary search only when the
    # rowid steps out of it, not looked up for every match.
    at = 0
    for rowid, score in conn.execute("SELECT rowid, rank FROM passage WHERE passage MATCH ?", (match,)):
        if not spans.starts[at] <= rowid < ends[at]:
            at = max(bisect.bisect_right(spans.starts, rowid) - 1, 0)
        heap = kept[at]
        if len(heap) < per_source:
            heapq.heappush(heap, (-score, -rowid))
        elif (-score, -rowid) > heap[0]:
            heapq.heapreplace(heap, (-score, -rowid))

    by_name = sorted(range(len(kept)), key=spans.sources.__getitem__)
    ids = [-rowid for at in by_name for _, rowid in sorted(kept[at], reverse=True)]
    if not ids:
        return []
    rows = {row[0]: IndexedPassage._make(row[1:]) for row in conn.execute(
        f"SELECT p.rowid, {COLUMNS} FROM passage p WHERE p.rowid IN ({','.join('?' * len(ids))})", ids,
    )}
    return [rows[rowid] for rowid in ids if rowid in rows]
