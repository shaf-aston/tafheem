"""Find the passages, put the best first, and say how strong each match is.

Two jobs, deliberately kept apart. Fetching candidates needs the index and so
needs SQLite; deciding which candidate is the better answer is a rule about
words and needs nothing, so `rank_of` below is pure and is tested on its own.

Two sharp edges in here, both found by running the thing:

The trigram index cannot match anything shorter than three characters, and it
does not complain when asked to, it simply returns nothing. Arabic is full of
two-letter words, so a search for أب would quietly find zero passages and look
like an honest "not in the book". Short terms are matched a different way.

And a trigram index matches *substrings*, which is not the same as tolerating a
typo: الرحييم is not a substring of anything, so it found nothing at all. What
does tolerate a typo is comparing the query's own three-letter runs against the
book's, because a misspelt word still shares most of them with the word meant.
That runs only when the ordinary search has already come back empty, so it
costs nothing on a query that was spelled correctly, and it is reported as a
loose match rather than passed off as a clean find.
"""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass

from backend.config import data_path, get_settings
from backend.services.daleel import registry
from backend.services.daleel.expand import Expansion, expand
from backend.services.daleel.lexicon import DictionaryLexicon

log = logging.getLogger(__name__)

# The shortest string SQLite's trigram tokenizer can match. Not a preference,
# a property of the tokenizer, so it is a constant here and not a setting.
# expand.py is told this number rather than carrying its own: two copies of it
# would let a config change switch off typo tolerance with nothing to show for
# it, because _runs() would go on returning nothing for a shorter term.
_TRIGRAM_MIN = 3

# How many two-letter words one question may put to the word index. It was a
# cap on full scans, which is why the number is small; each one is now an
# indexed lookup of a millisecond or two, so it is only a bound on how many
# queries one request may fire and could safely be raised.
_MAX_SHORT_TERMS = 6

# How many words in total may be put to the index at once. A seven-word English
# question expands into roughly forty and took three seconds to answer; past
# this many, more terms stop narrowing the search and start widening it.
#
# Twelve, not the twenty-four it was, because the second twelve were not
# earning their keep. Measured over ten questions against the real index: eight
# of them showed exactly the same twelve passages either way, and the other two
# changed one or two of the twelve. What it cost was the whole tail of the
# search: "the mercy of god" fell from 1.7 seconds to 0.35. Six was tried too
# and is too few, losing half the passages on the longer questions.
_MAX_TERMS = 12

# How many rows are ranked before the best are kept. Ranking is cheap and the
# index is small; this only stops a very common root from dragging thousands of
# rows into memory.
_CANDIDATE_FACTOR = 20

_MATCH_ALL = "exact"
_MATCH_SOME = "partial"
_MATCH_RELATED = "related"
_MATCH_ROOT = "root"
_MATCH_LOOSE = "loose"


@dataclass(frozen=True)
class Hit:
    """One quotation, and how it was found."""

    source: str
    book: str
    """Which book of that source it is. With thirty-four books under one badge the
    badge no longer says which one this is."""
    locator: str
    arabic: str
    english: str
    match: str
    """One of exact / partial / root / loose. Carried to the screen so a loose
    match can be labelled as one instead of passing for a clean find."""


def search(query: str, limit: int | None = None, books: tuple[str, ...] = ()) -> list[Hit]:
    """Passages worth showing for what was typed, best first.

    `books` narrows the search to those books by name. Empty means every book,
    which is the ordinary case. The caller drops names no book has before
    getting here, so a stale bookmark searches everything rather than finding
    nothing and reading as "no book says this".
    """
    settings = get_settings()
    limit = limit or settings.daleel_result_limit

    expansion = expand(
        query,
        DictionaryLexicon(),
        max_expand=settings.daleel_root_expand_max,
        max_translations=settings.daleel_english_expand_max,
        min_trigram_len=_TRIGRAM_MIN,
    )
    if expansion.is_empty():
        return []

    index = data_path("daleel_index_path")
    if not index.exists():
        return []

    conn = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    try:
        rows = _candidates(conn, expansion, limit * _CANDIDATE_FACTOR, tuple(books))
    finally:
        conn.close()

    ranked = sorted(((rank_of(row, expansion), row) for row in rows), key=lambda i: i[0])

    return [
        Hit(
            source=row[0],
            book=row[1],
            locator=row[2],
            arabic=row[3],
            english=row[4],
            match=_MATCH_BY_TIER[rank[0]],
        )
        for rank, row in _spread(ranked, limit)
    ]


