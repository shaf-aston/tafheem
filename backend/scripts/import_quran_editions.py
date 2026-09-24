"""Put every book of text that hangs on the ayahs into one library.

    python backend/scripts/import_quran_editions.py
    python backend/scripts/import_quran_editions.py --only jalalayn-ar
    python backend/scripts/import_quran_editions.py --list

An *edition* is one such book: a tafsir, a translation. They all have the same
shape, so they all live in one file with one schema, and `data/quran/editions.json`
beside it is the only place a book is ever named. Adding a book is an entry in
that manifest plus its downloaded file; no code is written. That is the whole
reason this script exists rather than a tenth build_quran_<book>.py.

Where the files come from
-------------------------
The Quranic Universal Library (https://qul.tarteel.ai) publishes 108 tafsirs and
204 translations as sqlite files. It has no API and its download button needs a
free account, so the files are fetched by hand, once, into `data/quran/downloads/`.
This is the same arrangement build_dictionary.py has with the Wiktionary dump.
Nothing here touches the network, then or ever.

What QUL's files actually look like
-----------------------------------
Their column names are published nowhere, so they were read out of their own
exporter (lib/exporter/export_tafsir.rb, lib/exporter/export_translation.rb, MIT)
rather than guessed at:

    tafsir       table `tafsir`
                 ayah_key, group_ayah_key, from_ayah, to_ayah, ayah_keys, text

                 Three different rows share that one table. A *text* row carries
                 the passage, with `ayah_keys` listing every ayah it covers. A
                 *pointer* row is one of those other ayahs, with empty text and
                 `group_ayah_key` naming the row that has it. An *empty* row is
                 an ayah the book says nothing about. Only text rows are read:
                 pointer rows repeat what `ayah_keys` already said, and an empty
                 row is not a passage.

    translation  table `translation` or `translations`, depending on which of
                 their export variants was downloaded, so the table is looked up
                 rather than assumed.
                 sura, ayah, ayah_key, text, and sometimes footnotes.

Both keep whatever HTML the source data had, which is stripped here, at the edge,
by services/markup.py. What reaches the database is text.

Safe to re-run. Writes to a scratch file and moves it into place only at the end,
so an interrupted run leaves the working library untouched. With --only, the
scratch starts as a copy of the current library, so one book is rewritten and the
others are not touched at all.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path, get_settings  # noqa: E402, needs the path above
from backend.services.markup import as_text  # noqa: E402

# The four words the app is allowed to print on a badge. Kept in step with
# tests/test_sources.py, which enforces the same list for sources.json: a fifth
# word here would show up as the weakest one on screen, quietly downgrading a
# hand-checked book to a guess.
CONFIDENCES = {"verified", "derived", "translated", "guessed"}

# asbab is a third: reports on why an ayah came down. Its own kind rather than a
# tafsir, because the tafsir picker is a list of commentaries a reader chooses
# between, and this is not one of those; the Timelines tab asks for it by id.
KINDS = {"tafsir", "translation", "asbab"}

# A translation is one line per ayah and there are exactly this many ayahs. A
# file with fewer is a bad download, not a translator who skipped some.
AYAHS_IN_QURAN = 6236


SCHEMA = """
CREATE TABLE edition (
    -- The slug we chose, in editions.json. Stable forever: it is what the
    -- reader's saved preference and every Daleel locator point at.
    id        TEXT PRIMARY KEY,
    -- Where this book sits in editions.json. Reading order is decided where the
    -- books are named, not in the panel that draws them.
    ordinal   INTEGER NOT NULL,
    kind      TEXT NOT NULL,
    language  TEXT NOT NULL,
    name      TEXT NOT NULL,
    -- What the picker calls it. The full name is for the credit line.
    short     TEXT NOT NULL,
    author    TEXT NOT NULL,
    licence   TEXT NOT NULL,
    origin    TEXT NOT NULL,
    -- Which entry in sources.json states how far this book is trusted.
    credit    TEXT NOT NULL,
    indexed   INTEGER NOT NULL,
    confidence TEXT NOT NULL,
    passages  INTEGER NOT NULL,
    ayahs     INTEGER NOT NULL
);

