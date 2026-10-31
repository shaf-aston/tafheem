"""Search the Qur'an from the index on this machine. No network, ever.

Built by backend/scripts/quran/build_quran_search_index.py out of the hand-tagged
corpus the app already ships, so what is found here is the corpus's own text.

The two sharp edges are the same ones Daleel hit, and are handled the same way,
because they are properties of SQLite's trigram tokenizer and not opinions:

  It cannot match anything shorter than three characters, and does not complain
  when asked to, it just finds nothing. Arabic is full of two-letter words, so
  those are matched with LIKE instead.

  It matches substrings of the folded text, which is why the query is folded
  with the same helper the index was built with. Typing الرَّحِيم with every mark
  on it must find the same ayahs as typing الرحيم.
"""
from __future__ import annotations

import re
import sqlite3
from collections import Counter
from functools import lru_cache

from backend.config import data_path
from backend.services.text import spelling
from backend.services.text.arabic_text import words
from backend.services.text.fts import TRIGRAM_MIN, quoted
from backend.services.quran.search.hit import Hit
from backend.services.core.readonly_db import ReadOnlyDb

NAME = "local"

# The source key this adapter's hits are badged with. The local text is the
# Quranic Arabic Corpus, which is hand-tagged, so it is "corpus" and not the
# Quran.com key: two different books must never wear one badge.
_SOURCE = "corpus"
# This thread's read-only connection to the index, reopened when a build replaces it.
_db = ReadOnlyDb(lambda: data_path("quran_search_index_path"))


# Anything that is not an Arabic letter or a space: punctuation, digits, Latin.
# A dictated ayah arrives with commas and full stops in it, and a substring
# match on "العالمين." found nothing.
_NOT_LETTERS_RE = re.compile(r"[^ء-ي\s]+")

# An ayah stays in the list when the query and it share at least this many
# whole words, or a run of consecutive words. Below this a nine-word query would
# be answered by every ayah with يوم in it.
_MIN_SHARED = 2


def search(query: str, limit: int) -> list[Hit]:
    """Ayahs sharing the most with what was typed, best first.

    Ranked by two fractions added: how much of the query one ayah holds in a
    single run, counted twice, and how much of the ayah the query covers. The
    first is what a typed phrase needs, the second is what a recitation across
    two ayahs needs: each ayah it covers whole outranks the long ayah elsewhere
    that quotes one of them. A misheard word costs a fraction rather than the
    whole search, and words in the wrong order still find their ayah. Ties go
    to the shorter ayah, then the Qur'an's own order. An ayah that only contains
    the letters (ملك inside الملك) comes last.

    Returns [] when the index has not been built. A missing index is a thing
    that has not been done yet, not a failure worth an error page.
    """
    return [hit for _, hit in _ranked(query)[:limit]]


def whole_ayah(query: str) -> Hit | None:
    """The ayah the query is, every word in order and nothing more, or None.

    The top score is that and only that: the whole query in one run, covering
    every word of the ayah. Scoring counts each word once, so the word count
    is checked too: the ayah typed twice is not that ayah."""
    best = next(iter(_ranked(query, every=True)), None)
    whole = best and best[0] == _WHOLE and len(words(query)) == len(words(best[1].arabic_text))
    return best[1] if whole else None


# Letters a typist and the Qur'an's own spelling disagree on most: the hamza's seat
# and the long alif (خاسئين / خٰسِـِٔين, ءاتوا / آتوا). Left out when two words are
# compared position by position, never when the index is asked.
_SEATS_RE = re.compile("[ءأإآئؤا]")
_HAMZA_RE = re.compile("[ءأإآئؤ]")


def ayah_run(query: str) -> tuple[Hit, int] | None:
    """The ayah holding the query's words as one run, in order, and the number of
    the run's first word there (1-based, as meanings.db counts), or None.

    Two words or more, every one of them matched whole, so a typed sentence that
    only shares words with an ayah is not taken for part of it. Asked of the index
    as "every word present", which answers in well under a millisecond when no
    ayah has them, so sentences that are not the Qur'an's cost nothing here.
    """
    wanted = [_key(w) for w in words(query)]
    wanted = [w for w in wanted if w]
    conn = _db()
    if len(wanted) < 2 or conn is None:
        return None
    # The index is asked with the words it spells as a typist does; the run check below takes the rest.
    # A word too short for the index is a full scan (_rows), so then every word is asked after all.
    plain = [w for w in words(query) if not _HAMZA_RE.search(w)]
    if not any(len(spelling.fold(w)) >= TRIGRAM_MIN for w in plain):
        plain = words(query)
    asked = " ".join(_NOT_LETTERS_RE.sub(" ", spelling.fold(" ".join(plain))).split())
    for surah, ayah, arabic, fold in sorted(_rows(conn, asked, every=True), key=lambda r: (r[0], r[1])):
        count, keys = len(words(arabic)), [_key(w) for w in fold.split()]
        # The fold holds the ayah twice where its two spellings differ, word for word.
        spellings = [keys[:count]] + ([keys[count:]] if len(keys) == 2 * count else [])
        for start in range(count - len(wanted) + 1):
            if all(any(s[start + i] == w for s in spellings) for i, w in enumerate(wanted)):
                return Hit(surah=surah, ayah=ayah, arabic_text=arabic, source=_SOURCE), start + 1
    return None


