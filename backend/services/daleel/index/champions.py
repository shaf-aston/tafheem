"""Champion lists: each common word's best passages in each source, scored at build time.

Why they exist. A search scores every passage its words match, so its cost
grows with how common the words are: قال is in 28,860 passages and scoring
them all is most of a search, while a rare word costs nothing. A word's best
passages do not change between searches, only between builds, so the build
works them out once per common word and source (`fill` below) and a search
reads those few hundred rows instead of scoring tens of thousands.

Why the answer stays exact. FTS5's bm25 score of an OR of words is the sum of
each word's own score (checked over 12,147 passages: no difference at all), so
a passage's score can be put together a word at a time:

    rare words      asked of FTS5 as before, exact, and cheap because rare
    common words    read from their lists; a passage a list leaves out scores
                    no better than that list's last entry (its floor)

That is Fagin's threshold algorithm. A passage the lists left out and no rare
word matched scores no better than the sum of the floors, so when each source's
last kept passage beats that sum, nothing unseen could have taken its place.
When it does not, `best` says so (None) and the search is asked the ordinary
way, so this can only ever be faster, never different.

A listed passage may also hold another common word whose list left it out. Its
score for that word is worked out here (`score`, the same formula FTS5 uses,
checked against FTS5 for every listed passage when the index is built), but
only for passages that could still reach the page.
"""
from __future__ import annotations

import bisect
import heapq
import math
import re
import sqlite3
from collections import Counter
from typing import NamedTuple, Sequence

from backend.services.text import fts

from backend.services.daleel.index.connection import db, has_table

# FTS5's bm25 constants (fts5_aux.c), which `score` has to agree with.
_K1 = 1.2
_B = 0.75

# The columns FTS5 indexes, in order: what a phrase is counted in and what a
# passage's length is. source, book, locator and arabic are UNINDEXED.
SEARCHED = ("english", "roots", "fold")

Scored = tuple[float, int]
"""(score, rowid). Lower is better, as FTS5 ranks it, and a lower rowid wins a tie."""


class Corpus(NamedTuple):
    """The two numbers bm25 needs about the whole index."""

    passages: int
    average_length: float


class Word(NamedTuple):
    """A word with a champion list."""

    word: str
    hits: int
    """Passages holding it anywhere: what its IDF is worked out from."""
    depth: int
    """How many passages per source the build kept. A list shorter than this is
    every passage that source has for the word."""


class Lists(NamedTuple):
    corpus: Corpus
    words: dict[str, Word]
    """By the FTS5 phrase a search writes for the word: `fts.quoted(word)`."""


def stored(conn: sqlite3.Connection) -> Lists | None:
    """This index's champion words, read once per build of the file. None for an
    index built before champion lists existed: every search is then the ordinary one."""
    return db.per_build(conn, _read)


def _read(conn: sqlite3.Connection) -> Lists | None:
    if not has_table(conn, "champion_word"):
        return None
    corpus = conn.execute("SELECT passages, average_length FROM champion_corpus").fetchone()
    if corpus is None:
        return None
    words = {fts.quoted(word): Word(word, hits, depth)
             for word, hits, depth in conn.execute("SELECT word, hits, depth FROM champion_word")}
    return Lists(Corpus(*corpus), words)


def score(word: str, columns: Sequence[str], hits: int, corpus: Corpus) -> float:
    """FTS5's bm25 rank for one word in one passage, worked out without FTS5.

    `columns` are the passage's searched columns, already lower-cased, as the
    trigram tokenizer compares them. A trigram phrase is counted wherever it
    starts, overlaps included, and a column of n characters is n - 2 trigrams.
    """
    found = sum(_count(text, word) for text in columns)
    if not found:
        return 0.0
    idf = math.log((corpus.passages - hits + 0.5) / (hits + 0.5))
    idf = idf if idf > 0 else 1e-6
    length = sum(max(len(text) - 2, 0) for text in columns)
    return -idf * found * (_K1 + 1) / (found + _K1 * (1 - _B + _B * length / corpus.average_length))


def _count(text: str, word: str) -> int:
    n, at = 0, text.find(word)
    while at >= 0:
        n += 1
        at = text.find(word, at + 1)
    return n


def lowered(row: Sequence[str | None]) -> list[str]:
    """A passage's searched columns as `score` reads them."""
    return [(text or "").lower() for text in row]