CREATE TABLE passage (
    edition TEXT NOT NULL,
    -- Named by the ayah it opens on, "78:1". A passage reached from any of its
    -- ayahs is therefore stored once. The rule tafsir.db already used.
    id      TEXT NOT NULL,
    text    TEXT NOT NULL,
    PRIMARY KEY (edition, id)
) WITHOUT ROWID;

CREATE TABLE covers (
    edition TEXT NOT NULL,
    surah   INTEGER NOT NULL,
    ayah    INTEGER NOT NULL,
    passage TEXT NOT NULL,
    PRIMARY KEY (edition, surah, ayah)
) WITHOUT ROWID;

-- WITHOUT ROWID above makes the primary key the table itself, so a lookup by
-- (edition, surah, ayah) is one descent with no second hop to fetch the row.
-- This index answers the other question, "every book on this one ayah", which
-- the primary key cannot: its columns are in the wrong order for it. It carries
-- `passage` so that question is answered out of the index without reading the
-- table at all.
CREATE INDEX covers_by_ayah ON covers (surah, ayah, edition, passage);
"""


@dataclass(frozen=True)
class RawPassage:
    """One passage as it left a foreign file, before anything is written."""

    id: str
    text: str
    covers: tuple[tuple[int, int], ...]


# ── Readers: one per foreign shape, and the only code that knows that shape ──


def read_qul_tafsir(path: Path):
    """Text rows from a QUL tafsir export. Pointer and empty rows are skipped."""
    with contextlib.closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        columns = {row[1] for row in db.execute("PRAGMA table_info(tafsir)")}
        if "ayah_key" not in columns:
            raise SystemExit(
                f"{path.name} has no `tafsir` table with an `ayah_key` column. "
                f"Is it a QUL tafsir export? It holds: {', '.join(sorted(columns)) or 'nothing'}."
            )

        for row in db.execute("SELECT * FROM tafsir"):
            text = as_text(row["text"] if "text" in columns else "")
            if not text:
                continue

            keys = row["ayah_keys"] if "ayah_keys" in columns else ""
            covers = _ayah_keys(keys) or _ayah_keys(row["ayah_key"])
            if not covers:
                continue

            # A run that crosses into the next surah would be stored correctly
            # and then read back wrongly: the reader asks "which ayahs was this
            # written about" one surah at a time, so it would answer with the
            # half in the surah asked for and the panel would tell the reader
            # something false. Nothing has been seen to do this, which is
            # exactly why it must say so rather than be silently trimmed.
            surahs = {surah for surah, _ in covers}
            if len(surahs) > 1:
                raise SystemExit(
                    f"{path.name}: the passage at {row['ayah_key']} covers ayahs in "
                    f"more than one surah ({sorted(surahs)}). Nothing here can show "
                    "that honestly yet. Report it rather than importing it."
                )

            yield RawPassage(id=str(row["ayah_key"]), text=text, covers=covers)


def read_qul_translation(path: Path):
    """One row per ayah from a QUL translation export."""
    with contextlib.closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        # Their exporter names the table `translation` in some variants and
        # `translations` in others, so it is looked up rather than assumed.
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        table = next((name for name in ("translations", "translation") if name in names), "")
        if not table:
            raise SystemExit(
                f"{path.name} has neither a `translation` nor a `translations` table. "
                f"It holds: {', '.join(sorted(names)) or 'nothing'}."
            )

        for row in db.execute(f"SELECT * FROM {table}"):  # noqa: S608, one of the two literals above
            text = as_text(row["text"])
            if not text:
                continue
            if covers := _ayah_keys(row["ayah_key"]):
                yield RawPassage(id=str(row["ayah_key"]), text=text, covers=covers)


def read_app_tafsir_db(path: Path):
    """This app's own tafsir.db, which build_quran_tafsir.py harvests.

    Kept as a reader rather than migrated once and forgotten, so that every
    edition in the library can be rebuilt from a file on disk. An edition that
    could only ever be produced once would be the one thing here nobody could
    put back.
    """
    with contextlib.closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        covered: dict[str, list[tuple[int, int]]] = {}
        for row in db.execute("SELECT surah, ayah, entry FROM covers ORDER BY surah, ayah"):
            covered.setdefault(row["entry"], []).append((int(row["surah"]), int(row["ayah"])))

        for row in db.execute("SELECT id, text FROM entry"):
            text = as_text(row["text"])
            covers = covered.get(row["id"], [])
            if not text or not covers:
                continue
            yield RawPassage(id=str(row["id"]), text=text, covers=tuple(covers))


def read_ayah_json(path: Path):
    """One text per ayah, from a file fetch_quran_editions.py wrote.

    The plainest shape a book can have: `{"passages": [{surah, ayah, text}]}`.
    Every mirror the fetcher knows is flattened into it there, so this reader
    never learns what a mirror is; it opens one file and reads three fields.

    A book fetched this way has no runs. QUL's own export can say "this passage
    is 78:1-10"; the mirrors publish the text against single ayahs and drop the
    rows that only point at another, so a passage here covers exactly one ayah
    and a pointed-at ayah is simply silent. That is a real difference from the
    account route and it is why `origin` records the mirror as well as the book.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("passages") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise SystemExit(f"{path.name} has no `passages` list. It is not a fetched book.")

    for row in rows:
        text = as_text(row.get("text", ""))
        if not text:
            continue
        if covers := _ayah_keys(f"{row.get('surah')}:{row.get('ayah')}"):
            yield RawPassage(id=f"{covers[0][0]}:{covers[0][1]}", text=text, covers=covers)


