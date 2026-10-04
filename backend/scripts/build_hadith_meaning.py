"""Turn every hadith's English into a meaning vector: hadith.db -> hadith_meaning.db.

    python backend/scripts/build_hadith_meaning.py

Only hadith not already stored with the same text are encoded, so a rebuild
after a small data change takes seconds; the first build takes ~13 minutes on
a desktop. Written beside the old file and swapped in whole.
"""
from __future__ import annotations

import hashlib
import shutil
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services.hadith import meaning  # noqa: E402

BATCH = 64

SCHEMA = """
CREATE TABLE IF NOT EXISTS meaning (
    collection_id TEXT NOT NULL,
    number        INTEGER NOT NULL,
    part          TEXT NOT NULL,
    text_hash     TEXT NOT NULL,  -- of the English the vector was made from
    vector        BLOB NOT NULL,  -- float16, unit length
    PRIMARY KEY (collection_id, number, part)
) WITHOUT ROWID;
"""


def _hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def main() -> None:
    target = data_path("hadith_meaning_path")
    building = target.with_suffix(".building.db")
    if target.exists():
        shutil.copyfile(target, building)
    else:
        building.unlink(missing_ok=True)

    source = sqlite3.connect(f"file:{data_path('hadith_index_path')}?mode=ro", uri=True)
    rows = source.execute("SELECT collection_id, number, part, english FROM hadith").fetchall()
    source.close()

    out = sqlite3.connect(building)
    out.executescript(SCHEMA)
    stored = {(c, n, p): h for c, n, p, h in out.execute("SELECT collection_id, number, part, text_hash FROM meaning")}
    wanted = {(c, n, p) for c, n, p, _ in rows}
    out.executemany("DELETE FROM meaning WHERE collection_id = ? AND number = ? AND part = ?",
                    [k for k in stored if k not in wanted])
    todo = [(c, n, p, e) for c, n, p, e in rows if stored.get((c, n, p)) != _hash(e)]
    todo.sort(key=lambda r: len(r[3]))  # alike lengths batch together, so little padding

    started = time.time()
    model = meaning.encoder() if todo else None  # nothing new: no model loaded
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        vectors = model.encode([e for *_, e in batch]).astype("float16")
        out.executemany("INSERT OR REPLACE INTO meaning VALUES (?, ?, ?, ?, ?)",
                        [(c, n, p, _hash(e), v.tobytes()) for (c, n, p, e), v in zip(batch, vectors)])
        out.commit()
        print(f"\r{i + len(batch)}/{len(todo)} encoded", end="", flush=True)
    out.close()
    building.replace(target)
    print(f"\n{len(rows)} hadith, {len(todo)} newly encoded in {time.time() - started:.0f}s -> {target}")


if __name__ == "__main__":
    main()