def _spread(ranked: list[tuple], limit: int) -> list[tuple]:
    """The best matches, with every book that has one getting a place.

    Sorted purely on how good a match each passage is, so no book is favoured;
    but a book that matched is then guaranteed one slot before the rest of the
    list is filled. Without that guarantee the Qur'an wins every slot on almost
    any query, simply because it has by far the most passages, and a reader
    would never learn that the dictionary or Ibn Faris had an answer too.
    """
    best_of: dict[str, tuple] = {}
    for item in ranked:
        best_of.setdefault(item[1][0], item)

    chosen = list(best_of.values())[:limit]
    taken = {(item[1][0], item[1][2]) for item in chosen}

    for item in ranked:
        if len(chosen) >= limit:
            break
        if (item[1][0], item[1][2]) not in taken:
            chosen.append(item)
            taken.add((item[1][0], item[1][2]))

    return sorted(chosen, key=lambda i: i[0])


_MATCH_BY_TIER = {
    0: _MATCH_ALL,
    1: _MATCH_SOME,
    2: _MATCH_RELATED,
    3: _MATCH_ROOT,
    4: _MATCH_LOOSE,
}


def rank_of(row: tuple, expansion: Expansion) -> tuple[int, int, int, int]:
    """How good a match this row is. Pure, so it can be argued with in a test.

    Returns four numbers, all smaller-is-better: the tier, then a strength
    within that tier, then where the first hit falls, then how long the passage
    is. Position matters because a passage whose opening words answer the
    question reads as the better quotation; length breaks the remaining ties
    towards the tighter passage rather than the rambling one.

    The three weaker tiers each need their own strength, because the one that
    suits a word match means nothing to them. A root match has no position to
    speak of, so it counts how many of the query's roots the passage carries; a
    loose match counts how much of the misspelt word it shares.
    """
    _, _, _, _, english, roots, fold = row

    # Both halves of the passage count as places a term can be found. Some
    # books here are English only, Ibn Kathir among them, and a rule that read
    # the Arabic alone would rank every one of their passages as a bad match.
    fold = f"{fold} {english.lower()}"

    present = [term for term in expansion.typed if term in fold]
    also = [term for term in expansion.related if term in fold]

    if expansion.typed and len(present) == len(expansion.typed):
        tier = 0
    elif present:
        tier = 1
    elif also:
        tier = 2
    elif shared_roots := sum(bool(_has_root(roots, root))
                         for root in expansion.roots):
        return (3, -shared_roots, 0, len(fold))
    else:
        return (4, -_closeness(expansion.loose, fold), 0, len(fold))

    # A passage using the word beats one that merely contains its letters.
    # Without this the shortest passage won every tie, and the shortest thing
    # in the index is a dictionary headword: searching كتب returned كتبي and
    # كتبة ahead of the ayahs that actually say كُتِبَ.
    #
    # The test is that the word *ends* where a word ends, and deliberately says
    # nothing about what comes before it. Arabic writes its prefixes joined on,
    # so بِالصَّبْرِ is the ordinary way an ayah says الصبر; demanding a space on
    # both sides called that a poor match and put a dictionary entry above the
    # verse. A suffix is different: كتبي is a different word from كتب.
    matched = present or also
    padded = f"{fold} "
    whole = sum(f"{term} " in padded for term in matched)

    first = min((fold.find(term) for term in matched), default=len(fold))
    return (tier, -whole, first, len(fold))


def _has_root(roots: str, root: str) -> bool:
    """Whether the passage carries that exact root.

    Compared word by word rather than as a substring: the roots column is a
    space-joined list, and a plain `in` would let كتب match a longer root that
    merely contains those letters.
    """
    return root in roots.split()


