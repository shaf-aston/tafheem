"""What every SQLite full-text search here shares (Daleel, Qur'an, Hadith):
quoting a typed term, narrowing to a list, and the trigram tokenizer's limit.
"""
from __future__ import annotations

# The shortest string SQLite's trigram tokenizer can match. Not a preference, a
# property of the tokenizer, so a constant and not a setting, and one copy: two
# once let a change switch off typo tolerance with nothing to show for it.
TRIGRAM_MIN = 3


def quoted(*words: str) -> str:
    """Words as one FTS5 phrase. A quote is the one character that is syntax
    there, and it is doubled, so a term cannot close its own phrase."""
    return '"' + " ".join(words).replace('"', '""') + '"'


def only_in(column: str, values: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
    """The `AND column IN (...)` clause narrowing a query to `values`, and its
    parameters. Empty in, empty out: no clause, every query as without a filter."""
    if not values:
        return "", ()
    return f" AND {column} IN (" + ",".join("?" * len(values)) + ")", values
