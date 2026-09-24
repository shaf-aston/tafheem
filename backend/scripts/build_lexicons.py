"""The classical dictionaries, filed by root, into one database.

    python backend/scripts/build_lexicons.py
    python backend/scripts/build_lexicons.py --dry-run     count everything, write nothing
    python backend/scripts/build_lexicons.py --only lane   one book, into the existing file

What this is for: the Dictionary tab shows one sentence about where a root's
meaning comes from. These are the books that sentence is drawn out of, whole, so
a reader who wants more than the sentence has it without leaving the app.

How this file is arranged
-------------------------
Three levels, each one holding only what its level really shares:

    Shelf          every book, and the single database they are written into
      Lexicon      what any dictionary has: a name, an author, and its entries
        OpenItiBook    the three Arabic books, read out of the OpenITI download
          HeadingBook    a book that starts each entry on a line of its own
            Lisan          ### $ كتب: the entry
            Taj            # |كتب
          MarkerBook       ( كتب ) opening an entry wherever it stands
            Maqayis        read but not shelved, see SHELF at the foot
        Lane           Perseus's XML, English prose with Buckwalter Arabic in it

A book is a class rather than a row of settings because the books differ in
behaviour, not in values: where Lisan and Taj differ is one regular expression,
where Ibn Faris differs is the whole way his file is cut up, and Lane is not the
same kind of file at all. Held as settings that difference has to be spelled as
a name, "colon", looked up in a table of readers somewhere else in the file, and
nothing makes the two halves stay together. Held as classes each book carries its
own rule and cannot be separated from it.

Pure text work, what counts as one root and what counts as rubbish in a line,
stays as plain functions below the classes. It touches no file and belongs to no
one book, and as functions it can be checked a line at a time.

Four books, and they were not chosen by fame. They were chosen because each one
says *in the file itself* where an entry begins, so filing them by root is
reading, not guessing.

Books deliberately left out, and why, so nobody wonders: al-Sihah, Kitab al-Ayn,
Tahdhib al-Lugha, al-Muhkam, al-Qamus al-Muhit and Mujmal al-Lugha are all on
this machine and all excellent, but their files mark only the chapter, the
"باب the letter ع and the letter ل", and leave the roots inside running prose.
Cutting entries out of that means deciding where one ends by eye. A wrong cut
files half of one root's entry under another root, which is the one mistake a
dictionary must not make, so they are not read. al-Mukhassas is arranged by
subject rather than by root and has no root to file under at all.

Where the words come from
-------------------------
The three Arabic books are the OpenITI copies already downloaded to this machine
for the Daleel tab, in the same mARkdown format import_openiti.py reads. Lane is
the Perseus Digital Library's XML from Tufts University, Creative Commons
Attribution-ShareAlike, fetched to Downloads separately because OpenITI holds no
English at all.

Two spellings of the same root
------------------------------
Each book files a root under its own editor's spelling, and they disagree: امر
and أمر, هدي and هدى. Every entry is therefore stored twice over, under the
spelling its own book used and under a folded spelling where those count as one
letter. The fold is read from the same spelling.json the root book uses, never a
second copy, because two tables of "which letters are the same" that disagree is
worse than none. Where folding would make two real roots collide, هنأ and هنا,
the lookup refuses to answer rather than picking one; that rule lives in the
service, with the query that needs it.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services import markup  # noqa: E402
from backend.services.arabic_text import normalize_root  # noqa: E402
from backend.services.root_meaning import read_fold  # noqa: E402

_BACKEND = Path(__file__).resolve().parents[1]
_OPENITI = Path(r"C:\Users\Shaf\Downloads\OpenITI-pri-data_v9")
_LANE = Path(r"C:\Users\Shaf\Downloads\lanes-lexicon-xml")
_OUT = _BACKEND / "data" / "lexicons.db"
_FOLD_BESIDE = _BACKEND / "data" / "maqayees"

_HEADER_END = "#META#Header#End#"
_PAGE = re.compile(r"PageV(\d+)P(\d+)")
_MILESTONE = re.compile(r"\bms\d+\b|@\d+@")
_QURAN_TAG = re.compile(r"@Q[BE]@")
_ARABIC = r"\u0621-\u064a"

# A chapter, not an entry: "فصل", "باب الهمزة والميم". Only ever tested against
# a heading that is otherwise a bare root, never against an entry's own words:
# "( أكل ) الهمزة والكاف واللام باب تكثر فروعه" is Ibn Faris's entry for أكل and
# an earlier rule threw it away for containing the word باب.
_CHAPTER_WORDS = {"باب", "فصل", "كتاب", "حرف"}


# ── the books ────────────────────────────────────────────────────────────────

class Lexicon:
    """One dictionary: who wrote it, and how to get its entries out of its file.

    Everything above the subclasses is the same for every book on the shelf: its
    name and author, the row that credits it, and turning what was read into rows
    ready to store. A subclass supplies one thing, `entries`, because that is the
    only thing these four books genuinely disagree about.
    """

    # Who the book is. Filled in by the one class per book at the bottom.
    id = ""
    title = ""
    english = ""
    author = ""
    died = 0
    language = "ar"
    # Which entry in data/sources.json credits this book. Lane's licence asks for
    # its credit by name, so this is a requirement and not a nicety.
    source = ""

    def entries(self) -> list[tuple[str, str]]:
        """(root, the whole entry) for every entry the book holds."""
        raise NotImplementedError

    def credit(self, order: int) -> tuple:
        """The one row in `book` that says who wrote this and where it came from."""
        return (self.id, self.title, self.english, self.author, self.died,
                self.language, self.source, order)

    def rows(self, fold: dict[int, int]) -> list[tuple]:
        """This book's entries, ready to insert.

        A root appearing twice is normal: a book returns to it in a later volume.
        Both are kept, so nothing the book said is dropped for tidiness.
        """
        rows = []
        for head, said in self.entries():
            key = normalize_root(head)
            if not key or not said:
                continue
            rows.append((self.id, key, key.translate(fold) if fold else key, head,
                         zlib.compress(said.encode("utf-8"), 6)))
        return rows


class OpenItiBook(Lexicon):
    """A book from the OpenITI download, written in mARkdown.

    All three share a file header to skip past and a way of wrapping a long line,
    "~~" at the start meaning the same sentence continued. What they do not share
    is where an entry begins, which is the next level down.
    """

    source = "openiti-lexicons"
    file = ""

    def text(self) -> str:
        """The book's words, past the header its file opens with."""
        raw = (_OPENITI / self.file).read_text(encoding="utf-8", errors="replace")
        return raw[raw.find(_HEADER_END) + len(_HEADER_END):]


