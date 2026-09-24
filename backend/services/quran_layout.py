"""Which printed page each ayah falls on, read from the local build.

This module is the only thing that opens layout.db. Everything else asks it,
the same rule quran_corpus.py and quran_meanings.py follow, for the same reason.

The printing is the 604-page Madani mushaf, the one whose script this app
already renders. Built by scripts/build_quran_layout.py. If it has never been
run the database is simply absent and `is_built()` is False: callers then have
no page numbers and fall back to sizing a page by word count, which is what the
app did before. A missing file is a valid state, it means "not built yet".
"""
from __future__ import annotations

from pathlib import Path

from backend.services.readonly_db import ReadOnlyDb

DATA_DIR = Path(__file__).parent.parent / "data" / "quran"
DATABASE = DATA_DIR / "layout.db"


def is_built() -> bool:
    return DATABASE.exists()


_db = ReadOnlyDb(lambda: DATABASE)


def for_surah(surah: int) -> dict[int, int]:
    """One surah's page numbers, as {ayah: page}. Empty if never built.

    One query for the whole surah rather than one per ayah, for the same reason
    quran_meanings.for_surah exists: reading al-Baqarah must not cost 286 reads.
    """
    db = _db()
    if db is None:
        return {}
    rows = db.execute("SELECT ayah, page FROM page WHERE surah = ?", (surah,)).fetchall()
    return {row["ayah"]: row["page"] for row in rows}
