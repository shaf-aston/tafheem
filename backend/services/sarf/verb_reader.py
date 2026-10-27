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
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path

from backend.services.sarf import conjugation
from backend.services.text.harakat import KASRA, SUKUN, letters, plural_alef
from backend.services.nahw.book import book_words, is_one

_READING = Path(__file__).parent.parent.parent / "data" / "sarf" / "reading.json"
_LONG = set("اوي")  # a sukun typed on a long letter is the reader's habit, not a vowel the table must hold
_MADDA = "آ"  # a hamza, its fatha and the alif after it: a vowel written into the letter itself (آتِ)


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


def _letters_of(root: str) -> list[str]:
    """A root's letters in any order, its weak و and ي as one."""
    return sorted(root.replace("ي", "و"))


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
        if form not in spelling.get("forms", [form]) or name not in spelling["columns"]:
            continue
        if (opens := spelling.get("opens")) and word.startswith(opens):
            found.append((name, spelling["becomes"] + word[len(opens):]))
        elif (within := spelling.get("within")) and within in word:
            found.append((name, word.replace(within, spelling["becomes"])))
    return found


@lru_cache(maxsize=1)
def _shapes() -> dict[int, list[tuple[re.Pattern, list[set], str, str, int, str]]]:
    """Every word of every stand-in's table as a pattern over bare letters, filed by
    length: (pattern, the stand-in word's marks, stand-in, باب, row, column read as).
    Built once, ~1.5 s."""
    blanks = _config()["placeholders"]
    root_letter = f"[^{re.escape(_config()['never-root'])}]"
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
                            pattern += f"(?P={_group(letter)})" if letter in seen else f"(?P<{_group(letter)}>{root_letter})"
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


def _voweled(marked: list[tuple[str, set]]) -> bool:
    """A vowel typed before the last letter, whose own is the case or a pause: آ carries one in it."""
    return any(marks or letter == _MADDA for letter, marks in marked[:-1])


def _untyped(typed: list[tuple[str, set]], word: str) -> int | None:
    """How many of the word's marks the reader left off, or None when the word does
    not hold every mark typed (or is not the same letters). A sukun on a long letter is
    no mark either way: أَدْرِي left off none of أَدْرِيْ, so "I know" is as close as "know!"."""
    its = letters(_fold(word))
    if [a for a, _ in typed] != [a for a, _ in its]:
        return None
    if not all(mine <= theirs for mine, (_, theirs) in zip(_typed(typed), its)):
        return None
    return sum(len(theirs - mine) for mine, theirs in zip(_typed(typed), _typed(its)))


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


def command(word: str, governed: bool = False, root: str = "", vouched: bool = False) -> Cell | None:
    """The command this typed word is (اِجْلِسِي، ارْحَمُوا، قُمْ), or None.

    `root` is the one the dictionary read the word with, if any: where sarf finds
    it, its readings are the word's (يَصْبِرْ is صبر, not a four-letter يصبر; اُكْتُبُوا
    is كتب, not a Form VIII passive of كبو). `governed` says a particle that puts a
    present verb in jazm or nasb was typed just before: a command never follows one,
    and without one the jussive's spelling cannot stand (أَقِمْ alone is a command).
    `vouched` says the sentence shows a verb where no vowel was typed (repair.typed),
    so the bare letters are read too (اكتبي درسك).
    Of what is left, the closest readings must all be a command to the same person;
    تَحَاسَدُوا is also a past verb, so the dictionary keeps its say.
    """
    if governed:
        return None
    if not vouched and not _voweled(letters(word)):
        # without its vowels a word fits a command and much else (الله، البر); the last
        # letter's alone is no help either, it is the case or a sukun of pausing (اللهِ)
        return None
    found = dict(_scored(word))
    found = {c: score for c, score in found.items() if c.root == root} or found
    found = {c: score for c, score in found.items() if c.column != "jussive"}
    if not found:
        return None
    closest = [c for c, score in found.items() if score == min(found.values())]
    # اُكْتُبَا: the dual is one word for two men or two women, both أنتما, so one person
    # only for the root the dictionary read: اهْدِنَا is هدي with "us", not a dual of هدن
    # قِفَا: the dictionary's قفو holds وقف's letters, out of order, so it still vouches for it
    # قفي too: a dictionary spells a weak root's last letter و or ي, so the two are one letter here
    closest = [c for c in closest if _letters_of(c.root) == _letters_of(root)] or closest if root else closest
    sure = bool(root) and all(_letters_of(c.root) == _letters_of(root) for c in closest)
    people = {(c.person, "" if c.number == "d" and sure else c.gender, c.number) for c in closest}
    if all(c.column == "amr" for c in closest) and len(people) == 1:
        # its root tied between بابs whose pasts differ (ضَرَبَ، حَسِبَ): the command is sure, its past is not
        pasts = {past(c) for c in closest if c.root == closest[0].root}
        return closest[0] if len(pasts) == 1 else replace(closest[0], form="")
    return None