READERS = {
    "qul-tafsir": read_qul_tafsir,
    "qul-translation": read_qul_translation,
    "app-tafsir-db": read_app_tafsir_db,
    "ayah-json": read_ayah_json,
}


def _ayah_keys(value) -> tuple[tuple[int, int], ...]:
    """"2:255,2:256" as ((2, 255), (2, 256)). Anything unreadable is dropped."""
    found: list[tuple[int, int]] = []
    for key in str(value or "").split(","):
        surah, _, ayah = key.strip().partition(":")
        if surah.isdigit() and ayah.isdigit():
            pair = (int(surah), int(ayah))
            if pair not in found:
                found.append(pair)
    return tuple(found)


# ── The manifest, checked before anything is opened ──────────────────────────


def manifest() -> dict[str, dict]:
    """Every declared edition. Keys starting with _ are notes, not books."""
    path = data_path("quran_editions_path")
    if not path.exists():
        raise SystemExit(f"No manifest at {path}. It is the list of books to import.")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if not key.startswith("_")}


def check(edition_id: str, spec: dict) -> None:
    """Refuse a book the app could not honestly describe.

    Every one of these is something the reader would otherwise be shown: a book
    with no licence recorded, a badge word the UI cannot draw, a `kind` that
    belongs to no panel. Loud here beats wrong on screen.
    """
    for field in ("kind", "language", "name", "author", "licence", "origin", "credit", "format", "file"):
        if not str(spec.get(field, "")).strip():
            raise SystemExit(f"{edition_id}: '{field}' is empty in the manifest.")

    if spec["kind"] not in KINDS:
        raise SystemExit(f"{edition_id}: kind must be one of {sorted(KINDS)}, got {spec['kind']!r}.")
    if spec.get("confidence") not in CONFIDENCES:
        raise SystemExit(
            f"{edition_id}: confidence must be one of {sorted(CONFIDENCES)}, "
            f"got {spec.get('confidence')!r}."
        )
    if spec["format"] not in READERS:
        raise SystemExit(
            f"{edition_id}: format must be one of {sorted(READERS)}, got {spec['format']!r}."
        )


def source_file(spec: dict) -> Path:
    """The downloaded file this edition is built from, checked to be inside data/quran/."""
    base = data_path("quran_library_path").parent
    target = (base / spec["file"]).resolve()
    if not target.is_relative_to(base):
        raise SystemExit(f"file must stay inside {base}, got {spec['file']!r}")
    return target


# ── Writing ──────────────────────────────────────────────────────────────────


