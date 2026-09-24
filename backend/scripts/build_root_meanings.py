"""Build the classical root book the Dictionary tab reads.

    python backend/scripts/build_root_meanings.py

Writes backend/data/maqayees/roots.json. Needs the network once, and
`pip install access-parser`. Every knob it turns lives in build.json beside the
output, this file holds no tuning value of its own.

Where the words come from
-------------------------
Ibn Faris's Maqayees al-Lugha (d. 395 AH), in Abd al-Salam Harun's edition, 
the same edition as the scanned PDF, checked by matching printed page numbers.
It is out of copyright, and the Arabic was typed up by people for the Shamela
library, so nothing here is read off a scan by a machine.

What this script decides
------------------------
Only where an entry starts and stops. Ibn Faris opens each entry by naming the
root's letters and stating its origin sense; that statement is taken verbatim.
The entry list comes from the book's own table of contents, so no root is
invented and none is guessed at from the prose.

Each root is written once, under the spelling the editor used. Matching a
reader's spelling to it is the reader's side of the job and belongs to the
lookup in services/root_meaning.py, not to a second copy of the entry here.
"""
from __future__ import annotations

import io
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.root_meaning import read_fold  # noqa: E402, needs the path above

DATA = Path(__file__).resolve().parent.parent / "data" / "maqayees"
OUT = DATA / "roots.json"


# ── Config ──────────────────────────────────────────────────────────────────
# One reader of build.json, so no value below is written twice.

class Config:
    """Every knob, and the compiled patterns built from them."""

    def __init__(self, path: Path):
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.source = raw["source"]
        self.index = raw["index"]
        self.entry = raw["entry"]
        # The one thing the builder and the lookup must agree on, so it is one
        # file both read rather than a rule written down twice.
        self.fold = read_fold(path.parent)

        p = raw["patterns"]
        self.diacritics = re.compile(p["diacritics"])
        self.lacuna = re.compile(p["lacuna"])
        self.section_heading = re.compile(p["section_heading"])
        self.section_label = re.compile(p["section_label"])
        self.sense_markers = re.compile(p["sense_markers"])
        self.multi_origin = tuple(p["multi_origin_words"])
        self.min_branch_chars = p["min_branch_chars"]
        # One table, two readers: which words are letter names at all, and which
        # letter each one names. Written down once so they cannot disagree.
        self.names_of = p["letter_names"]
        every = {name for names in self.names_of.values() for name in names}
        # Longest first, so "الحرف المعتل" is never half-matched as "الحرف".
        names = sorted(every, key=len, reverse=True)
        self.letter_names = re.compile("|".join(re.escape(n) for n in names))
        self.connectives = re.compile(p["connectives"])


def sidecar(name: str) -> dict:
    """An optional hand-supplied input beside the output, keyed by root.

    Missing is normal and not an error, the book itself is the required input
    and these only add to it. Unreadable is an error, because a file that is
    there and cannot be parsed is a mistake someone needs to hear about rather
    than a silently thinner result.
    """
    path = DATA / name
    if not path.is_file():
        print(f"  no {name}, building without it")
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be an object keyed by root, not {type(data).__name__}")
    return data


# ── The book, as one stream of text ─────────────────────────────────────────

def fetch(cfg: Config) -> bytes:
    """The Shamela database, downloaded and unzipped in memory."""
    url = f'https://archive.org/download/{cfg.source["archive_item"]}/{urllib.parse.quote(cfg.source["archive_file"])}'
    print("downloading the book…")
    with urllib.request.urlopen(url, timeout=cfg.source["timeout_seconds"]) as response:
        blob = response.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        return archive.read(archive.namelist()[0])


def read_tables(cfg: Config, blob: bytes) -> tuple[dict, dict]:
    """The database's text and index tables. It predates Unicode: cp1256 bytes."""
    try:
        from access_parser import AccessParser
    except ImportError as e:  # pragma: no cover - an install instruction, not logic
        raise SystemExit("needs access-parser:  pip install access-parser") from e

    scratch = DATA / "_book.bok"
    scratch.write_bytes(blob)
    try:
        db = AccessParser(str(scratch))
        return db.parse_table(cfg.source["text_table"]), db.parse_table(cfg.source["toc_table"])
    finally:
        scratch.unlink(missing_ok=True)