def typed_fully(word: str, cell: Cell) -> bool:
    """The reader typed every mark of the cell's spelling (سَمِّ), so no mark of it is a guess
    (ابْنُ as اُبْنُ wants a damma the reader left off)."""
    return _untyped(letters(_fold(word)), cell.spelled) == 0



def called(before: str, after: str, read_as: str = "") -> bool:
    """A noun called is never the command its letters spell (Ibn Aqil V1 p15: والندا): after يا (يَا رَبِّ), or with
    its يا left off, opening the sentence before the command said to it (رَبِّ اغْفِرْ لِي; V3 p256). `before` is the
    bare word typed before it, "" opening the sentence; `read_as` the tense the sentence's reading gave `after`, a
    command with its object written on (رَبِّ زِدْنِي) that command() alone cannot split. A noun after is no command
    said (رَبِّ ابْنَكَ: "raise your son", not ابْنَ + كَ)."""
    return is_one(before, "nida") or not before and (read_as == "c" or command(after) is not None)


def known_as(word: str) -> str | None:
    """A word the dictionary has no reading for, written as sarf's table prints it, its joined
    letters (وَ، فَ، لْ) kept as typed: فَلْيَسْتَعْفِفْ is فَلْيَسْتَعِفَّ, which the dictionary reads.
    None where no verb of the table fits, or the fit is not one word: the vowels typed are the
    evidence, so a bare word (الله) fits too much, and a command has its own reading (command)."""
    for front, _, closest in _cuts(word):
        closest = [cell for cell in closest if cell.column != "amr"]
        if closest and len({cell.spelled for cell in closest}) == 1:
            return _spell(front) + closest[0].spelled
    return None


def reading_of(word: str, known: Callable[[str], bool] | None = None) -> dict | None:
    """A verb the dictionary cannot read even as the table spells it (يَسْتَعْتِبُوا), read off
    the table in the dictionary's own features (reading.json `camel`): {pos, asp, vox, ...}.
    None unless the closest cells agree on its tense and voice. What they do not agree on is
    left out, not guessed: تَسْتَحِ is "she" or "you", أَفْشُوا has فشو or فشي; both are verbs.
    `known` says whether the dictionary has a verb, by its past: of the closest cells, the verbs
    it has are the word's, and where it has none of them, a verb it has with an object pronoun
    written on is (اِهْدِنَا is هَدَى + نا, not a dual of هَدَنَ, a verb no text it learnt from uses)."""
    for front, rest, closest in _cuts(word):
        if known:
            seen = [c for c in closest if known(past(c))]
            if not seen and (split := _with_object(word, known)) and known(split.get("lex", "")):
                return split
            closest = seen or closest
        if len({tuple(_config()["camel"][c.column].items()) for c in closest}) != 1:
            continue
        cells = [{**_config()["camel"][c.column], "per": c.person, "gen": c.gender, "num": c.number, "root": c.root,
                  "lex": past(c), "weak_last": c.root[-1:] in "وي"} for c in closest]
        return {"pos": "verb", **{key: value for key, value in cells[0].items() if all(c[key] == value for c in cells)},
                **(_pieces(front, rest) if front else {})}
    return _with_object(word, known)