def _how_to_get(edition_id: str, spec: dict) -> str:
    """How to put this book's file where the importer expects it.

    Branches on the format, because only some of these come from QUL. Telling
    somebody to download `tafsir.db` from a website that has never held it is
    the kind of instruction that costs an hour.
    """
    if spec["format"] == "app-tafsir-db":
        return "Run backend/scripts/build_quran_tafsir.py, which harvests it from Quran.com."
    if spec["format"] == "ayah-json":
        return (
            f"Run backend/scripts/fetch_quran_editions.py --only {edition_id}, "
            "which downloads it from a public mirror. No account is needed."
        )
    kind, _, number = spec["origin"].partition(":")
    where = f"https://qul.tarteel.ai/resources/{spec['kind']}/{number}" if kind == "qul" else spec["origin"]
    return (
        f"Sign in at https://qul.tarteel.ai (a free account), open {where}, press "
        f"'Download sqlite', and save it as {spec['file']} under backend/data/quran/."
    )


def write_edition(conn: sqlite3.Connection, edition_id: str, spec: dict) -> tuple[int, int]:
    """Replace this one edition's rows. Returns (passages, ayahs)."""
    path = source_file(spec)
    if not path.exists():
        raise SystemExit(
            f"{edition_id}: {path} is not here.\n  {_how_to_get(edition_id, spec)}"
        )

    conn.execute("DELETE FROM passage WHERE edition = ?", (edition_id,))
    conn.execute("DELETE FROM covers WHERE edition = ?", (edition_id,))
    conn.execute("DELETE FROM edition WHERE id = ?", (edition_id,))

    seen_passages: set[str] = set()
    claimed: dict[tuple[int, int], str] = {}

    for raw in READERS[spec["format"]](path):
        # Two passages under one name, or two passages claiming one ayah, are
        # the file contradicting itself. Left to the database they vanish: OR
        # IGNORE drops the second text, OR REPLACE moves the ayah onto the
        # first, and every count afterwards still looks healthy while a reader
        # is shown one passage's words under another's address.
        if raw.id in seen_passages:
            raise SystemExit(
                f"{edition_id}: {path.name} has two passages both called {raw.id!r}. "
                "One of them would be dropped without a word, so neither is imported."
            )
        seen_passages.add(raw.id)

        for surah, ayah in raw.covers:
            holder = claimed.get((surah, ayah))
            if holder is not None and holder != raw.id:
                raise SystemExit(
                    f"{edition_id}: {path.name} gives {surah}:{ayah} to both "
                    f"{holder!r} and {raw.id!r}. Only one could be kept, and "
                    "picking would be guessing."
                )
            claimed[(surah, ayah)] = raw.id

        conn.execute(
            "INSERT INTO passage (edition, id, text) VALUES (?, ?, ?)",
            (edition_id, raw.id, raw.text),
        )
        conn.executemany(
            "INSERT INTO covers (edition, surah, ayah, passage) VALUES (?, ?, ?, ?)",
            [(edition_id, surah, ayah, raw.id) for surah, ayah in raw.covers],
        )

    # Counted out of the table rather than trusted from the loop above:
    # INSERT OR IGNORE and OR REPLACE both silently drop duplicates, and a file
    # full of repeats would otherwise report a healthy number.
    passages = conn.execute("SELECT COUNT(*) FROM passage WHERE edition = ?", (edition_id,)).fetchone()[0]
    ayahs = conn.execute("SELECT COUNT(*) FROM covers WHERE edition = ?", (edition_id,)).fetchone()[0]

    _check_coverage(edition_id, spec, ayahs)

    conn.execute(
        "INSERT INTO edition (id, ordinal, kind, language, name, short, author, licence, origin, "
        "credit, indexed, confidence, passages, ayahs) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            edition_id,
            0,  # restamped from the manifest once every book is written
            spec["kind"],
            spec["language"],
            spec["name"],
            spec.get("short") or spec["name"],
            spec["author"],
            spec["licence"],
            spec["origin"],
            spec["credit"],
            1 if spec.get("index") else 0,
            spec["confidence"],
            passages,
            ayahs,
        ),
    )
    return passages, ayahs