def decode(cfg: Config, value: object) -> str:
    """One page of the book as text, with one kind of line break in it.

    The database is from the DOS-and-Windows era and breaks a line with a
    carriage return, sometimes alone, sometimes paired. Those breaks are the
    editor's own, they are where a line of poetry ends, so they are kept, but
    written the one way the web understands. A lone carriage return survives a
    round trip through JSON and then renders as nothing at all, which is how a
    whole entry ends up printed as a single block.
    """
    encoding = cfg.source["encoding"]
    if not isinstance(value, str):
        return ""
    text = value.encode("latin-1", "replace").decode(encoding, "replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def stream_pages(cfg: Config, text: dict) -> tuple[str, dict[int, int]]:
    """The whole book as one string, and where each page starts in it.

    One stream rather than a list of pages because an entry runs across a page
    break, and the heading that ends it may be on the following page.
    """
    pages = {text["id"][i]: decode(cfg, text["nass"][i]) for i in range(len(text["id"]))}
    offset, parts, cursor = {}, [], 0
    for page_id in sorted(pages):
        offset[page_id] = cursor
        parts.append(pages[page_id])
        cursor += len(pages[page_id]) + 1
    return "\n".join(parts), offset


def index_key(cfg: Config, title: str) -> str:
    """The root a line of the table of contents names, under one spelling.

    The editor wrote that page the way the entry is printed, so a line reaches
    here wearing his punctuation, and; in the chapters of words longer than
    three letters, the definite article and sometimes the connective he opened
    the sentence with: "(والحناتم) :". None of those are letters of the root.

    The one place that decides what a contents line is called, so the index and
    the search can never disagree about it. What comes back may still be no root
    at all; read_index does that judging.
    """
    # "(رَبَى \\ أ)" is one entry filed under two spellings of its weak last
    # letter. It is called by the first; the search folds ى onto أ, so a reader
    # who types the second still lands on it.
    word = strip(cfg, title).split(cfg.index["alternate_mark"])[0]
    word = word.strip(cfg.index["strip_chars"])
    for opener in cfg.index["drop_openers"]:
        if word.startswith(opener):
            word = word[len(opener):].strip(cfg.index["strip_chars"])
    # The و of وطر is a letter; the و of والحناتم is "and". Only the second is
    # ever dropped, and only where a root of more than three letters is left.
    for prefix in (cfg.index["connective"], cfg.index["article"]):
        if word.startswith(prefix) and len(word) - len(prefix) >= cfg.index["min_after_prefix"]:
            word = word[len(prefix):]
    return word


def read_index(cfg: Config, toc: dict) -> list[tuple[str, int]]:
    """The roots the book's own table of contents names, in its own order.

    A line still holding a space once its punctuation is off is a chapter
    heading or the editor's closing line, "تم كتاب الغين", never a root.
    """
    rows = [
        (index_key(cfg, decode(cfg, toc["tit"][i])), toc["id"][i])
        for i in range(len(toc["id"]))
        if toc["lvl"][i] >= cfg.index["min_level"] and decode(cfg, toc["tit"][i]).startswith("(")
    ]
    return [
        (root, page_id) for root, page_id in rows
        if " " not in root and cfg.index["min_letters"] <= len(root) <= cfg.index["max_letters"]
    ]


def place_headings(cfg: Config, full: str, offset: dict, index: list) -> tuple[list, list]:
    """Where in the stream each indexed root is actually printed.

    Searched forward only, from just before the page the index names, so the
    headings come out in the book's order and an entry can never start before
    the one above it ended.
    """
    placed, unplaced, cursor = [], [], 0
    mark = f"{cfg.diacritics.pattern}*"

    def spell(word: str) -> str:
        """A word as the book prints it: every letter may wear a vowel mark."""
        return "".join(r"\s+" if c == " " else re.escape(c) + mark for c in word)

    for root, page_id in index:
        letters = r"\s*".join(re.escape(c) + mark for c in root)
        # The printed heading still wears what index_key took off the contents
        # line, so a root long enough to have had it taken off must be allowed
        # to find it again. A short root is matched bare: letting "(وطر)" answer
        # for طر would hand one root's entry to another.
        head = ""
        if len(root) >= cfg.index["min_after_prefix"]:
            openers = "|".join(spell(o) for o in cfg.index["drop_openers"])
            for prefix in (f"(?:{openers})", spell(cfg.index["connective"]),
                           spell(cfg.index["article"])):
                head += f"(?:{prefix})?"
        # Some weak-final roots are filed under both their spellings at once, 
        # "(رَبَى \\ أ)" is ربى and ربأ. The entry is one entry; it is placed
        # under the first spelling and the second is written beside it.
        alternate = r"(?:\s*\\\s*[^\s\])]" + mark + r")?"
        # Either bracket on either side: a few headings the editor added are
        # typed "( [بَقَرَ) …]", with the brackets crossed over.
        pattern = re.compile(r"[\[(]\s*[\[(]?\s*" + head + letters + alternate + r"\s*[\])]")
        window = max(offset.get(page_id, 0) - cfg.index["lookbehind_chars"], cursor)
        match = pattern.search(full, window)
        if not match:
            unplaced.append(root)
            continue
        placed.append((root, match.start(), match.end()))
        cursor = match.end()
    return placed, unplaced


def named_by_the_prose(cfg: Config, full: str, placed: list) -> list:
    """Entry headings the editor printed but left off his contents page.

    Five of them, and each costs twice: the entry itself is lost, and the entry
    above it runs on and prints it as part of its own meaning, أم carried 615
    characters of the entry for أه that way.

    A bracketed word is not enough on its own; brackets run all through the
    prose. What makes a heading certain is what follows it. Ibn Faris opens an
    entry by naming its own letters, "(حدأ) الحاء والدال والهمزة", so a
    bracketed word whose next words name exactly its own letters, in order and
    with nothing but connectives between them, is a heading and can be nothing
    else. Over the whole book that finds five, and no false one.
    """
    # Searched without the vowel marks, because that is how the letter names are
    # written down; where each stripped character came from is kept alongside,
    # so what comes back is an offset into the book itself.
    bare, origin = [], []
    for at, letter in enumerate(full):
        if not cfg.diacritics.match(letter):
            bare.append(letter)
            origin.append(at)
    bare = "".join(bare)

    marked = re.compile(r"[\[(]\s*((?:%s)?(?:%s)?[ء-ي]{%d,%d})\s*[\])]" % (
        re.escape(cfg.index["connective"]), re.escape(cfg.index["article"]),
        cfg.index["min_letters"], cfg.index["max_letters"]))
    # Every character an already-placed heading covers, not just where it began.
    # A heading the editor typed with its brackets crossed, "( [بَقَرَ) …]", 
    # is placed from the inner bracket and found here from the outer one, and
    # comparing only the two start points would file it as a second entry two
    # characters before the first.
    known = {at for _, start, end in placed for at in range(start, end)}
    named = {root for root, _, _ in placed}
    found = []
    for match in marked.finditer(bare):
        start, end = origin[match.start()], origin[match.end() - 1] + 1
        if known & set(range(start, end)):
            continue
        root = index_key(cfg, match.group(1))
        after = bare[match.end():match.end() + cfg.index["names_lookahead_chars"]]
        if _spells_its_own_letters(cfg, root, after) or _printed_twice(named, bare, match, root):
            found.append((root, start, end))
    return found


def _spells_its_own_letters(cfg: Config, root: str, after: str) -> bool:
    """Whether what follows names this root's letters, in order, immediately.

    How Ibn Faris opens an entry of three letters, "(حدأ) الحاء والدال
    والهمزة", and nothing else in the prose looks like it.
    """
    cursor = 0
    for letter in root:
        spots = [at for name in cfg.names_of.get(letter, ())
                 if (at := after.find(name, cursor)) != -1]
        if not spots or min(spots) - cursor > cfg.index["names_within_chars"]:
            return False
        cursor = min(spots) + 1
    return True


def _printed_twice(named: set, bare: str, match: "re.Match", root: str) -> bool:
    """Whether the book prints these letters twice and the index only knew once.

    An entry for a word of more than three letters does not spell its letters
    out; it names the word and defines it: "(الْعَسَلَّقُ) : الظَّلِيمُ", the
    ostrich. That shape alone is far too common to trust, Ibn Faris writes
    "قَالَ:" and "يَوْمٌ (عَمَرَّسٌ) : شَدِيدٌ" the same way, and taking every
    one of them invented 35 roots and cut 29 entries short.

    What makes this one certain is that the contents page already names these
    letters. It has one row for them and the book has two different words under
    it, العَسْلَق a bold predator, العَسَلَّق an ostrich; so the row was spent
    on the first, and the entry above the second was printing the ostrich as
    part of its own meaning. Over the whole book this recognises that one.
    """
    if root not in named or not re.match(r"\s*:", bare[match.end():]):
        return False
    before = bare[:match.start()].rstrip()
    return not before or before[-1] == "." or "\n" in bare[len(before):match.start()]


# ── Cutting one entry out of the stream ─────────────────────────────────────

def strip(cfg: Config, text: str) -> str:
    """Without the vowel marks, for comparing. Never for printing."""
    return cfg.diacritics.sub("", text)


def unpaired(text: str) -> str:
    """Drop a square bracket whose partner is not here.

    The editor's own brackets, "[أحدهما]", "[هو]", are balanced and stay. One
    left stranded came from a heading typed with its brackets crossed over, and
    would otherwise be printed in the middle of a sentence.
    """
    while text.count("]") > text.count("["):
        text = text.replace("]", "", 1)
    while text.count("[") > text.count("]"):
        text = "".join(text.rsplit("[", 1))
    return text.strip(" ،؛")


def before_next_chapter(cfg: Config, text: str) -> str:
    """Everything up to where the next chapter of the book begins.

    An entry is cut at the next root's heading, but the last root of a chapter
    is followed by the chapter's own closing matter and then the next chapter's
    opening, none of which is this root's entry. Without this, 654 entries
    carried a foreign chapter and eleven of them were almost entirely it.
    """
    chapter = cfg.section_heading.search(text)
    return text[: chapter.start()] if chapter else text


def sentences(text: str) -> list[str]:
    """The entry's opening, split where the editor put his full stops."""
    return [piece.strip() for piece in text.split(".") if piece.strip()]


def clean_body(cfg: Config, raw: str) -> str:
    """The entry with the book's own furniture taken off both ends.

    The single owner of what is furniture and what is Ibn Faris. The sense is
    read out of the result, so the two can never disagree about where the entry
    starts, which is exactly how ten entries came to print their first
    sentence twice.
    """
    body = unpaired(re.sub(r"^[\s\])[(:;،]+", "", raw).strip())
    body = before_next_chapter(cfg, body).strip()
    parts = sentences(body)
    # A chapter's name standing where an entry's opening should be: it belongs
    # to the book's structure, not to this root.
    while parts and cfg.section_label.search(strip(cfg, parts[0])):
        parts.pop(0)
        body = body.split(".", 1)[1] if "." in body else ""
        # The sentence list drops empty pieces and the slice above does not, so
        # a label closed by more than one full stop would leave the body opening
        # on punctuation the sense read out of it does not have, and the card
        # strips the sense off the body by matching that opening exactly.
        body = body.lstrip(" .،؛")
    return body


def carries_a_sense(cfg: Config, sentence: str) -> bool:
    """Whether a sentence says anything beyond naming the root's letters.

    Ibn Faris opens "the B and the H and the R" and usually continues in the
    same breath, but where the editor put a full stop after the enumeration,
    that opening is the root spelled out and nothing more. Printing it as the
    origin sense tells the reader the letters they just typed.
    """
    residue = cfg.letter_names.sub("", strip(cfg, sentence))
    return len(cfg.connectives.sub("", residue).strip()) > 0


def origin_sentence(cfg: Config, body: str) -> str:
    """The entry's opening statement, read out of an already-cleaned body.

    Ibn Faris opens by naming the root's letters and usually states the sense in
    the same breath. Where the editor put a full stop after the enumeration, that
    opening tells the reader only the letters they typed, so the sentence after
    it is taken as well, 221 entries had a headline that said nothing.
    """
    if cfg.lacuna.search(body[: cfg.entry["lacuna_window_chars"]]):
        return ""  # a gap in the manuscript is not a meaning
    taken: list[str] = []
    for piece in sentences(body)[: cfg.entry["sense_lookahead_sentences"]]:
        taken.append(piece)
        if carries_a_sense(cfg, " ".join(taken)):
            break
    return unpaired(". ".join(taken).strip())


def branches(cfg: Config, sentence: str) -> list[str]:
    """The separate origins, when Ibn Faris marks them. Never a guessed split."""
    if all(word not in strip(cfg, sentence) for word in cfg.multi_origin):
        return []
    colon = sentence.find(":")
    if colon == -1:
        return []
    tail = sentence[colon + 1:]
    cuts = [m.start() for m in cfg.sense_markers.finditer(tail)]
    if len(cuts) < 2:
        return []
    cuts.append(len(tail))
    out = []
    for start, end in zip(cuts, cuts[1:]):
        piece = unpaired(cfg.sense_markers.sub("", tail[start:end], count=1).strip(" ،؛"))
        if len(piece) > cfg.min_branch_chars:
            out.append(piece)
    return out


def slice_entries(cfg: Config, full: str, placed: list) -> tuple[dict, list]:
    """One record per root: the opening sense, and the whole entry behind it.

    The body is kept whole and never split. Ibn Faris marks where one sense
    ends in a minority of entries, and three ways of measuring that rate
    disagreed by 35% to 91%, a boundary three methods disagree about that much
    is not one to print a guess at.
    """
    book, blank, twice = {}, [], []
    for i, (root, _, start) in enumerate(placed):
        # To where the next heading *begins*, so no entry ever swallows the next
        # root's name and prints it as part of this root's meaning.
        end = placed[i + 1][1] if i + 1 < len(placed) else len(full)
        body = clean_body(cfg, full[start:end])
        core = origin_sentence(cfg, body)
        if len(core) < cfg.entry["min_core_chars"]:
            blank.append(root)
            continue
        # Twice in the book, the same spelling heads two different words; 
        # العَسْلَق a bold predator and العَسَلَّق an ostrich, كتو twice over. One
        # key can hold one record, so the second entry is written under the
        # first rather than thrown away: the book really does file both under
        # those letters, and dropping one loses Ibn Faris's words with nothing
        # on screen to show they are missing.
        if root in book:
            book[root]["body"] += "\n\n" + body
            twice.append(root)
            continue
        book[root] = {
            "core_meaning": core,
            "sarf_pattern": "",
            "variances": branches(cfg, core),
            "body": body,
        }
    return book, blank, twice


# ── The two hand-supplied inputs ────────────────────────────────────────────

def add_blanks(cfg: Config, book: dict) -> int:
    """Roots the printed edition leaves blank that the scanned copy could read.

    Held to the same bar as the book itself: an opening that is a manuscript
    gap or names only the root's letters is not a meaning here either.
    """
    added = 0
    for root, entry in sidecar("blanks.json").items():
        core = str(entry.get("core_meaning", "")).strip()
        if root in book or len(core) < cfg.entry["min_core_chars"]:
            continue
        if cfg.lacuna.search(core) or not carries_a_sense(cfg, core):
            continue
        book[root] = {
            "core_meaning": core, "sarf_pattern": "", "variances": [], "body": "",
            "english": str(entry.get("core_meaning_english", "")).strip(),
        }
        added += 1
    return added


def attach_english(cfg: Config, book: dict) -> int:
    """The plain gloss, matched to the entry however either side spells the root.

    The one thing here a machine read off a page image, so it stays its own
    field and the card badges it separately, it must never be read as carrying
    the same authority as the typed Arabic beside it.

    Matched through the folded spelling because the two sides disagree: the
    book files أخ and the gloss is filed under اخ. Matching on the letters as
    typed lost 407 real glosses to that difference alone.
    """
    english = sidecar("english.json")
    folded = {}
    for root in book:
        folded.setdefault(root.translate(cfg.fold), []).append(root)

    attached = 0
    for key, entry in english.items():
        gloss = str(entry.get("core_meaning_english", "")).strip()
        if not gloss:
            continue
        # Two roots sharing a folded spelling are two different roots, and this
        # file cannot tell them apart: it is keyed without the hamza signs, which
        # are the whole difference between دفأ, warmth, and دفا, a long bend. So
        # the folded key decides, and only where it names one root; an exact hit
        # is not proof when the key had no way to spell the other one. Four pairs
        # are like this, and one of them had the wrong meaning printed under it.
        claimants = folded.get(key.translate(cfg.fold), [])
        targets = [key] if key in book and len(claimants) < 2 else claimants
        if len(targets) != 1:
            continue
        record = book[targets[0]]
        if not record.get("english"):
            record["english"] = gloss
            attached += 1
    return attached


# ── Wiring ──────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cfg = Config(DATA / "build.json")
    # A path to an already-downloaded copy, so a re-cut of the same book gives
    # the same result twice and does not depend on archive.org still serving it.
    blob = Path(argv[0]).read_bytes() if argv else fetch(cfg)
    text, toc = read_tables(cfg, blob)
    full, offset = stream_pages(cfg, text)
    placed, unplaced = place_headings(cfg, full, offset, read_index(cfg, toc))
    unlisted = named_by_the_prose(cfg, full, placed)
    placed = sorted(placed + unlisted, key=lambda heading: heading[1])

    book, blank, twice = slice_entries(cfg, full, placed)
    blanks_added = add_blanks(cfg, book)
    english_attached = attach_english(cfg, book)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"wrote {OUT}")
    print(f"  {len(book)} roots, {sum(bool(v.get('english'))
                                  for v in book.values())} with English")
    print(f"  {english_attached} glosses attached, {blanks_added} roots taken from the scan")
    if unplaced:
        print(f"  {len(unplaced)} headings not found in the text: {unplaced}")
    if blank:
        print(f"  {len(blank)} entries the print leaves blank: {blank}")
    if twice:
        print(f"  {len(twice)} spellings the book heads twice, both kept: {twice}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