class HeadingBook(OpenItiBook):
    """A book that gives every entry a line of its own, `START` matching it.

    The rule captures the root and the rest of that line, which is the first
    words of the entry and not a separate thing.
    """

    START: re.Pattern

    def entries(self) -> list[tuple[str, str]]:
        found: list[tuple[str, list[str]]] = []
        for line in self.text().splitlines():
            if line.startswith("~~"):
                # A wrapped line: the same sentence, continued.
                if found:
                    found[-1][1].append(line[2:])
                continue
            if match := self.START.match(line):
                found.extend(
                    (head, [match.group(2) if match.lastindex > 1 else ""])
                    for head in _heads_of(match.group(1).strip())
                )
            elif found and line.startswith("#"):
                found[-1][1].append(line.lstrip("#").lstrip("| ").strip())
        return [(root, _clean(" ".join(parts))) for root, parts in found]


class MarkerBook(OpenItiBook):
    """A book that opens an entry with "( root )" wherever that falls.

    Ibn Faris does not start a line for a new root. His entries run on: the last
    words of أح and the marker "( أخ )" that opens the next entry share a line,
    2,679 times out of 4,495. Read line by line, only the 1,805 that happen to
    fall at a line start are found and 60% of the book is lost without a word
    said. So this book is flattened first and split on the marker itself.
    """

    MARKER = re.compile(rf"\(\s*([{_ARABIC}]{{2,6}})\s*\)")

    def entries(self) -> list[tuple[str, str]]:
        flat = " ".join(
            line[2:] if line.startswith("~~") else line.lstrip("#").lstrip("| ")
            for line in self.text().splitlines()
        )
        cuts = list(self.MARKER.finditer(flat))
        found = []
        for index, cut in enumerate(cuts):
            end = cuts[index + 1].start() if index + 1 < len(cuts) else len(flat)
            if said := _clean(flat[cut.end():end]):
                found.append((cut.group(1), said))
        return found


