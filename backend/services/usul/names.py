"""A name as words, and the one rule that joins a name written in a book to a narrator. Pure: no I/O.

The books and sunnah.com write the same man a little differently (الحسين and
حسين, سيئ and سيء), so every name is folded the way a grade is (level.fold_word)
and its article is dropped. A name written in a book joins a narrator when its
first `size` words equal the first `size` words of his lineage or of his name
(books write him either way: حبيب بن أبي ثابت is حبيب بن قيس) and, where `window` is given, a nisba of his stands among
the next `window` words. It is a join only when it is one-to-one: one narrator
for the name and one name for the narrator. Anything else goes to the gap table.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Hashable, NamedTuple

from backend.services.hadith.chain import SPELLINGS
from backend.services.usul.level import fold_word
from backend.services.usul.rule import rule

_SPLIT = re.compile(r"[\s،,]+")
_SPELLINGS = {fold_word(was): fold_word(now) for was, now in SPELLINGS.items()}
# Words that begin a compound name (usul.json `join.bound`): عبد (عبد الله), the kunya's أبو and أم.
_BOUND = {fold_word(w) for w in rule()["join"]["bound"]}


def word(token: str) -> str:
    """One name word, folded, with أبا and أبي as أبو, ابن as بن, and the article off; "" where nothing is left."""
    folded = fold_word(token)
    if folded.startswith("ال") and len(folded) > 4:
        folded = folded[2:]
    return _SPELLINGS.get(folded, folded)


def flat(text: str) -> tuple[str, ...]:
    """The name's words one by one, عبد and الله apart: how running text is read word by word (services/usul/jami)."""
    return tuple(w for w in map(word, _SPLIT.split(text)) if w)


def words(text: str) -> tuple[str, ...]:
    """The name's words: الحسين بن علي is (حسين, بن, علي). A word that only means something with the next one stays
    with it (عبد الله, أبو بكر, أم سلمة), so the first three words of محمد بن عبد الله and محمد بن عبد الرحمن differ."""
    out: list[str] = []
    for token in map(word, _SPLIT.split(text)):
        if not token:
            continue
        if out and out[-1] in _BOUND and " " not in out[-1]:
            out[-1] = f"{out[-1]} {token}"
        else:
            out.append(token)
    return tuple(out)


class Person(NamedTuple):
    """A narrator as the joins see him: `keys` are his lineage words and his name's."""
    id: int
    keys: tuple[tuple[str, ...], ...]
    nisba: frozenset[str]
    names: tuple[tuple[str, ...], ...]   # his name, lineage and each kunya, word by word (flat)
    generation: str
    grade: tuple[str, ...]


def person(row: dict) -> Person:
    """A narrator row of rijal.db as a Person."""
    kunyas = [k for k in re.split(r"\s*،\s*", row["kunya_ar"]) if k.strip()]
    return Person(
        id=row["id"], keys=tuple(dict.fromkeys(w for w in (words(row["lineage_ar"]), words(row["name_ar"])) if w)), nisba=frozenset(words(row["nisba_ar"])),
        names=tuple(w for w in (flat(row["name_ar"]), flat(row["lineage_ar"]), *map(flat, kunyas)) if w),
        generation=row["generation_ar"], grade=words(row["grade_ar"]),
    )


class Index:
    """The narrators by the first `size` words of each of their keys."""

    def __init__(self, people: list[Person], size: int):
        self.size = size
        self._by_key: dict[tuple[str, ...], list[Person]] = defaultdict(list)
        for p in people:
            for head in {k[:size] for k in p.keys if len(k) >= size}:
                self._by_key[head].append(p)

    def named(self, written: tuple[str, ...], window: int = 0) -> list[Person]:
        """Narrators the written name matches: its first `size` words equal theirs and, with a `window`, a nisba of
        theirs stands among the words after those. None where it is shorter than `size`."""
        if len(written) < self.size:
            return []
        found = self._by_key.get(written[:self.size], [])
        if not window:
            return list(found)
        near = set(written[self.size:self.size + window])
        return [p for p in found if p.nisba & near]

    def headed(self, written: tuple[str, ...], window: int) -> list[Person]:
        """Narrators a heading names: its key, and where it goes on past the key, a nisba of his among those words
        too (إبراهيم بن العباس السامري is not the one whose nisba is الحجازي)."""
        return self.named(written, window) if len(written) > self.size else self.named(written)

    def opened(self, written: tuple[str, ...], window: int) -> list[Person]:
        """Narrators running text opens with: its key and, only where the key is shared, a nisba of his among the
        words after it. The text goes on past his name, so a name with no nisba is not held against him."""
        found = self.named(written)
        return found if len(found) < 2 else self.named(written, window)


def one_to_one(matches: dict[Hashable, list[int]], exclusive: bool = True) -> tuple[dict[Hashable, int], dict[Hashable, str]]:
    """({entry: narrator id} where the entry has one narrator and, if `exclusive`, he has one entry, {entry: why not}).

    why is "none" for an entry nobody matched, "many" for one that matched several narrators, and "shared"
    for one whose narrator another entry matched too."""
    claimed: dict[int, int] = defaultdict(int)
    for ids in matches.values():
        for who in set(ids):
            claimed[who] += 1
    joined: dict[Hashable, int] = {}
    why: dict[Hashable, str] = {}
    for entry, ids in matches.items():
        unique = set(ids)
        if not unique:
            why[entry] = "none"
        elif len(unique) > 1:
            why[entry] = "many"
        elif exclusive and claimed[next(iter(unique))] > 1:
            why[entry] = "shared"
        else:
            joined[entry] = next(iter(unique))
    return joined, why