def best(
    conn: sqlite3.Connection, phrases: Sequence[str], per_source: int, starts: Sequence[int],
) -> list[list[Scored]] | None:
    """Each source's `per_source` best passages for the OR of `phrases`, best
    first, a list per source in `starts` order. None when the lists cannot
    answer this question exactly, and the caller asks FTS5 instead.

    `starts` is where each source's run of rowids begins (share.Spans).
    """
    lists = stored(conn)
    common = [p for p in phrases if lists and p in lists.words]
    # A list must hold one more than the page: its last entry is its floor,
    # and a page ending on the floor ties with what the list left out.
    if not common or any(lists.words[p].depth <= per_source for p in common):
        return None
    words = {p: lists.words[p] for p in common}
    rare = [p for p in phrases if p not in words]
    sources = len(starts)

    def source_of(rowid: int) -> int:
        return max(bisect.bisect_right(starts, rowid) - 1, 0)

    place = {words[p].word: i for i, p in enumerate(common)}
    listed: list[set[int]] = [set() for _ in common]
    lengths = [[0] * sources for _ in common]
    worst = [[-math.inf] * sources for _ in common]
    known: dict[int, float] = {}
    for word, rowid, points in conn.execute(
        f"SELECT word, id, score FROM champion WHERE word IN ({','.join('?' * len(place))})", list(place),
    ):
        i, at = place[word], source_of(rowid)
        listed[i].add(rowid)
        known[rowid] = known.get(rowid, 0.0) + points
        lengths[i][at] += 1
        worst[i][at] = max(worst[i][at], points)

    # A full list's floor is its last entry; a short one is the whole source,
    # so a passage it leaves out does not hold the word at all and adds 0.
    floor = [[worst[i][at] if lengths[i][at] >= words[p].depth else 0.0 for i, p in enumerate(common)]
             for at in range(sources)]

    def unsure_of(known: dict[int, float]) -> dict[int, list[int]] | None:
        """Which passages may still be missing a common word and could reach the
        page if they held each at its floor; None when even that page would
        fail the check at the end, so there is no point reading any text.

        A known sum is the worst a passage can score, so the per_source-th best
        of those is a bar nothing scoring above it can pass.
        """
        by_source: list[list[int]] = [[] for _ in range(sources)]
        for rowid in known:
            by_source[source_of(rowid)].append(rowid)
        unsure: dict[int, list[int]] = {}
        for at, rowids in enumerate(by_source):
            bar = _nth([known[r] for r in rowids], per_source)
            best_case: list[float] = []
            for rowid in rowids:
                missing = [i for i, f in enumerate(floor[at]) if f < 0 and rowid not in listed[i]]
                lowest = known[rowid] + sum(floor[at][i] for i in missing)
                best_case.append(lowest)
                if missing and lowest <= bar:
                    unsure[rowid] = missing
            if _unseen_could_win(_nth(best_case, per_source), floor[at]):
                return None
        return unsure

    # Asked of the lists alone first, which is a millisecond. The rare words
    # can only lower scores, so this is a guess, not a proof: a question it
    # turns away is answered the ordinary way, as exactly, just not faster.
    # A sharper guess (the lists' own sums, no floors) turned away questions
    # the lists could answer: 1282ms against 1144ms over forty questions.
    if unsure_of(known) is None:
        return None

    # Exact sums over the rare words: the ordinary search, made cheap by
    # leaving the common words out of it.
    if rare:
        for rowid, points in conn.execute(
            "SELECT rowid, rank FROM passage WHERE passage MATCH ?", (" OR ".join(rare),),
        ):
            known[rowid] = known.get(rowid, 0.0) + points
    if (unsure := unsure_of(known)) is None:
        return None

    if unsure:
        ids = list(unsure)
        for rowid, *columns in conn.execute(
            f"SELECT rowid, {', '.join(SEARCHED)} FROM passage WHERE rowid IN ({','.join('?' * len(ids))})", ids,
        ):
            text = lowered(columns)
            for i in unsure[rowid]:
                word = words[common[i]]
                known[rowid] += score(word.word.lower(), text, word.hits, lists.corpus)

    by_source: list[list[Scored]] = [[] for _ in range(sources)]
    for rowid, points in known.items():
        by_source[source_of(rowid)].append((points, rowid))
    kept: list[list[Scored]] = []
    for at, scored in enumerate(by_source):
        top = heapq.nsmallest(per_source, scored)
        if _unseen_could_win(top[-1][0] if len(top) >= per_source else math.inf, floor[at]):
            return None
        kept.append(top)
    return kept


def _unseen_could_win(last: float, floors: list[float]) -> bool:
    """Whether a passage no list or rare word saw might beat the last one kept.

    Such a passage scores no better than the floors' sum, so the last kept must
    beat that sum outright. With no full list in this source (every floor 0)
    nothing went unseen.
    """
    unseen = sum(floors)
    return unseen < 0 and not last < unseen


def _nth(scores: list[float], n: int) -> float:
    """The n-th best (lowest) of these, or infinity when there are fewer: then
    every one of them is on the page and none may be skipped."""
    return heapq.nsmallest(n, scores)[-1] if len(scores) >= n else math.inf


