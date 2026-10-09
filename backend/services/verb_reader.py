"""A typed verb read back into sarf's table: which root, باب, person and column it is.

The dictionary lacks many verb forms (اِجْلِسِي، ارْحَمُوا، أَفْشُوا) and offers a
name instead; sarf builds every one of them from the root. So nahw asks here, and
the book's rules live in one place, conjugation.py, never retyped as vowel shapes.

How: the table of each stand-in root (data/sarf/reading.json) gives every word a
shape with the root letters left blank (يَفْعَلُونَ -> يَ_ْ_َ_ُونَ). A typed word that
fits a shape names a root; that root is conjugated for real, and the reading stands
only if the real word holds every vowel the reader typed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path

from backend.services import conjugation
from backend.services.harakat import SUKUN, letters
from backend.services.nahw_book import book_words

_READING = Path(__file__).parent.parent / "data" / "sarf" / "reading.json"
_LONG = set("اوي")  # a sukun typed on a long letter is the reader's habit, not a vowel the table must hold


@dataclass(frozen=True)
class Cell:
    """One word of sarf's table: the root, the باب, the column as read
    (madi, mudari, amr, jussive, madi-passive, mudari-passive), and the person."""
    root: str
    form: str
    column: str
    person: str
    gender: str
    number: str
    spelled: str = field(default="", compare=False)  # the table's own spelling of the word, the one the dictionary knows


@lru_cache(maxsize=1)
def _config() -> dict:
    return json.loads(_READING.read_text(encoding="utf-8"))


def _fold(word: str) -> str:
    return word.replace("ٱ", "ا")


def _read_words(column: str, row: int, word: str, form: str) -> list[tuple[str, str]]:
    """(name the column is read as, word) for one cell of the table, its allowed
    spellings too; nothing for a column that is not read."""
    config = _config()
    name = config["columns"].get(column)
    if name is None or (name == "amr" and not conjugation.addressed(row)):
        return []
    word = word.split(" ")[-1]  # لَا يَفْعَلْ: the jussive itself
    found = [(name, word)]
    for spelling in config["spellings"]:
        if form in spelling["forms"] and name in spelling["columns"] and word.startswith(spelling["opens"]):
            found.append((name, spelling["becomes"] + word[len(spelling["opens"]):]))
    return found


@lru_cache(maxsize=1)
def _shapes() -> dict[int, list[tuple[re.Pattern, list[set], str, str, int, str]]]:
    """Every word of every stand-in's table as a pattern over bare letters, filed by
    length: (pattern, the stand-in word's marks, stand-in, باب, row, column read as).
    Built once, ~1.5 s."""
    blanks = _config()["placeholders"]
    shapes: dict[int, list] = {}
    for stand_in, forms in _stand_ins():
        for form in forms:
            try:
                table = conjugation.cells(stand_in, form)
            except ValueError:  # a root kind the rules do not shape yet
                continue
            for row, column, word in table:
                for name, read in _read_words(column, row, word, form):
                    marked = letters(_fold(read))
                    seen: set[str] = set()
                    pattern = ""
                    for letter, _ in marked:
                        if letter in blanks and letter in stand_in:
                            pattern += f"(?P={_group(letter)})" if letter in seen else f"(?P<{_group(letter)}>.)"
                            seen.add(letter)
                        else:
                            pattern += re.escape(letter)
                    shapes.setdefault(len(marked), []).append(
                        (re.compile(pattern), [marks for _, marks in marked], stand_in, form, row, name))
    return shapes


def _stand_ins() -> list[tuple[str, list[str]]]:
    """(stand-in root, the forms to build it in): every kind of root, then the letters
    and roots the rules name, each only where its rule acts."""
    found = [(root, list(conjugation.forms(len(root)))) for root in _config()["stand-ins"]]
    for source in _config()["from-rules"]:
        rule = conjugation.rule(source["rule"])
        forms = rule[source["forms"]]
        if "roots" in source:
            found += [(root, forms) for root in rule[source["roots"]]]
        else:
            into = source["into"]
            if into == "first":
                into = ["_" + root[1:] for root in _config()["stand-ins"] if root[0] in _config()["placeholders"]]
            found += [(shape.replace("_", letter), forms) for shape in into for letter in rule[source["letters"]]]
    return found


def _group(letter: str) -> str:
    """A regex group name for a stand-in letter."""
    return f"r{ord(letter)}"


def _typed(marked: list[tuple[str, set]]) -> list[set]:
    """The marks the reader typed that a word must hold (a sukun on a long letter is habit)."""
    return [marks - ({SUKUN} if letter in _LONG else set()) for letter, marks in marked]


def _untyped(typed: list[tuple[str, set]], word: str) -> int | None:
    """How many of the word's marks the reader left off, or None when the word does
    not hold every mark typed (or is not the same letters)."""
    its = letters(_fold(word))
    if [a for a, _ in typed] != [a for a, _ in its]:
        return None
    if not all(mine <= theirs for mine, (_, theirs) in zip(_typed(typed), its)):
        return None
    return sum(len(theirs - mine) for (_, mine), (_, theirs) in zip(typed, its))


def warm() -> None:
    """Build the shapes now rather than on the first verb read."""
    _shapes()


def read(word: str) -> list[Cell]:
    """Every cell of sarf's table this typed word can be: its letters are the cell's,
    and its typed vowels are all the cell's. Closest first: the cell whose own marks
    the reader typed the most of (أَقِمْ is أَقِمْ, not أَقِّمْ with its shadda left off)."""
    found = dict(_scored(word))
    return sorted(found, key=found.__getitem__)


@lru_cache(maxsize=4096)
def _scored(word: str) -> tuple[tuple[Cell, int], ...]:
    """read()'s cells, each with how many of its marks the reader left off. Cached:
    the card and the tree both ask, as typed and as paused."""
    typed = letters(_fold(word))
    bare = "".join(letter for letter, _ in typed)
    wanted = _typed(typed)
    found: dict[Cell, int] = {}
    for pattern, stand_in_marks, stand_in, form, row, name in _shapes().get(len(typed), []):
        if not (match := pattern.fullmatch(bare)):
            continue
        root = "".join(match.group(_group(c)) if c in _config()["placeholders"] else c for c in stand_in)
        same_kind = conjugation.kind(root) == conjugation.kind(stand_in)
        if same_kind and not all(mine <= theirs for mine, theirs in zip(wanted, stand_in_marks)):
            continue  # the same kind of root keeps the stand-in's vowels: no need to build its table
        try:
            own = conjugation.row_cells(root, form, row)
        except ValueError:
            continue
        reads = [read for column, real in own for named, read in _read_words(column, row, real, form) if named == name]
        scores = [score for read in reads if (score := _untyped(typed, read)) is not None]
        if scores:
            cell = Cell(root, form, name, *conjugation.person_features(row), spelled=reads[0])
            found[cell] = min(min(scores), found.get(cell, min(scores)))
    return tuple(found.items())


def past(cell: Cell) -> str:
    """The dictionary form of the cell's verb, its past for "he" (أَفْشَى، أَقَامَ);
    "" when the command fits more than one باب and the past is not known."""
    if not cell.form:
        return ""
    return dict(conjugation.row_cells(cell.root, cell.form, 0))["madi"]


def command(word: str, governed: bool = False, root: str = "") -> Cell | None:
    """The command this typed word is (اِجْلِسِي، ارْحَمُوا، قُمْ), or None.

    `root` is the one the dictionary read the word with, if any: where sarf finds
    it, its readings are the word's (يَصْبِرْ is صبر, not a four-letter يصبر; اُكْتُبُوا
    is كتب, not a Form VIII passive of كبو). `governed` says a particle that puts a
    present verb in jazm or nasb was typed just before: a command never follows one,
    and without one the jussive's spelling cannot stand (أَقِمْ alone is a command).
    Of what is left, the closest readings must all be a command to the same person;
    تَحَاسَدُوا is also a past verb, so the dictionary keeps its say.
    """
    if governed:
        return None
    if not any(marks for _, marks in letters(word)[:-1]):
        # without its vowels a word fits a command and much else (الله، البر); the last
        # letter's alone is no help either, it is the case or a sukun of pausing (اللهِ)
        return None
    found = dict(_scored(word))
    found = {c: score for c, score in found.items() if c.root == root} or found
    found = {c: score for c, score in found.items() if c.column != "jussive"}
    if not found:
        return None
    closest = [c for c, score in found.items() if score == min(found.values())]
    people = {(c.person, c.gender, c.number) for c in closest}
    if all(c.column == "amr" for c in closest) and len(people) == 1:
        # its root tied between بابs whose pasts differ (ضَرَبَ، حَسِبَ): the command is sure, its past is not
        pasts = {past(c) for c in closest if c.root == closest[0].root}
        return closest[0] if len(pasts) == 1 else replace(closest[0], form="")
    return None


def typed_fully(word: str, cell: Cell) -> bool:
    """The reader typed every mark of the cell's spelling (سَمِّ), so no mark of it is a guess
    (ابْنُ as اُبْنُ wants a damma the reader left off)."""
    return _untyped(letters(_fold(word)), cell.spelled) == 0


def known_as(word: str) -> str | None:
    """A word the dictionary has no reading for, written as sarf's table prints it, its joined
    letters (وَ، فَ، لْ) kept as typed: فَلْيَسْتَعْفِفْ is فَلْيَسْتَعِفَّ, which the dictionary reads.
    None where no verb of the table fits, or the fit is not one word: the vowels typed are the
    evidence, so a bare word (الله) fits too much, and a command has its own reading (command)."""
    marked = letters(word)
    for cut in range(min(len(marked), _JOINED_MOST) + 1):
        front, rest = marked[:cut], marked[cut:]
        if not all(letter in _joined() for letter, _ in front) or not any(marks for _, marks in rest[:-1]):
            continue
        found = dict(_scored(_spell(rest)))
        closest = [cell for cell, score in found.items() if score == min(found.values()) and cell.column != "amr"] if found else []
        if closest and len({cell.spelled for cell in closest}) == 1:
            return _spell(front) + closest[0].spelled
    return None


# a verb takes at most two letters in front: وَ or فَ, then لْ
_JOINED_MOST = 2


@lru_cache(maxsize=1)
def _joined() -> set[str]:
    """The one-letter words that are written onto the front of a verb: the conjunctions and the jazm particle."""
    return {w for family in ("atf", "jazm") for w in book_words(family) if len(w) == 1}


def _spell(marked: list[tuple[str, set]]) -> str:
    return "".join(letter + "".join(sorted(marks)) for letter, marks in marked)
