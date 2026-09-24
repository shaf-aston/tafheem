"""Take one book off the classical shelf that is already built.

build_lexicons.py decides what a fresh database holds. A database built before
that list changed still holds the book, and rebuilding the whole shelf to drop
one of them costs half an hour of reading OpenITI. This drops just the one.

Ibn Faris is the case it was written for: his book is held on its own in
data/maqayees/, with harakat and an English gloss, and the copy on this shelf
was the same book read worse. Only the shelf is touched; data/maqayees is not
opened here and cannot be affected by it.

    python backend/scripts/drop_lexicon_book.py maqayis

The old file is copied beside itself as lexicons.db.bak first, so the step is
undone by putting that copy back.
"""

import shutil
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "lexicons.db"


def drop(book: str) -> None:
    if not DB.exists():
        raise SystemExit(f"no shelf at {DB}")

    with sqlite3.connect(DB) as db:
        held = [row[0] for row in db.execute("SELECT id FROM book")]
        if book not in held:
            raise SystemExit(f"{book} is not on this shelf. It holds: {', '.join(held)}")

    backup = DB.with_suffix(".db.bak")
    shutil.copy2(DB, backup)

    with sqlite3.connect(DB) as db:
        gone = db.execute("DELETE FROM entry WHERE book = ?", (book,)).rowcount
        db.execute("DELETE FROM book WHERE id = ?", (book,))
        db.commit()
        left = [row[0] for row in db.execute("SELECT id FROM book")]
    # Outside the transaction: sqlite will not vacuum inside one.
    sqlite3.connect(DB).execute("VACUUM")

    print(f"dropped {book}: {gone} entries. Left on the shelf: {', '.join(left)}")
    print(f"the old file is at {backup}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("name one book, for example: maqayis")
    drop(sys.argv[1])
