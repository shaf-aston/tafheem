"""A passage and its neighbours in the same book, for reading it in context."""
from __future__ import annotations

from backend.services.daleel.index.connection import db
from backend.services.daleel.index.row import COLUMNS, IndexedPassage


def around(passage_id: int, span: int) -> list[IndexedPassage]:
    """The passage and up to `span` either side of it in the same book, in book order.

    Read through passage_meta's (source, id) index, so a neighbour from the next
    book over is never shown as context: a quotation read beside a stranger's
    text is the misreading this view exists to prevent. Empty for an unknown id.
    """
    conn = db()
    if conn is None:
        return []
    return list(map(IndexedPassage._make, conn.execute(
        f"SELECT {COLUMNS} FROM passage_meta m JOIN passage_meta c"
        " ON c.source = m.source AND c.book = m.book AND c.id BETWEEN m.id - ? AND m.id + ?"
        " JOIN passage p ON p.rowid = c.id WHERE m.id = ? ORDER BY c.id",
        (span, span, passage_id),
    )))
