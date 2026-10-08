"""Read an entry of Ibn Hajar's Taqrib al-Tahdhib, and join it to a narrator. Pure: no I/O.

An entry runs: the name chain, Ibn Hajar's grade wording, "من الثالثة" (the
generation), "مات سنة ..." (the death year) and the signs of the books that
carry him. The preface says how to read the year: a man of the first two
generations died before the 100th year, the third to the eighth after it, the
ninth on after the 200th, and one who falls outside is given with his hundreds
written out (data/usul/usul.json `taqrib`).

A narrator joins an entry only when his name, generation and grade all agree
and each is the other's only match (names.one_to_one). Any entry or narrator
left over is listed with why, never guessed at.
"""
from __future__ import annotations

import re
from typing import NamedTuple

from backend.services.usul import names
from backend.services.usul.level import fold_word

# The words a year is written in. Folded like everything else, so the spelling is the book's.
_UNITS = {
    1: "واحد احد احدى واحدة", 2: "اثنين اثنتين اثنان اثنتان اثنا اثنتا اثني اثنتي ثنتين ثنتان ثنتي", 3: "ثلاث ثلاثة",
    4: "أربع أربعة", 5: "خمس خمسة", 6: "ست ستة", 7: "سبع سبعة", 8: "ثمان ثماني ثمانية", 9: "تسع تسعة",
}
_TENS = {
    20: "عشرين عشرون", 30: "ثلاثين ثلاثون", 40: "أربعين أربعون", 50: "خمسين خمسون", 60: "ستين ستون",
    70: "سبعين سبعون", 80: "ثمانين ثمانون", 90: "تسعين تسعون",
}
_TEN = "عشر عشرة"
_HUNDREDS = {
    100: "مائة مئة", 200: "مائتين مائتان مئتين مئتان", 300: "ثلاثمائة", 400: "أربعمائة", 500: "خمسمائة",
    600: "ستمائة", 700: "سبعمائة", 800: "ثمانمائة", 900: "تسعمائة",
}


def _table() -> dict[str, tuple[int, str]]:
    """{folded word: (value, class)} for every number word; class is unit, ten (the 10 of 13), tens or hundred."""
    out = {}
    for group, kind in ((_UNITS, "unit"), (_TENS, "tens"), (_HUNDREDS, "hundred")):
        for value, spelled in group.items():
            out.update({fold_word(w): (value, kind) for w in spelled.split()})
    out.update({fold_word(w): (10, "ten") for w in _TEN.split()})
    return out


_NUMBER = _table()
_WAW = "و"


def _number_word(token: str) -> tuple[int, str, bool] | None:
    """(value, class, joined by و) when the folded token is a number word, with or without a leading و."""
    if token in _NUMBER:
        return (*_NUMBER[token], False)
    if token.startswith(_WAW) and token[1:] in _NUMBER:
        return (*_NUMBER[token[1:]], True)
    return None


def number_words(tokens: list[str]) -> tuple[int, int] | None:
    """(the number the words add up to, how many tokens it took) from the start of folded `tokens`, None when it
    does not open with a number word or is not a number a person would write.

    Written: units and tens joined by و (تسع وعشرين), a unit with عشرة (ثلاث عشرة), hundreds last (ومائة).
    Two of one class, a word with no و that is not the عشرة of a teen, and the like are not read."""
    total, seen, last, took = 0, set(), "", 0
    for token in tokens:
        word = _number_word(token)
        if word is None:
            break
        value, kind, joined = word
        if (kind in seen or (last and not joined and not (kind == "ten" and last == "unit"))
                or {kind, last} == {"ten", "tens"}):
            return None
        seen.add(kind)
        total, last, took = total + value, kind, took + 1
    return (total, took) if took else None


def death_year(text: str, doubt: list[str] | tuple[str, ...] = ()) -> tuple[int | None, str]:
    """(the year as written, "") for the plain form "مات سنة <number words>"; (None, why) for anything else.

    why: no_clause (no such words), digits (the year is in figures), unreadable (words this does not read) or doubt
    (a word of `doubt`, like وقيل or أو, follows: the book itself is not sure)."""
    year, why, _ = _death(text.split(), doubt)
    return year, why