def _check_coverage(edition_id: str, spec: dict, ayahs: int) -> None:
    if spec["kind"] == "translation" and ayahs != AYAHS_IN_QURAN:
        raise SystemExit(
            f"{edition_id}: covers {ayahs:,} ayahs, and a translation must cover "
            f"exactly {AYAHS_IN_QURAN:,}. That is a bad file, not a short translation."
        )
    floor = get_settings().quran_tafsir_ayah_floor
    if spec["kind"] == "tafsir" and ayahs < floor:
        raise SystemExit(
            f"{edition_id}: covers only {ayahs:,} ayahs. Under {floor:,} means the "
            "file is broken, not that the scholar was quiet. A book that really "
            "does cover only part of the Qur'an needs quran_tafsir_ayah_floor lowered."
        )


def build(only: str | None = None) -> dict[str, tuple[int, int]]:
    books = manifest()
    if only and only not in books:
        raise SystemExit(f"No edition called {only!r}. Known: {', '.join(books)}")

    wanted = {only: books[only]} if only else books
    for edition_id, spec in wanted.items():
        check(edition_id, spec)

    target = data_path("quran_library_path")
    target.parent.mkdir(parents=True, exist_ok=True)
    scratch = target.with_suffix(".building")
    scratch.unlink(missing_ok=True)

    # With --only the scratch starts as a copy, so the books not named here keep
    # exactly the rows they already had.
    fresh = not (only and target.exists())
    if not fresh:
        shutil.copy2(target, scratch)

    conn = sqlite3.connect(scratch)
    counts: dict[str, tuple[int, int]] = {}
    try:
        if fresh:
            conn.executescript(SCHEMA)
        for edition_id, spec in wanted.items():
            counts[edition_id] = write_edition(conn, edition_id, spec)
            conn.commit()
            passages, ayahs = counts[edition_id]
            print(f"  {edition_id:<16} {passages:>6,} passages over {ayahs:>6,} ayahs")

        # A book taken out of the manifest goes out of the library with it.
        # Without this it stayed forever: the list of books said one thing and
        # the app went on showing another, and the only way to find out was to
        # notice a name in the picker that nobody had put there. The manifest is
        # what is true; this file is derived from it.
        gone = [
            row[0] for row in conn.execute("SELECT id FROM edition")
            if row[0] not in books
        ]
        for edition_id in gone:
            conn.execute("DELETE FROM passage WHERE edition = ?", (edition_id,))
            conn.execute("DELETE FROM covers WHERE edition = ?", (edition_id,))
            conn.execute("DELETE FROM edition WHERE id = ?", (edition_id,))
            print(f"  {edition_id:<16} removed, the manifest no longer names it")

        # Every book's place in the reading order, not just the ones written
        # here. It is a fact about the manifest as a whole, so importing one
        # book must not leave the others holding a position from an older
        # version of that list.
        conn.executemany(
            "UPDATE edition SET ordinal = ? WHERE id = ?",
            list(enumerate(books)),
        )
        conn.commit()
        conn.close()
    except BaseException:
        conn.close()
        scratch.unlink(missing_ok=True)
        raise

    try:
        # One operation, not delete-then-rename: the old library is never gone
        # before the new one is there, so an interruption costs the run and not
        # the books.
        scratch.replace(target)
    except PermissionError:
        # Windows will not replace a file another process has open, and the
        # running app holds the library open for reading. Said plainly, because
        # "PermissionError: [WinError 32]" reads like a broken script rather
        # than like "stop the server and run this again".
        scratch.unlink(missing_ok=True)
        raise SystemExit(
            f"{target.name} is open in another process, so it cannot be replaced.\n"
            "  Stop the backend, run this again, then start it back up. "
            "The library on disk is untouched."
        ) from None
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Import just this one edition id")
    parser.add_argument("--list", action="store_true", help="Show the manifest and stop")
    args = parser.parse_args()

    if args.list:
        for edition_id, spec in manifest().items():
            here = "have" if source_file(spec).exists() else "MISSING"
            searched = "searched" if spec.get("index") else "read only"
            print(f"  {edition_id:<16} {spec['kind']:<12} {spec['language']}  {here:<8} {searched}")
        return 0

    print("Importing into the Qur'an library")
    counts = build(args.only)
    passages = sum(passage for passage, _ in counts.values())
    print(f"\n{len(counts)} edition(s), {passages:,} passages, in {data_path('quran_library_path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
