"""Build the Qur'an's own search index, so searching works with no network.

    python backend/scripts/build_quran_search_index.py

Reads corpus.db, which the app already ships, joins each ayah's segments back
into its written text, and writes one FTS5 table. Nothing is downloaded: the
text is already on this machine, it was simply never searchable.

Why a separate file rather than a table inside corpus.db: the same reason the
word-by-word English and the mushaf page breaks are separate. Each is rebuilt on
its own, and a rebuild must not be able to damage the hand-tagged corpus.

Rebuilding is safe at any time. It writes a fresh file beside the old one and
moves it into place at the end, so a run that fails leaves the working index
untouched rather than half-written.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services import quran_corpus  # noqa: E402
from backend.services.arabic_text import alef_written_out, bare_letters  # noqa: E402

# One column is searched, the rest are carried. `fold` is the ayah with its
# diacritics and spelling variants flattened, which is what a typed query is
# compared against; `arabic` keeps the corpus's own spelling for display.
# Same shape and the same tokenizer as the Daleel index, deliberately: two
# search indexes in one app that behave differently is two things to learn.
#
# The table is "verse" and not "ayah" because FTS5 refuses a column named after
# its own table, and the ayah number has to keep its name.
_SCHEMA = """
CREATE VIRTUAL TABLE verse USING fts5(
    surah UNINDEXED,
    ayah UNINDEXED,
    arabic UNINDEXED,
    fold,
    tokenize = 'trigram'
);
"""

_SURAHS = 114


def _fold(text: str) -> str:
    """The ayah written both ways a reader might type it, in one column.

    The Qur'an writes a long "aa" as a small mark above the letter, so ٱلْكِتَٰب is
    the word an ordinary book spells الكتاب. Drop the mark and someone typing
    الكتاب finds nothing; write it out as a full alef and someone typing الرحمن
    finds nothing, because that word is never spelled الرحمان. Neither fold is
    right on its own, so both go in and a query matches whichever fits. It costs
    roughly twice the index size, which here is four megabytes.
    """
    dropped = bare_letters(text)
    written = alef_written_out(text)
    return dropped if written == dropped else f"{dropped} {written}"


def build() -> int:
    """Write the index. Returns how many ayahs went in."""
    if not quran_corpus.is_loaded():
        raise SystemExit(
            "corpus.db is not here. Run backend/scripts/build_quran_corpus.py first."
        )

    target = data_path("quran_search_index_path")
    target.parent.mkdir(parents=True, exist_ok=True)
    scratch = target.with_suffix(".building")
    scratch.unlink(missing_ok=True)

    conn = sqlite3.connect(scratch)
    written = 0
    try:
        conn.executescript(_SCHEMA)
        for surah in range(1, _SURAHS + 1):
            # ayah_texts already knows how to glue segments into words and words
            # into an ayah. Repeating that join here would be a second answer to
            # a question the corpus module already owns.
            rows = [
                (surah, number, text, _fold(text))
                for number, text in quran_corpus.ayah_texts(surah)
            ]
            if not rows:
                continue
            conn.executemany(
                "INSERT INTO verse (surah, ayah, arabic, fold) VALUES (?, ?, ?, ?)", rows
            )
            written += len(rows)
        conn.commit()
        conn.close()
    except Exception:
        conn.close()
        scratch.unlink(missing_ok=True)
        raise

    # One operation, not delete-then-rename: the working index is never gone
    # before its replacement is there.
    scratch.replace(target)
    return written


def main() -> int:
    print("Building the Qur'an search index")
    written = build()
    print(f"  {written:,} ayahs indexed")

    # The Qur'an has a known length, so an index that is short is a broken build
    # and not a matter of opinion. Said out loud rather than left to be noticed
    # later by a search that quietly finds nothing.
    if written != 6236:
        print("  WARNING: expected 6,236 ayahs. The corpus may be incomplete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