class Lane(Lexicon):
    """Lane's Arabic-English Lexicon, from Perseus, and the one book in English.

    A different kind of file from the other three: XML rather than mARkdown, one
    file per letter, and its Arabic written in Latin letters. So it descends
    straight from Lexicon and shares none of the OpenITI machinery.
    """

    id = "lane"
    title = "Lane's Arabic-English Lexicon"
    english = "Arabic explained in English"
    author = "Edward William Lane"
    died = 1876
    language = "en"
    source = "lane"

    ROOT = re.compile(r'<div2\s+n="([^"]+)"\s+type="root"[^>]*>', re.I)
    # The two elements Perseus marks as Arabic: a headword, and Arabic quoted
    # inside an English sentence.
    ARABIC = re.compile(r"<(foreign|orth)\b[^>]*\blang=\"ar\"[^>]*>(.*?)</\1>",
                        re.I | re.S)
    # Where one headword ends and the next begins. The whole opening tag goes,
    # attributes and all: split at the "<" alone and the id and key print as
    # words in the entry.
    BLOCK = re.compile(r"<entryFree\b[^>]*>", re.I)

    def entries(self) -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        for path in sorted(_LANE.glob("*.xml")):
            text = path.read_text(encoding="utf-8", errors="replace")
            # Split on the root divisions themselves: everything between one and
            # the next is that root's entry, headword, senses, quotations and all.
            cuts = list(self.ROOT.finditer(text))
            for index, cut in enumerate(cuts):
                root = _arabic(cut.group(1))
                if len(root) < 2:
                    continue
                end = cuts[index + 1].start() if index + 1 < len(cuts) else len(text)
                if said := self._entry(text[cut.end():end]):
                    found.append((root, said))
        return found

    def _entry(self, fragment: str) -> str:
        """One root's entry, a line per headword, the way the book sets it.

        Perseus opens an <entryFree> at every headword: each verb form, then
        each noun built on the root. That is where the book itself breaks the
        paragraph, and it is the only honest way to find those breaks. Run
        together into one string, علم prints as forty column-inches of grey and
        nothing short of guessing at Lane's own wording gets the breaks back.
        """
        blocks = (self._said(block) for block in self.BLOCK.split(fragment))
        return "\n".join(block for block in blocks if block)

    def _said(self, fragment: str) -> str:
        """One entry as a reader sees it: English prose with its Arabic in Arabic."""
        def turn(match):
            said = match.group(2).strip()
            # A lone star is Lane's own typographic mark for the headword, not
            # the letter ذ that a star stands for everywhere else in this scheme.
            return "" if said == "*" else _arabic(said)

        # markup.as_text is the app's one tag stripper, already used for every
        # other book that arrives as markup, so Lane's XML is not a second set of
        # rules about what a paragraph is.
        # Every kind of gap becomes one space, which is the opposite of what the
        # Arabic books want. Lane has no line breaks of his own in here: the ones
        # in the file are where the XML was indented, and kept they print an
        # entry one ragged fragment per line.
        said = re.sub(r"\s+", " ", markup.as_text(self.ARABIC.sub(turn, fragment)))
        return _fenced(said.strip())


class Maqayis(MarkerBook):
    id = "maqayis"
    title = "معجم مقاييس اللغة"
    english = "The Measures of the Language"
    author = "ابن فارس"
    died = 395
    file = "0395IbnFarisQazwini.MucjamMaqayis.JK008008-ara1"


class Lisan(HeadingBook):
    id = "lisan"
    title = "لسان العرب"
    english = "The Tongue of the Arabs"
    author = "ابن منظور"
    died = 711
    file = "0711IbnManzurIfriqi.LisanCarab.Shamela0001687-ara1.mARkdown"
    # ### $ بكأ: بكأت الناقة ...
    START = re.compile(rf"^#+\s*\$\s*([{_ARABIC}]{{2,6}})\s*:\s*(.*)$")


class Taj(HeadingBook):
    id = "taj"
    title = "تاج العروس"
    english = "The Bride's Crown"
    author = "الزبيدي"
    died = 1205
    file = "1205MurtadaZabidi.TajCarus.JK007140-ara1"
    # # |بدأ, and also # |أي ب, a root spelled with its letters apart, and
    # # |عكث وعنكث, one entry covering two roots. Both are real headings: 4,434
    # of Taj al-Arus's 11,600 entries are written one of those two ways, and a
    # rule that took only the plain ones silently lost a third of the book.
    START = re.compile(rf"^#+\s*\|\s*([{_ARABIC}][{_ARABIC}\s]{{1,13}})\s*$")


# ── the shelf ────────────────────────────────────────────────────────────────