def _candidates(
    conn: sqlite3.Connection, expansion: Expansion, cap: int, books: tuple[str, ...] = ()
) -> list[tuple]:
    """Rows that could match, with every source getting a share of the places.

    Each source gets its own share rather than the best matches being taken as
    they come. Without that the Qur'an fills the limit every time, simply
    because it has by far the most passages, and the other books were in the
    index, matched the query, and never once reached the screen.

    The share is cut by `passage_meta`, not by asking the same question twelve
    times over with `AND source = ?`. That filter reads a column FTS5 does not
    index, so it could only be answered by fetching every matching passage in
    full and looking at it, and the whole of that was done again for each
    source: a question of a few words took nineteen seconds. It now takes a
    third of one.
    """
    columns = "source, book, locator, arabic, english, roots, fold"
    per_source = max(cap // max(len(registry.SOURCES), 1), 8)
    found: dict[tuple[str, str], tuple] = {}

    # Capped, and the strongest terms come first, so what is dropped is always
    # the weakest end: the typed words survive, then the synonyms, then the
    # roots. A long question still fans out, but not without limit.
    # Deduplicated before the cap: a translation is often its own root (صبر),
    # and each repeat spent one of the twelve places on nothing.
    long_terms = list(dict.fromkeys(t for t in (*expansion.all_terms, *expansion.roots)
                                    if len(t) >= _TRIGRAM_MIN))[:_MAX_TERMS]

    # The words the trigram index cannot see, because it cannot match anything
    # shorter than three characters. They go to the `word` index, which holds
    # the same folded text cut into whole words. This used to be a LIKE with a
    # leading wildcard, which no index can help, so every two-letter word cost
    # a full scan of every book and a search took fifteen and a half seconds.
    # The terms past the cap are not lost; they are still matched by the
    # trigram path when they are long enough.
    short_terms = [t for t in expansion.all_terms
                   if len(t) < _TRIGRAM_MIN and _is_a_word(t)][:_MAX_SHORT_TERMS]

    # An index built before the word table existed still opens and still
    # answers every long word, so it must not turn a short one into a 500.
    # Said out loud with the command that mends it, because the quiet version
    # of this is a two-letter word reading as "no book says this".
    if short_terms and not _has_table(conn, "word"):
        log.warning("this index has no word table, so %d short term(s) cannot be "
                    "searched; run: python backend/scripts/build_daleel_index.py --words",
                    len(short_terms))
        short_terms = []

    if long_terms:
        match = " OR ".join(f'"{_escape(term)}"' for term in long_terms)
        for row in _fairly(conn, columns, match, per_source, books):
            found[(row[0], row[2])] = row

    # Matched as whole words, which is what the word index holds, so a
    # two-letter query does not match the inside of every longer one. The
    # quotes make each piece a phrase rather than a bare token, so a term
    # FTS5 would otherwise read as an operator is read as the word it is.
    #
    # Asked a source at a time, unlike the long terms above, because here the
    # narrowing is free: source and book are indexed columns of the word table,
    # so it is part of the same lookup rather than a filter over its answers.
    passage_columns = ", ".join(f"p.{name}" for name in columns.split(", "))
    for source in registry.SOURCES:
        for term in short_terms:
            for row in conn.execute(
                f"SELECT {passage_columns} FROM word JOIN passage p ON p.rowid = word.rowid "
                f"WHERE word MATCH ? LIMIT ?",
                (_word_match(term, source.id, books), per_source),
            ):
                found.setdefault((row[0], row[2]), row)

    # Only now, and only if nothing was found spelled the way it was typed.
    if not found:
        for row in _loosely(conn, columns, expansion, per_source, books):
            found.setdefault((row[0], row[2]), row)

    return list(found.values())


def _fairly(
    conn: sqlite3.Connection, columns: str, match: str, per_source: int,
    books: tuple[str, ...] = (),
) -> list[tuple]:
    """The best `per_source` passages each source has for that match, in one question.

    The matching is left to the trigram index, which answers in rowids and
    never unpacks a passage. `passage_meta` says which source each of those
    rowids belongs to, the numbering hands every source its own share, and only
    the rows that survive that are fetched in full.

    The share is cut by FTS5's own relevance score, not by passage order. Cut
    by order, a source with many matches kept its earliest ones and its best
    was often never ranked: over sixteen questions on the real index, 112 of
    156 sources kept their best passage that way and 149 do now. The score
    costs about 20 ms on a typical question and 0.3 s on the slowest. Putting
    passages holding every typed word first was tried too and kept only 121.
    """
    only, chosen = _only_books(books)
    passage_columns = ", ".join(f"p.{name}" for name in columns.split(", "))
    return list(conn.execute(
        f"SELECT {passage_columns} FROM ("
        f" SELECT m.id, row_number() OVER (PARTITION BY m.source ORDER BY f.rank, m.id) AS place"
        f" FROM (SELECT rowid AS id, rank FROM passage WHERE passage MATCH ?) f"
        f" JOIN passage_meta m ON m.id = f.id{only}"
        f") share JOIN passage p ON p.rowid = share.id WHERE share.place <= ?",
        (match, *chosen, per_source),
    ))


def _loosely(
    conn: sqlite3.Connection,
    columns: str,
    expansion: Expansion,
    per_source: int,
    books: tuple[str, ...] = (),
) -> list[tuple]:
    """Passages sharing most of a term's three-letter runs. The "did you mean".

    A misspelling keeps nearly all of the runs of the word intended: الرحييم
    and الرحيم share four of five. Matching on the runs rather than on the word
    is what turns SQLite's index into typo tolerance without any model.
    """
    runs = {run for term in expansion.loose for run in _trigrams(term)}
    if not runs:
        return []

    match = " OR ".join(f'"{_escape(run)}"' for run in sorted(runs))
    return _fairly(conn, columns, match, per_source, books)


def _runs(term: str, size: int) -> set[str]:
    """Every window of `size` characters in a term."""
    return {term[i:i + size] for i in range(len(term) - size + 1)}


def _trigrams(term: str) -> set[str]:
    """Every three-character window. What the index itself is built from."""
    return _runs(term, _TRIGRAM_MIN)


def _closeness(terms: tuple, haystack: str) -> int:
    """How near a misspelling is to what this passage actually says.

    Three-letter runs alone are too coarse to separate near misses: searching
    الرحييم, both الرحيم and الرحى share exactly three of them, so the tie fell
    to whichever passage was shorter and an idiom about millstones was put
    above al-Fatihah. Counting four-letter runs as well breaks that tie the way
    a reader would: الرحيم keeps more of the word in one piece.
    """
    score = 0
    for size in (_TRIGRAM_MIN, _TRIGRAM_MIN + 1):
        for term in terms:
            score += sum(run in haystack for run in _runs(term, size))
    return score


def _escape(term: str) -> str:
    """A term safe to sit inside an FTS5 double-quoted string."""
    return term.replace('"', '""')


def _has_table(conn: sqlite3.Connection, name: str) -> bool:
    """Whether this index holds that table. Older ones hold fewer of them."""
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone())


