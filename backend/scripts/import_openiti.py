"""Bring the OpenITI books into the project, so the download folder can go.

    python backend/scripts/import_openiti.py --from "C:/Users/Shaf/Downloads/OpenITI-pri-data_v9"
    python backend/scripts/import_openiti.py            # re-derive from the copies already here
    python backend/scripts/import_openiti.py --dry-run  # count everything, write nothing

Two things are produced and they are deliberately not the same thing:

  data/books/openiti/<file>   the book exactly as OpenITI wrote it, copied once.
  data/books/openiti.db       the passages, parsed out of those files.

The copy exists so that a rule in this file can be changed and every book
re-derived without the original download. Deriving into a database and throwing
the source away is how a parsing decision becomes permanent by accident.

Which books are imported is data/books/openiti-books.json, not this file. This
file knows how to read the format; it does not know which books exist.

The format, in full, because it is small:

    #META# ...                  header, two rival schemas, ended by
    #META#Header#End#
    # some text                 a paragraph starts
    ~~more of it                the same paragraph, wrapped
    ### | باب الإعراب           a heading (Shamela files)
    # | بحث كذا                 a heading (al-Jami' al-Kabir files)
    PageV01P141                 the printed page, inline, mid-sentence
    ms073                       a word-count milestone, meaningless to a reader
    @QB@ ... @QE@               a Qur'an quotation inside the prose

Nothing here repairs the Arabic. Some of these texts have a stray space inside
a word after a hamza-alif, "الأ قسام" for "الأقسام", and the temptation is to
close it up. The join would be a guess: أ ends real words too, and a wrong join
invents a word the book never had. The count is reported per book instead, so
the size of the problem is visible rather than silently papered over.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.arabic_text import bare_letters  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1] / "data" / "books"
_MANIFEST = _ROOT / "openiti-books.json"
_COPIES = _ROOT / "openiti"
_DB = _ROOT / "openiti.db"

# A paragraph with fewer Arabic letters than this is not a quotation anybody
# would cite: it is a stray "...", a page marker on its own, or a heading that
# lost its marker. Counted in letters rather than characters, and the number is
# low on purpose. At thirty characters it was throwing away real text: the
# Ajurrumiyya's "وللخفض ثلاث علامات" is a sentence of the book, and half of an
# Alfiyya verse is shorter still.
_MIN_PASSAGE_LETTERS = 12

# What a broken verse looks like. These files set a line of verse as
# "صدر ... عجز" on one line, and where the digitiser slipped it set the two
# halves as two paragraphs, leaving the first one ending in the separator with
# nothing after it. That dangling separator is the evidence, so the halves are
# put back together rather than stored as two half-lines that rhyme with
# nothing. Nothing is inferred from the words themselves.
#
# The length cap is what stops that rule running away. A stray "..." on its own
# line, or a prose paragraph that happens to trail off, would otherwise take the
# paragraph below it, and having grown a trailing separator would take the next
# one too. A first hemistich is short; anything longer than this is prose that
# ended in dots, and prose is left alone.
_HANGING_VERSE = re.compile(r"\.\.\.\s*$")
_HEMISTICH_MAX_LETTERS = 60

_HEADER_END = "#META#Header#End#"
_PAGE = re.compile(r"PageV(\d+)P(\d+)")
_MILESTONE = re.compile(r"\bms\d+\b")
_QURAN_TAG = re.compile(r"@Q[BE]@")
_HEADING = re.compile(r"^#+ \|+\s*(.*)$")

# What the two schemas write around a heading that is not part of the heading.
# Shamela marks a machine-detected one "AUTO", sometimes numbered; al-Jami'
# al-Kabir writes the nesting depth as a bare digit at both ends, so its chapter
# reads "1 كتاب الطهارات 1". Left in, both end up printed on the citation under
# a book's name, which makes the app look like it cannot read its own sources.
_HEADING_NOISE = re.compile(r"^(?:AUTO\s*)?(?:\d+\s*-\s*|\d+\s+)?(.*?)(?:\s+\d+)?$")
_PARAGRAPH = re.compile(r"^# (.*)$")
_CONTINUES = re.compile(r"^~~(.*)$")
_BROKEN_ALIF = re.compile(r"[\u0623\u0625\u0622] [\u0621-\u064a]")

_SCHEMA = """
CREATE TABLE book (
    file       TEXT PRIMARY KEY,
    collection TEXT NOT NULL,
    title      TEXT NOT NULL,
    author     TEXT NOT NULL,
    died       INTEGER
);
CREATE TABLE passage (
    id         INTEGER PRIMARY KEY,
    file       TEXT NOT NULL REFERENCES book(file),
    collection TEXT NOT NULL,
    page       TEXT NOT NULL,
    heading    TEXT NOT NULL,
    arabic     TEXT NOT NULL
);
CREATE INDEX passage_by_book ON passage(file);
"""


@dataclass
class Parsed:
    """What one book yielded, and what was thrown away getting there."""

    passages: list[tuple[str, str, str]]
    """(page, heading, arabic), in the book's own order."""

    too_short: int
    broken_alif: int