def _death(shown: list[str], doubt) -> tuple[int | None, str, tuple[int, int] | None]:
    """death_year over the entry's words, with the (first, last) word of the clause when it is read."""
    tokens = [fold_word(t) for t in shown]
    at = next((i for i in range(len(tokens) - 1) if tokens[i] == "مات" and tokens[i + 1] == "سنة"), None)
    if at is None:
        return None, "no_clause", None
    if re.fullmatch(r"\d+", shown[at + 2] if at + 2 < len(shown) else ""):
        return None, "digits", None
    read = number_words(tokens[at + 2:])
    if read is None:
        return None, "unreadable", None
    end = at + 2 + read[1]
    if end < len(tokens) and tokens[end] in {fold_word(d) for d in doubt}:
        return None, "doubt", None
    return read[0], "", (at, end - 1)


def hijri(year: int, generation: int, bands: list[dict]) -> int | None:
    """The year of the hijra: as written where it names its hundreds, else the hundreds the generation's band adds.
    None where the band has none to add (null): the year cannot be told from the first or the second century."""
    if year >= 100:
        return year
    add = next(b["add"] for b in bands if b["from"] <= generation <= b["to"])
    return None if add is None else year + add


class Parsed(NamedTuple):
    text: str
    generation: int | None
    before: tuple[str, ...]         # the words before "من <generation>", folded as names are: the name and the grade
    wording: str                    # the same words as the book prints them
    generation_quote: str           # "من الثالثة" as printed, "" with no generation
    death: int | None
    death_why: str
    death_quote: str                # "مات سنة ..." as printed, "" unless the year is read
    death_at: int                   # where that clause starts in `text`


def parse(text: str, cfg: dict) -> Parsed:
    """One entry's generation, the words before it and the death year as written. cfg is usul.json's `taqrib`."""
    spans = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]
    shown = [text[a:b] for a, b in spans]
    words = [fold_word(t) for t in shown]
    ordinals = sorted(((i + 1, tuple(fold_word(w) for w in name.split())) for i, name in enumerate(cfg["generations"])),
                      key=lambda o: -len(o[1]))
    died = next((i for i in range(len(words) - 1) if words[i] == "مات" and words[i + 1] == "سنة"), len(words))
    found = None
    for i in range(min(died, len(words) - 1)):   # the last "من <generation>" before the death clause
        if words[i] == "من":
            found = next(((number, i, len(ordinal)) for number, ordinal in ordinals
                          if tuple(words[i + 1:i + 1 + len(ordinal)]) == ordinal), found)
    year, why, clause = _death(shown, cfg["death"]["doubt"])
    generation, at, size = found if found else (None, len(words), 0)
    return Parsed(
        text, generation, names.words(" ".join(shown[:at])), " ".join(shown[:at]),
        text[spans[at][0]:spans[at + size][1]] if found else "", year, why,
        text[spans[clause[0]][0]:spans[clause[1]][1]] if clause else "", spans[clause[0]][0] if clause else 0)


def join(entries: dict[int, Parsed], people: list[names.Person], cfg: dict, size: int) -> tuple[dict[int, int], dict[int, str]]:
    """({entry n: narrator id}, {entry n: why not}) over every entry.

    A narrator is a candidate when the first `size` words of his lineage equal the entry's, his generation is the
    entry's, and the words just before "من <generation>" end with his grade (or he has none)."""
    index = names.Index(people, size)
    ordinal = {fold_word(name): i + 1 for i, name in enumerate(cfg["generations"])}
    matches: dict[int, list[int]] = {}
    why: dict[int, str] = {}
    for n, entry in entries.items():
        if entry.generation is None:
            why[n] = "no_generation"
            continue
        matches[n] = [
            p.id for p in index.named(names.words(entry.text))
            if ordinal.get(fold_word(p.generation)) == entry.generation
            and entry.before[len(entry.before) - len(p.grade):] == p.grade
        ]
    joined, gaps = names.one_to_one(matches)
    return joined, {**why, **gaps}