def _is_a_word(term: str) -> bool:
    """Whether the word index would make a word of this at all.

    A single % is not a word, and asking for it is not asking for nothing: the
    tokenizer drops it, the query left behind is the source filter on its own,
    and that matches every passage in the book. One typed % came back as twelve
    quotations picked at random, each labelled a clean match. It did this once
    before through LIKE's own wildcards; the shape of the mistake is the same
    one, so the guard is kept even though the escape it needed is gone.
    """
    return any(letter.isalnum() for letter in term)


def _word_match(term: str, source: str, books: tuple[str, ...]) -> str:
    """One FTS5 query for the word index: this word, in this source, in these books.

    Written as column filters rather than as a WHERE on the joined passage,
    because a WHERE only runs once the index has already found every passage
    holding the word and fetched each one to look at.
    """
    query = f'source:"{_escape(source)}" fold:"{_escape(term)}"'
    if books:
        inside = " OR ".join(f'"{_escape(name)}"' for name in books)
        query += f" AND book:({inside})"
    return query


def _only_books(books: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    """The SQL that narrows `passage_meta` to those books, and the values it needs.

    Empty in, empty out: no clause and no values, which is every query in this
    file behaving exactly as it did before a filter existed.
    """
    if not books:
        return "", ()
    return " AND book IN (" + ",".join("?" * len(books)) + ")", books


def books() -> list[tuple[str, str]]:
    """Every book in the index and the source it is credited to.

    Read from the index rather than from a manifest, so the picker can only
    ever offer a book that is genuinely searchable. A book listed but not
    indexed would be a filter that always finds nothing.

    From the catalogue table the build writes, not from the passages. Asking
    the passages for DISTINCT book made FTS5 unpack every column of every row,
    which is fifteen seconds of the picker sitting empty for forty-seven names.
    """
    index = data_path("daleel_index_path")
    if not index.exists():
        return []

    conn = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    try:
        # Ordered by source first so the list arrives grouped the way the page
        # already groups its results, one shape for the reader to learn.
        return list(
            conn.execute("SELECT name, source FROM book ORDER BY source, name")
        )
    finally:
        conn.close()


def is_built() -> bool:
    """Whether the index is there and whole. The panel says so rather than
    showing nothing.

    An index built before `passage_meta` existed holds every passage but cannot
    answer the query above, so it counts as not built. The half-minute mend is
    named in the log rather than on screen: the screen would be telling a
    reader to run a command about a table they have never heard of.
    """
    index = data_path("daleel_index_path")
    if not index.exists():
        return False

    conn = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    try:
        if _has_table(conn, "passage_meta"):
            return True
    finally:
        conn.close()

    log.warning("this index has no passage_meta table, so no search can run; "
                "run: python backend/scripts/build_daleel_index.py --meta")
    return False