def parse(text: str) -> Parsed:
    """The quotable paragraphs of one OpenITI file, in order.

    Page and heading are carried forward from the last one seen, because both
    are stated once and then apply until the next: that is what makes a page
    number a citation rather than a label on a single line.
    """
    body = text.partition(_HEADER_END)[2]
    passages: list[tuple[str, str, str]] = []
    page, heading = "", ""
    current: list[str] = []
    too_short = 0

    def close() -> None:
        nonlocal too_short, current
        if not current:
            return
        joined = _clean(" ".join(current))
        current = []
        if not joined:
            return

        # The half-verse left hanging by the line before takes this one as its
        # second half, and the pair is stored as the one line it is.
        if passages and _is_hanging_verse(passages[-1][2]):
            prev_page, prev_heading, prev = passages[-1]
            passages[-1] = (prev_page, prev_heading, f"{prev} {joined}")
            return

        if _letters(joined) < _MIN_PASSAGE_LETTERS:
            too_short += 1
            return
        passages.append((page, heading, joined))

    for line in body.splitlines():
        line = line.rstrip()

        # The page marker is read before anything else strips it, and it is
        # taken from the line the paragraph *starts* on. A paragraph running
        # over a page break is cited by the page it began on, which is what a
        # person holding the book would do.
        found = _PAGE.search(line)

        if match := _CONTINUES.match(line):
            current.append(match.group(1))
        elif match := _HEADING.match(line):
            close()
            heading = _heading(match.group(1))
        elif match := _PARAGRAPH.match(line):
            close()
            if found:
                page = f"{int(found.group(1))}/{int(found.group(2))}"
            current.append(match.group(1))
        elif not line.strip():
            close()

        if found and not current:
            page = f"{int(found.group(1))}/{int(found.group(2))}"

    close()
    return Parsed(passages, too_short, len(_BROKEN_ALIF.findall(body)))


def _is_hanging_verse(text: str) -> bool:
    """Whether that passage is a first hemistich still waiting for its second."""
    if not _HANGING_VERSE.search(text):
        return False
    letters = _letters(text)
    return 0 < letters <= _HEMISTICH_MAX_LETTERS


def _heading(text: str) -> str:
    """A chapter title with each schema's bookkeeping taken off the ends."""
    match = _HEADING_NOISE.match(_clean(text))
    return match.group(1).strip() if match else _clean(text)


def _letters(text: str) -> int:
    """How many Arabic letters, which is the only measure of a real sentence.

    Counting characters instead let punctuation and Latin page furniture make a
    line of nothing look long enough to keep, and made a short line of real
    Arabic look too short to bother with.
    """
    return sum("ء" <= c <= "ي" for c in text)


def _clean(text: str) -> str:
    """The reader's text: the book's words, without the file's machinery.

    Page markers, milestones and the Qur'an-quote tags are addresses and
    annotations, not words anyone said. Left in, every one of them would be
    searchable and a query for a page number would return prose.
    """
    text = _PAGE.sub(" ", text)
    text = _MILESTONE.sub(" ", text)
    text = _QURAN_TAG.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _load_manifest() -> dict:
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))


def _copy_in(source_dir: Path, manifest: dict) -> list[str]:
    """Bring each named book into the project. Returns what was missing."""
    _COPIES.mkdir(parents=True, exist_ok=True)
    missing = []
    for book in manifest["books"]:
        origin = source_dir / book["file"]
        if not origin.exists():
            missing.append(book["file"])
            continue
        shutil.copy2(origin, _COPIES / book["file"])
    return missing


def build(dry_run: bool = False) -> None:
    manifest = _load_manifest()

    conn = sqlite3.connect(":memory:" if dry_run else _scratch())
    conn.executescript(_SCHEMA)

    # Dedup is per collection, not per book, and the order of the manifest is
    # what decides the winner. Al-Hidaya is a commentary that quotes the whole
    # of Bidayat al-Mubtadi inside itself, so the same sentence is genuinely in
    # both files; listing the matn first means the matn keeps it and the reader
    # is not shown one sentence twice under two names.
    seen: dict[tuple[str, str], str] = {}
    duplicates: dict[str, int] = {}

    for book in manifest["books"]:
        path = _COPIES / book["file"]
        if not path.exists():
            print(f"  MISSING  {book['title']}  ({book['file']})")
            continue

        parsed = parse(path.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO book VALUES (?,?,?,?,?)",
            (book["file"], book["collection"], book["title"],
             book["author"], book.get("died")),
        )

        kept = 0
        for page, heading, arabic in parsed.passages:
            key = (book["collection"], bare_letters(arabic))
            if key in seen:
                duplicates[book["file"]] = duplicates.get(book["file"], 0) + 1
                continue
            seen[key] = book["file"]
            conn.execute(
                "INSERT INTO passage (file, collection, page, heading, arabic)"
                " VALUES (?,?,?,?,?)",
                (book["file"], book["collection"], page, heading, arabic),
            )
            kept += 1

        dropped = duplicates.get(book["file"], 0)
        print(f"  {kept:6,} passages  {book['title']}"
              f"   (dropped {dropped:,} duplicate, {parsed.too_short:,} too short,"
              f" {parsed.broken_alif:,} spaced-hamza)")

    total = conn.execute("SELECT count(*) FROM passage").fetchone()[0]
    print(f"\n  {total:,} passages kept, {sum(duplicates.values()):,} duplicates dropped")

    if dry_run:
        print("  dry run: nothing written")
        conn.close()
        return

    conn.commit()
    conn.close()
    _scratch().replace(_DB)
    print(f"  wrote {_DB}")


def _scratch() -> Path:
    """Written beside the real file and moved over it only once it is whole."""
    return _DB.with_suffix(".building")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="source", help="the OpenITI download folder")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = _load_manifest()

    if args.source:
        print(f"Copying {len(manifest['books'])} books into the project...")
        missing = _copy_in(Path(args.source), manifest)
        for name in missing:
            print(f"  NOT FOUND  {name}")

    print("\nParsing:")
    build(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
