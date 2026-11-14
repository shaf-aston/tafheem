"""Very common words scored only where they can still change the page (MaxScore).

Why. A search's cost is the number of passages it scores, and a word like الا
(in half of all passages), قال or علي makes that number huge while adding
almost nothing to any score: bm25 gives a word in half the passages an IDF
near zero. On the real index الا alone was 58 of the 92ms of لا إله إلا الله.

How it stays exact. This is Turtle and Flood's MaxScore (1995). A passage's
score is the sum of each phrase's own score (see champions), and one word can
never add more than its `ceiling`. So:

    1. Score every passage holding an informative phrase, leaving the very
       common words out. Each source's per_source-th best of those is a bar.
    2. A passage further from the bar than all the common words' ceilings
       together cannot reach the page, and neither can a passage holding only
       common words. Nothing needs to be worked out for them.
    3. FTS5 scores the common words only for the passages near a bar, and
       for every passage of a source with too few informative ones to set a
       bar. Its own bm25, so the sum is the score scoring every match gives.

Why this is cheap, and stays cheap on a cold server: finding which passages
hold a word is fast (FTS5 walks the word's list), working out a score for
each is what costs. Here the near passages are picked before any score is
worked out, as a filter FTS5 cannot turn into one lookup per rowid
(`rowid+0`), so only they are scored. Only the index is read, never a
passage's text, and the index is what every search reads anyway, so it
stays in memory: a passage's text mostly does not.

The page is the one scoring every match picks; only the work shrinks.
"""
from __future__ import annotations

import bisect
import heapq
import json
import math
import sqlite3
from typing import Sequence

from backend.config import get_settings

from backend.services.daleel.index import champions
from backend.services.daleel.index.champions import Scored

_LAST_ROWID = (1 << 63) - 1


def best(
    conn: sqlite3.Connection, phrases: Sequence[str], per_source: int, starts: Sequence[int],
) -> list[list[Scored]] | None:
    """Each source's `per_source` best passages for the OR of `phrases`, best
    first, a list per source in `starts` order, as `share.scored` returns them.

    None, before any searching, when no phrase is common enough to leave out
    or every phrase is: the ordinary search is then no slower.
    """
    lists = champions.stored(conn)
    if lists is None:
        return None
    settings = get_settings()
    least = settings.daleel_skip_word_share * lists.corpus.passages
    common = [p for p in phrases if p in lists.words and lists.words[p].hits >= least]
    rest = [p for p in phrases if p not in common]
    if not common or not rest:
        return None

    words = [lists.words[p] for p in common]
    reach = sum(champions.ceiling(word.hits, lists.corpus) for word in words)
    lasts = (*(start - 1 for start in starts[1:]), _LAST_ROWID)

    def source_of(rowid: int) -> int:
        return max(bisect.bisect_right(starts, rowid) - 1, 0)

    # 1. The informative phrases alone. Their sum is the worst each passage can
    # score, since a common word only ever lowers (improves) it.
    partial = dict(conn.execute("SELECT rowid, rank FROM passage WHERE passage MATCH ?", (" OR ".join(rest),)))
    by_source: list[list[Scored]] = [[] for _ in starts]
    for rowid, points in partial.items():
        by_source[source_of(rowid)].append((points, rowid))

    # 2. Per source, which passages may still reach the page.
    final: dict[int, float] = {}
    near: list[int] = []
    runs: list[list[int]] = []  # [first, last] rowids of sources scored whole
    for at, scored in enumerate(by_source):
        # Fewer informative passages than the page holds: no bar (infinity),
        # since the page also takes passages holding only common words.
        bar = heapq.nsmallest(per_source, scored)[-1][0] if len(scored) >= per_source else math.inf
        if -reach > bar:
            near += [rowid for points, rowid in scored if points - reach <= bar]
        elif runs and runs[-1][1] + 1 == starts[at]:
            runs[-1][1] = lasts[at]
        else:
            runs.append([starts[at], lasts[at]])

    # 3. The common words added where they may count.
    either = " OR ".join(common)
    for first, last in runs:
        for rowid, points in conn.execute(
            "SELECT rowid, rank FROM passage WHERE passage MATCH ? AND rowid BETWEEN ? AND ?", (either, first, last),
        ):
            final[rowid] = partial.get(rowid, 0.0) + points
        for rowid, points in partial.items():
            if first <= rowid <= last:
                final.setdefault(rowid, points)
    if near:
        for rowid in near:
            final[rowid] = partial[rowid]
        for rowid, points in conn.execute(
            "SELECT rowid, rank FROM passage WHERE passage MATCH ? AND rowid+0 IN (SELECT value FROM json_each(?))",
            (either, json.dumps(near)),
        ):
            final[rowid] += points

    kept: list[list[Scored]] = [[] for _ in starts]
    for rowid, points in final.items():
        kept[source_of(rowid)].append((points, rowid))
    return [heapq.nsmallest(per_source, scored) for scored in kept]