class Shelf:
    """Every book held, in the order they are shown, and the one file they go in.

    The level above a book. It owns what no single book can own: what order they
    stand in, the shape of the database, and the difference between rebuilding
    everything and rebuilding one. A book never opens the database itself.
    """

    SCHEMA = """
CREATE TABLE book (
    id       TEXT PRIMARY KEY,
    title    TEXT NOT NULL,
    english  TEXT NOT NULL,
    author   TEXT NOT NULL,
    died     INTEGER,
    language TEXT NOT NULL,
    source   TEXT NOT NULL,
    ord      INTEGER NOT NULL
);
CREATE TABLE entry (
    book   TEXT NOT NULL REFERENCES book(id),
    root   TEXT NOT NULL,
    folded TEXT NOT NULL,
    head   TEXT NOT NULL,
    body   BLOB NOT NULL
);
CREATE INDEX entry_by_root ON entry(root);
CREATE INDEX entry_by_folded ON entry(folded);
"""

    def __init__(self, *books: Lexicon, out: Path = _OUT):
        self.books = list(books)
        self.out = out

    def wanted(self, only: str | None) -> list[Lexicon]:
        """The books to rebuild. A name nothing answers to is a mistake, not none."""
        if only is None:
            return list(self.books)
        chosen = [book for book in self.books if book.id == only]
        if not chosen:
            names = ", ".join(book.id for book in self.books)
            raise SystemExit(f"No book called {only}. Try: {names}")
        return chosen

    def build(self, only: str | None = None, dry_run: bool = False) -> None:
        fold = read_fold(_FOLD_BESIDE)
        wanted = self.wanted(only)

        made = {book.id: book.rows(fold) for book in wanted}
        for book in wanted:
            rows = made[book.id]
            roots = len({row[1] for row in rows})
            size = sum(len(row[4]) for row in rows) / 1e6
            print(f"{book.id:9} {len(rows):>7} entries  {roots:>6} roots"
                  f"  {size:6.1f}MB stored")
        if dry_run:
            print("dry run, nothing written")
            return

        fresh = only is None
        if fresh:
            self.out.unlink(missing_ok=True)
        db = sqlite3.connect(self.out)
        try:
            if fresh:
                db.executescript(self.SCHEMA)
            for book in wanted:
                db.execute("DELETE FROM entry WHERE book = ?", (book.id,))
                # The order is the book's place on the whole shelf, never its
                # place among the ones being rebuilt: --only lane must not move
                # Lane to the front of a shelf it is meant to stand last on.
                db.execute("INSERT OR REPLACE INTO book VALUES (?,?,?,?,?,?,?,?)",
                           book.credit(self.books.index(book)))
                db.executemany("INSERT INTO entry VALUES (?,?,?,?,?)", made[book.id])
            db.commit()
            db.execute("VACUUM")
        finally:
            db.close()
        print(f"wrote {self.out} ({self.out.stat().st_size / 1e6:.1f}MB)")


# Ibn Faris is not on this shelf. His book is held on its own, in
# data/maqayees/, with the harakat and an English gloss the OpenITI copy has
# neither of; the Dictionary card above the shelf is drawn from that. Building
# him here as well put a second, poorer Ibn Faris on the same page. The reader
# is kept below in case the file is ever the only copy again.
SHELF = Shelf(Lisan(), Taj(), Lane())


# ── the plain text work ──────────────────────────────────────────────────────
# Pure string rules: a line in, a line out. They belong to no one book and touch
# no file, which is what keeps them checkable a case at a time.

