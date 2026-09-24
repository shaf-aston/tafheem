"""Search the Qur'an from the index on this machine. No network, ever.

Built by backend/scripts/build_quran_search_index.py out of the hand-tagged
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

from backend.config import data_path
from backend.services.arabic_text import bare_letters
from backend.services.quran_search.hit import Hit

NAME = "local"

# The shortest string SQLite's trigram tokenizer can match. Not a preference, a
# property of the tokenizer, so it is a constant here and not a setting.
_TRIGRAM_MIN = 3

# The source key this adapter's hits are badged with. The local text is the
# Quranic Arabic Corpus, which is hand-tagged, so it is "corpus" and not the
# Quran.com key: two different books must never wear one badge.
_SOURCE = "corpus"


# Anything that is not an Arabic letter or a space: punctuation, digits, Latin.
# A dictated ayah arrives with commas and full stops in it, and a substring
# match on "العالمين." found nothing.
_NOT_LETTERS_RE = re.compile(r"[^ء-ي\s]+")

# A spelling difference the index does not fold: ة and ه at the end of a word
# (الجنة typed as الجنه, as speech-to-text and many keyboards spell it).
_TA_TO_HA = str.maketrans("ة", "ه")

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
    index = data_path("quran_search_index_path")
    if not index.exists():
        return []

    folded = " ".join(_NOT_LETTERS_RE.sub(" ", bare_letters(query)).split())
    if not folded:
        return []

    conn = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    try:
        rows = _rows(conn, folded)
    finally:
        conn.close()

    # Each word once: الله الله الله is a one-word question, and counting it as
    # three made every ayah fall short of the threshold below.
    wanted = list(dict.fromkeys(folded.translate(_TA_TO_HA).split()))
    scored = sorted(
        ((score, row) for row in rows if (score := _score(wanted, row[3], len(row[2].split()))) is not None),
        key=lambda pair: (-pair[0], len(pair[1][3]), pair[1][0], pair[1][1]),
    )
    return [Hit(surah=row[0], ayah=row[1], arabic_text=row[2], source=_SOURCE) for _, row in scored[:limit]]


def _score(wanted: list[str], fold: str, length: int) -> float | None:
    """How well one ayah answers the query, 0 to 3, or None when it shares too
    little to be an answer at all. `length` is the ayah's own word count: the
    fold holds the ayah twice where its spellings differ, and counting that
    made a two-word ayah look three words long and half covered."""
    have = fold.translate(_TA_TO_HA).split()
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


def _rows(conn: sqlite3.Connection, folded: str) -> list[tuple]:
    """Every ayah containing any word of the query, by whichever of the two
    routes can see it. Ranking happens in Python, over these."""
    columns = "surah, ayah, arabic, fold"
    long_enough = [w for w in folded.split() if len(w) >= _TRIGRAM_MIN]

    if long_enough:
        # A word typed with a final ه is also asked for with ة: the index
        # spells الجنة the Qur'an's way, the query often does not.
        spellings = long_enough + [f"{w[:-1]}ة" for w in long_enough if w.endswith("ه")]
        match = " OR ".join(f'"{_escape(w)}"' for w in spellings)
        return list(conn.execute(f"SELECT {columns} FROM verse WHERE verse MATCH ?", (match,)))

    # Too short for the index to see. A full scan, and it is affordable here in
    # a way it would not be over a large corpus: 6,236 rows is a few
    # milliseconds. Matched as a whole word, with a space demanded on both
    # sides: letting a prefix run into it made أب match the end of ٱلْكِتَٰب, and a
    # two-letter search came back with most of the Qur'an in it.
    return list(conn.execute(
        f"SELECT {columns} FROM verse WHERE ' ' || fold || ' ' LIKE ? ESCAPE '\\'",
        (f"% {_like_safe(folded.split()[0])} %",),
    ))


def _escape(term: str) -> str:
    """A term safe to sit inside an FTS5 double-quoted string."""
    return term.replace('"', '""')


def _like_safe(term: str) -> str:
    """A term with LIKE's own wildcards defused.

    Without this, typing a single % would match every ayah in the Qur'an and the
    page would fill with results that had nothing to do with anything. The
    backslash is escaped first, or escaping the wildcards would go on to escape
    that.
    """
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