def _key(word: str) -> str:
    """One word as ayah_run compares it: folded, letters only, no hamza seat or alif."""
    return _SEATS_RE.sub("", _NOT_LETTERS_RE.sub("", spelling.fold(word)))


def _ranked(query: str, every: bool = False) -> list[tuple[float, Hit]]:
    """Every ayah that answers the query, with its score, best first; with
    `every`, only ayahs holding every word of it."""
    conn = _db()
    folded = " ".join(_NOT_LETTERS_RE.sub(" ", spelling.fold(query)).split())
    if conn is None or not folded:
        return []

    rows = _rows(conn, folded, every)

    # Each word once: الله الله الله is a one-word question, and counting it as
    # three made every ayah fall short of the threshold below.
    wanted = list(dict.fromkeys(folded.split()))
    scored = sorted(
        ((score, row) for row in rows if (score := _score(wanted, row[3], len(row[2].split()))) is not None),
        key=lambda pair: (-pair[0], len(pair[1][3]), pair[1][0], pair[1][1]),
    )
    return [(score, Hit(surah=row[0], ayah=row[1], arabic_text=row[2], source=_SOURCE)) for score, row in scored]


def respelt(query: str) -> tuple[str, list[tuple[str, str]]]:
    """The query with each word no ayah holds, even inside a longer word, swapped
    for the one it was likeliest meant to be (services/text/spelling.py), and the
    swaps as (typed, used). رحمن is kept: it matches inside الرحمن."""
    if (stamp := _db.stamp()) is None:
        return query, []
    known = _vocabulary(stamp)
    swapped = {}
    for typed in dict.fromkeys(query.split()):
        word = _NOT_LETTERS_RE.sub("", spelling.fold(typed))
        if word and not known.holds(word) and (used := known.nearest(word)):
            swapped[typed] = used
    # Each slip reported once, however often it was typed.
    return " ".join(swapped.get(w, w) for w in query.split()), list(swapped.items())


@lru_cache(maxsize=1)
def _vocabulary(_stamp: tuple[str, int]) -> spelling.Vocabulary:
    """Every word of the Qur'an by how often it occurs, read once per build of the index (the stamp is the key)."""
    rows = _db().execute("SELECT fold FROM verse")
    return spelling.Vocabulary(Counter(w for (fold,) in rows for w in spelling.fold(fold).split()))


# _score's ceiling: the query is one run of the ayah and covers all of it.
_WHOLE = 3.0


def _score(wanted: list[str], fold: str, length: int) -> float | None:
    """How well one ayah answers the query, 0 to 3, or None when it shares too
    little to be an answer at all. `length` is the ayah's own word count: the
    fold holds the ayah twice where its spellings differ, and counting that
    made a two-word ayah look three words long and half covered."""
    have = spelling.fold(fold).split()
    distinct = set(have[:length])
    present = len(set(wanted) & set(have))
    # Longest run of words the two share in the same order: ending[j] is the
    # run ending at have[j] for the current query word, built row by row.
    run, ending = 0, [0] * len(have)
    for word in wanted:
        ending = [ending[j - 1] + 1 if h == word and j else int(h == word) for j, h in enumerate(have)]
        run = max(run, *ending, 0)
    if max(run, present) >= min(_MIN_SHARED, len(wanted)):
        # The index holds an ayah in two spellings where they differ, so
        # `distinct` runs a little large and coverage a little small. It is
        # the same for every ayah, so the order between them holds.
        return 2 * run / len(wanted) + present / len(distinct)
    # Only the letters match, inside some longer word. Still a hit, ranked last.
    return 0.0 if len(wanted) == 1 else None


def _rows(conn: sqlite3.Connection, folded: str, every: bool = False) -> list[tuple]:
    """Every ayah containing any word of the query (with `every`, all of its
    index-visible words), by whichever of the two routes can see it. Ranking
    happens in Python, over these."""
    columns = "surah, ayah, arabic, fold"
    long_enough = [w for w in folded.split() if len(w) >= TRIGRAM_MIN]

    if long_enough:
        # A word typed with a final ه is also asked for with ة: the index
        # spells الجنة the Qur'an's way, the query often does not.
        asks = [f"({quoted(w)} OR {quoted(w[:-1] + 'ة')})" if w.endswith("ه") else quoted(w) for w in long_enough]
        match = (" AND " if every else " OR ").join(asks)
        return list(conn.execute(f"SELECT {columns} FROM verse WHERE verse MATCH ?", (match,)))

    # Too short for the index to see. A full scan, and it is affordable here in
    # a way it would not be over a large corpus: 6,236 rows is a few
    # milliseconds. Matched as a whole word, with a space demanded on both
    # sides: letting a prefix run into it made أب match the end of ٱلْكِتَٰب, and a
    # two-letter search came back with most of the Qur'an in it. The column is
    # folded as the query is (ة as ه), as the index route above asks both.
    return list(conn.execute(
        f"SELECT {columns} FROM verse WHERE ' ' || replace(fold, 'ة', 'ه') || ' ' LIKE ? ESCAPE '\\'",
        (f"% {_like_safe(folded.split()[0])} %",),
    ))


def _like_safe(term: str) -> str:
    """A term with LIKE's own wildcards defused.

    Without this, typing a single % would match every ayah in the Qur'an and the
    page would fill with results that had nothing to do with anything. The
    backslash is escaped first, or escaping the wildcards would go on to escape
    that.
    """
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