def _clean(text: str) -> str:
    """The book's words, without the file's machinery.

    Page markers and milestones are addresses, not words anyone wrote. The
    Qur'an-quote tags mark where a verse is quoted, which nothing here shows, so
    the tag goes and the verse stays.

    Two marks are punctuation rather than rubbish and become it, not nothing.
    "|" is where the book itself broke a sentence and "%" fences each half of a
    line of poetry, so both become a line break: every half-line of verse then
    stands on its own line, the way verse is printed, and each sense of the root
    starts its own. Printed raw they read as stray pipes and percent signs in the
    middle of Ibn Faris; simply deleted, three separate senses run into one
    sentence and a quoted verse becomes part of the prose around it.
    """
    text = _PAGE.sub(" ", text)
    text = _MILESTONE.sub(" ", text)
    text = _QURAN_TAG.sub(" ", text)
    text = text.replace("%", "\n").replace("|", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\s*\n\s*", "\n", text).strip()


def _heads_of(heading: str) -> list[str]:
    """The root or roots one heading names, or nothing if it names a chapter.

    "عكث وعنكث" is one entry covering two roots, and both must find it. "خ و ف"
    is one root with its letters apart, and splitting it on that same "و" would
    invent two roots of one letter each. What separates the two cases is
    whether the pieces are long enough to be roots at all, so that is the test.
    """
    words = heading.split()
    if words and words[0] in _CHAPTER_WORDS:
        return []
    parts = [part for part in re.split(r"\s+و", heading) if part.strip()]
    if len(parts) > 1 and all(len(part.replace(" ", "")) >= 2 for part in parts):
        return parts
    return [heading]


# Perseus holds every Arabic word in Lane, the root headings and the Arabic
# inside the English both, as Buckwalter: Latin letters standing one for one for
# Arabic ones, ktb for كتب and katabahu for كَتَبَهُ. Unconverted, an entry reads
# "1 katabahu, aor. katuba, inf. n. katobN", which is Lane's Arabic printed in a
# script Arabic is not written in. So it is turned back, letters and vowel marks
# together, and only inside the elements the file itself marks as Arabic.
_BUCKWALTER = {
    "'": "ء", "|": "آ", ">": "أ", "&": "ؤ", "<": "إ", "}": "ئ", "A": "ا",
    "b": "ب", "p": "ة", "t": "ت", "v": "ث", "j": "ج", "H": "ح", "x": "خ",
    "d": "د", "*": "ذ", "r": "ر", "z": "ز", "s": "س", "$": "ش", "S": "ص",
    "D": "ض", "T": "ط", "Z": "ظ", "E": "ع", "g": "غ", "f": "ف", "q": "ق",
    "k": "ك", "l": "ل", "m": "م", "n": "ن", "h": "ه", "w": "و", "Y": "ى",
    "y": "ي", "{": "ٱ", "`": "ٰ", "_": "ـ",
    # The marks: two fathas is "an", a sukun is no vowel at all, a shadda
    # doubles the letter. Dropped, كَتَبَ and كُتُب would print as the same word.
    "a": "َ", "u": "ُ", "i": "ِ", "F": "ً", "N": "ٌ", "K": "ٍ", "~": "ّ", "o": "ْ",
    # A caret with no carrier in front of it, 113 times in the book against
    # 12,057 that have one. On its own it is a hamza sitting on the line.
    "^": "ء",
}


# Perseus does not write a hamza carrier the way Buckwalter does. Where the
# scheme has one letter for each, > for أ, & for ؤ, } for ئ, this file writes the
# plain carrier and then a caret: A^, w^, y^. None of the three standard letters
# appears in the whole book, so this is not a variant spelling, it is the only
# spelling. Left alone, 293 of Lane's 5,281 entries print a stray caret in the
# middle of a word, and the vowel marks around it land on the wrong letters:
# شُؤْبُوبٌ came out as شُو^ْبُوبٌ. Turned back into the standard letters first,
# the one table of letters below then reads them like anything else.
_CARRIED_HAMZA = re.compile(r"([Awy])\^")
_CARRIER = {"A": ">", "w": "&", "y": "}"}


def _arabic(buckwalter: str) -> str:
    """Buckwalter back into Arabic script. Unknown marks are left alone."""
    text = _CARRIED_HAMZA.sub(lambda seat: _CARRIER[seat.group(1)], buckwalter)
    return "".join(_BUCKWALTER.get(ch, ch) for ch in text)


# A run of Arabic: its letters, its vowel marks, and the spaces inside a phrase.
_ARABIC_RUN = re.compile(r"[؀-ۿ][؀-ۿ ]*[؀-ۿ]|[؀-ۿ]")


def _fenced(said: str) -> str:
    """Each Arabic run fenced off from the English sentence it sits in.

    An Arabic word dropped bare into a left-to-right sentence drags the
    punctuation and any digit beside it to the wrong side: Lane printed
    "كتب 1, aor." and a browser lays it out as "1 كتب , aor.". The two invisible
    characters here say "this run has its own direction, and it ends here",
    which is the only thing that fixes it; no CSS rule can reach inside a single
    run of text.

    Added after the tags are stripped, not before. The app's stripper takes out
    every bidi control character on the way in, which is right for text from
    somebody else's server and would silently undo this if it ran second.
    """
    return _ARABIC_RUN.sub(lambda run: f"⁨{run.group(0)}⁩", said)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="rebuild one book, leaving the others alone")
    parser.add_argument("--dry-run", action="store_true", help="count, write nothing")
    args = parser.parse_args()
    SHELF.build(only=args.only, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