# a long letter and the vowel before it that makes it long (اُكْتُبِي، اُكْتُبُوا، اُكْتُبَا)
_LENGTHENS = {"ي": KASRA, "و": "ُ", "ا": "َ"}


def _with_object(word: str, known: Callable[[str], bool] | None = None) -> dict | None:
    """reading_of a verb with its object pronoun written on (ظَلَمَكَ is ظَلَمَ + كَ), the table
    holding the verb alone: the longest pronoun first, the verb before it voweled to its end."""
    marked = letters(word)
    for size in (3, 2, 1):
        verb, pronoun = marked[:-size], marked[-size:]
        if len(verb) < 2 or "".join(c for c, _ in pronoun) not in book_words("damir_muttasil", "on_verbs"):
            continue
        # اُكْتُبِيهِ، اُكْتُبُوهُ: a doer written as a long letter ends the verb on the vowel before it, and
        # the plural's alef, written only at the word's end, comes back (plural_alef)
        voweled = verb[-1][1] or _LENGTHENS.get(verb[-1][0]) in verb[-2][1]
        if not voweled or not (found := reading_of(plural_alef(_spell(verb)), known)):
            continue
        person = _ENCLITIC.get("".join(c for c, _ in pronoun)) or _ENCLITIC["كِ" if "ِ" in pronoun[-1][1] else "كَ"]
        joined = found.get("catib6", "").count("PRT")  # فَاهْدِنَا: the فَ the table read the verb behind
        return {**found, **_pieces(verb[:joined], verb[joined:], pronoun), "enc0": f"{person}_dobj"}
    return None


def _cuts(word: str):
    """(the letters written onto its front, the rest, the table's closest cells for the rest), fewest
    joined letters (وَ، فَ، لْ) first; only the vowels typed are evidence, so a bare word yields none."""
    marked = letters(word)
    for cut in range(min(len(marked), _JOINED_MOST) + 1):
        front, rest = marked[:cut], marked[cut:]
        if not all(letter in _joined() for letter, _ in front) or not _voweled(rest):
            continue
        found = dict(_scored(_spell(rest)))
        if found:
            yield front, rest, [cell for cell, score in found.items() if score == min(found.values())]


def _pieces(front: list, verb: list, pronoun: list = ()) -> dict:
    """The dictionary's split of a verb the table read (atbtok, catib6, ud): each joined letter a
    particle (فَ+، وَ+ a conjunction, لْ+ of the command), the verb, its object pronoun (فَ+_اقْبَلْ_+هَا)."""
    return {"atbtok": "_".join([*(_spell([p]) + "+" for p in front), _spell(verb), *(["+" + _spell(pronoun)] if pronoun else [])]),
            "catib6": "+".join(["PRT"] * len(front) + ["VRB"] + ["NOM"] * bool(pronoun)),
            "ud": "+".join([*(_PROCLITIC[letter] for letter, _ in front), "VERB", *(["PRON"] if pronoun else [])])}


# CAMeL's name for each object pronoun, by its letters and, for ك, its vowel
_ENCLITIC = {"ني": "1s", "نا": "1p", "كَ": "2ms", "كِ": "2fs", "كما": "2d", "كم": "2mp", "كن": "2fp",
             "ه": "3ms", "ها": "3fs", "هما": "3d", "هم": "3mp", "هن": "3fp"}

# the UD tag of each letter joined to a verb's front (_joined)
_PROCLITIC = {"و": "CCONJ", "ف": "CCONJ", "ل": "PART"}

# a verb takes at most two letters in front: وَ or فَ, then لْ
_JOINED_MOST = 2


@lru_cache(maxsize=1)
def _joined() -> set[str]:
    """The one-letter words that are written onto the front of a verb: the conjunctions and the jazm particle."""
    return {w for family in ("atf", "jazm") for w in book_words(family) if len(w) == 1}


def _spell(marked: list[tuple[str, set]]) -> str:
    return "".join(letter + "".join(sorted(marks)) for letter, marks in marked)
