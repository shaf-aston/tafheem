"""Build the narrator database from the pages fetch_rijal.py cached.

    python backend/scripts/hadith/build_rijal.py

Parses every cached narrator page, and finds each name of each cached book
page inside our own Arabic text (hadith.db), keeping where it starts and ends.
Prints how many hadith were linked and names placed, and every name it could
not place, so nothing is lost quietly.

Rebuilding is safe at any time: it writes a fresh file beside the old one and
moves it into place at the end, like build_hadith_index.py.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services.hadith import loader, words  # noqa: E402
from backend.services.hadith.rijal import cache, parse  # noqa: E402

# Lists are JSON. Search reads the Arabic columns folded the way the hadith index folds Arabic.
_SCHEMA = """
CREATE TABLE narrator (
    id INTEGER PRIMARY KEY,
    name_en TEXT NOT NULL DEFAULT '', name_ar TEXT NOT NULL DEFAULT '',
    kunya_ar TEXT NOT NULL DEFAULT '', grade_en TEXT NOT NULL DEFAULT '', grade_ar TEXT NOT NULL DEFAULT '',
    grade_rank INTEGER, generation_ar TEXT NOT NULL DEFAULT '', years TEXT NOT NULL DEFAULT '', years_ar TEXT NOT NULL DEFAULT '',
    alt_en TEXT NOT NULL DEFAULT '', alt_ar TEXT NOT NULL DEFAULT '',
    lineage_ar TEXT NOT NULL DEFAULT '', nisba_ar TEXT NOT NULL DEFAULT '', city_ar TEXT NOT NULL DEFAULT '',
    profession_ar TEXT NOT NULL DEFAULT '', school_ar TEXT NOT NULL DEFAULT '',
    hadith_total INTEGER, fetched INTEGER NOT NULL DEFAULT 0, books TEXT NOT NULL DEFAULT '[]', flags TEXT NOT NULL DEFAULT '[]', facts TEXT NOT NULL DEFAULT '[]', texts TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE verdict (narrator_id INTEGER NOT NULL, ord INTEGER NOT NULL, scholar TEXT NOT NULL, quote TEXT NOT NULL);
CREATE INDEX verdict_by_narrator ON verdict (narrator_id, ord);
-- teacher_ord: the teacher's place in the student's own page; student_ord: the student's place in the teacher's. NULL where that page was never fetched.
CREATE TABLE tie (teacher_id INTEGER NOT NULL, student_id INTEGER NOT NULL, teacher_ord INTEGER, student_ord INTEGER, PRIMARY KEY (teacher_id, student_id));
CREATE INDEX tie_by_student ON tie (student_id);
CREATE TABLE mention (
    collection TEXT NOT NULL, book INTEGER NOT NULL, number INTEGER NOT NULL, part TEXT NOT NULL,
    start INTEGER NOT NULL, end INTEGER NOT NULL, narrator_id INTEGER NOT NULL, ord INTEGER NOT NULL,
    in_chain INTEGER NOT NULL DEFAULT 1  -- 0 for a name sunnah.com links in the matn, outside the isnad (arabic_sanad)
);
CREATE INDEX mention_by_book ON mention (collection, book, number, part, ord);
CREATE INDEX mention_by_narrator ON mention (narrator_id);
CREATE VIRTUAL TABLE narrator_fts USING fts5(name_ar, name_en, kunya_ar, lineage_ar);
"""
_JSON = ("books", "flags", "facts", "texts")
_PLAIN = ("name_en", "name_ar", "kunya_ar", "grade_en", "grade_ar", "grade_rank", "generation_ar", "years", "years_ar", "alt_en", "alt_ar",
          "lineage_ar", "nisba_ar", "city_ar", "profession_ar", "school_ar", "hadith_total")


def add_narrators(conn: sqlite3.Connection) -> int:
    """A row per cached narrator page, then a bare row (names only) for each teacher or student never fetched."""
    heard: dict[int, tuple[str, str]] = {}
    count = 0
    columns = ", ".join(("id", "fetched", *_JSON, *_PLAIN))
    for who, page in cache.narrator_pages():
        html = cache.read(page)
        if not html:
            continue
        found = parse.narrator(html)
        if not found["name_ar"]:
            continue  # a cached page that is no narrator's (an error or login page) is no row
        conn.execute(f"INSERT INTO narrator ({columns}) VALUES ({', '.join('?' * (2 + len(_JSON) + len(_PLAIN)))})",
                     (who, 1, *(json.dumps(found[f], ensure_ascii=False) for f in _JSON), *(found[f] for f in _PLAIN)))
        conn.executemany("INSERT INTO verdict VALUES (?, ?, ?, ?)",
                         [(who, i, *v) for i, v in enumerate(found["verdicts"])])
        for place, (other, name_ar, name_en) in enumerate(found["teachers"]):
            conn.execute("INSERT INTO tie (teacher_id, student_id, teacher_ord) VALUES (?, ?, ?) "
                         "ON CONFLICT DO UPDATE SET teacher_ord = excluded.teacher_ord", (other, who, place))
            heard[other] = (name_ar, name_en)
        for place, (other, name_ar, name_en) in enumerate(found["students"]):
            conn.execute("INSERT INTO tie (teacher_id, student_id, student_ord) VALUES (?, ?, ?) "
                         "ON CONFLICT DO UPDATE SET student_ord = excluded.student_ord", (who, other, place))
            heard[other] = (name_ar, name_en)
        count += 1
    conn.executemany("INSERT OR IGNORE INTO narrator (id, name_ar, name_en) VALUES (?, ?, ?)",
                     [(who, *names) for who, names in heard.items()])
    conn.executemany(
        "INSERT INTO narrator_fts (rowid, name_ar, name_en, kunya_ar, lineage_ar) VALUES (?, ?, ?, ?, ?)",
        [(i, words.fold(ar), words.fold_en(en), words.fold(kunya), words.fold(lineage)) for i, ar, en, kunya, lineage in
         conn.execute("SELECT id, name_ar, name_en, kunya_ar, lineage_ar FROM narrator").fetchall()])
    return count


def add_mentions(conn: sqlite3.Connection) -> tuple[int, int, int, int, list[tuple]]:
    """(our hadith in the cached books, those a page names, names placed, names seen, the names not placed)."""
    ours = linked = placed_n = seen = 0
    lost: list[tuple] = []
    for collection, book, page in cache.book_pages():
        text = {(h["number"], h["part"]): h["arabic"] for h in loader.hadiths(collection, book)}
        ours += len(text)
        for entry in parse.book_chains(cache.read(page)):
            arabic = text.get((entry["number"], entry["part"]))
            seen += len(entry["names"])
            if arabic is None:
                placed, missing = [], [(who, shown) for who, shown, *_ in entry["names"]]
            else:
                linked += 1
                placed, missing = parse.place(arabic, entry["names"])
            conn.executemany("INSERT INTO mention VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             [(collection, book, entry["number"], entry["part"], start, end, who, i, in_chain)
                              for i, (start, end, who, in_chain) in enumerate(placed)])
            lost.extend((collection, entry["number"], entry["part"], who, shown) for who, shown in missing)
            placed_n += len(placed)
    return ours, linked, placed_n, seen, lost


def build() -> None:
    if not cache.book_pages():
        raise SystemExit("no cached book pages. Run: python backend/scripts/hadith/fetch_rijal.py muslim 24")
    target = data_path("rijal_index_path")
    scratch = target.with_suffix(".building.db")
    scratch.unlink(missing_ok=True)
    conn = sqlite3.connect(scratch)
    try:
        conn.executescript(_SCHEMA)
        narrators = add_narrators(conn)
        ours, linked, placed, seen, lost = add_mentions(conn)
        if not placed:  # hadith.db missing or the wrong books: an empty index would read as "nobody narrated anything"
            raise SystemExit(f"no names placed in {ours:,} of our hadith: the old file is kept. Is hadith.db built?")
        conn.commit()
        conn.close()
    except BaseException:  # SystemExit too: a refused build leaves no half file
        conn.close()
        scratch.unlink(missing_ok=True)
        raise
    scratch.replace(target)

    print(f"narrators: {narrators:,} pages parsed")
    print(f"hadith linked: {linked:,}/{ours:,} = {linked / max(ours, 1):.1%}")
    print(f"names placed: {placed:,}/{seen:,} = {placed / max(seen, 1):.1%}")
    for collection, number, part, who, shown in lost:
        print(f"  unplaced {collection}:{number}{part} narrator {who}: {shown!r}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # the unplaced names are Arabic
    build()