# ---- built once, with the index ------------------------------------------------

SCHEMA = """
-- Each common word's best passages in each source, so a search reads them
-- instead of scoring every passage the word is in. See index/champions.py.
DROP TABLE IF EXISTS champion;
DROP TABLE IF EXISTS champion_word;
DROP TABLE IF EXISTS champion_corpus;
CREATE TABLE champion_word (
    word  TEXT PRIMARY KEY,   -- as a search writes it, before quoting
    hits  INTEGER NOT NULL,   -- passages holding it: its IDF
    depth INTEGER NOT NULL    -- passages kept per source; fewer means all of them
) WITHOUT ROWID;
CREATE TABLE champion (
    word  TEXT NOT NULL,
    id    INTEGER NOT NULL,   -- the passage's rowid
    score REAL NOT NULL,      -- FTS5's rank for this word alone
    PRIMARY KEY (word, id)
) WITHOUT ROWID;
CREATE TABLE champion_corpus (
    passages       INTEGER NOT NULL,
    average_length REAL NOT NULL
);
"""


def fill(conn: sqlite3.Connection, least_hits: int, depth: int, say=print) -> int:
    """Work out every common word's champion list. Returns how many words got one.

    Needs `passage` and `passage_meta` finished. A word whose stored scores
    `score` cannot reproduce is left without a list, and said so, rather than
    let a search add up numbers that are not FTS5's.
    """
    conn.executescript(SCHEMA)
    corpus = Corpus(*conn.execute(
        "SELECT count(*), total(" + " + ".join(f"max(length(coalesce({c}, '')) - 2, 0)" for c in SEARCHED)
        + ") * 1.0 / max(count(*), 1) FROM passage",
    ).fetchone())
    conn.execute("INSERT INTO champion_corpus VALUES (?, ?)", corpus)

    kept = 0
    for word in _common_words(conn, least_hits):
        phrase = fts.quoted(word)
        hits = conn.execute("SELECT count(*) FROM passage WHERE passage MATCH ?", (phrase,)).fetchone()[0]
        if hits < least_hits:
            continue
        rows = conn.execute(
            "SELECT id, points FROM ("
            " SELECT f.id, f.points, row_number() OVER (PARTITION BY m.source ORDER BY f.points, f.id) AS place"
            " FROM (SELECT rowid AS id, rank AS points FROM passage WHERE passage MATCH ?) f"
            " JOIN passage_meta m ON m.id = f.id"
            ") WHERE place <= ?",
            (phrase, depth),
        ).fetchall()
        if not _agrees(conn, word, hits, corpus, rows):
            say(f"  champion: {word!r} left out, its scores could not be reproduced")
            continue
        conn.execute("INSERT INTO champion_word VALUES (?, ?, ?)", (word, hits, depth))
        conn.executemany("INSERT INTO champion VALUES (?, ?, ?)", [(word, rowid, points) for rowid, points in rows])
        kept += 1
    conn.commit()
    return kept


def _agrees(conn: sqlite3.Connection, word: str, hits: int, corpus: Corpus, rows: list[tuple[int, float]]) -> bool:
    """Whether `score` gives FTS5's own number for every passage on the list."""
    fts_said = dict(rows)
    ids = list(fts_said)
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for rowid, *columns in conn.execute(
            f"SELECT rowid, {', '.join(SEARCHED)} FROM passage WHERE rowid IN ({','.join('?' * len(chunk))})", chunk,
        ):
            ours = score(word.lower(), lowered(columns), hits, corpus)
            if not math.isclose(ours, fts_said[rowid], rel_tol=1e-9, abs_tol=1e-12):
                return False
    return True


def _common_words(conn: sqlite3.Connection, least_hits: int) -> list[str]:
    """Words that may be in `least_hits` passages, to be counted exactly.

    Arabic from the word index's own vocabulary, English from the English
    column. A whole word is counted per passage there, while the trigram index
    also matches it inside longer words, so the bar here is a quarter of the
    real one: a word just under it as a whole word can still be over it.
    """
    floor = max(least_hits // 4, 1)
    words: list[str] = []
    if has_table(conn, "word"):
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS temp.word_vocab USING fts5vocab(main, word, col)")
        words += [w for (w,) in conn.execute(
            "SELECT term FROM temp.word_vocab WHERE col = 'fold' AND doc >= ? AND length(term) >= ?",
            (floor, fts.TRIGRAM_MIN),
        )]
    english: Counter[str] = Counter()
    for (text,) in conn.execute("SELECT english FROM passage WHERE english != ''"):
        english.update(set(re.findall(r"[a-z]{%d,}" % fts.TRIGRAM_MIN, text.lower())))
    words += sorted(w for w, n in english.items() if n >= floor)
    return list(dict.fromkeys(words))
