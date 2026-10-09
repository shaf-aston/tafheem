"""Read Ibn Hajar's Ta'rif Ahl al-Taqdis (the men described as mudallis, in five levels), and join it to narrators. Pure.

An entry begins with the signs of the books that carry the man (the same signs
as the Taqrib's, plus ه and ز which the Ta'rif adds), then his name and the
nisba words that tell him from others of the name, then what is said of his
tadlis. The level is the heading the entry stands under.

A narrator joins an entry by the Taqrib's name rule (names.Index) and, since the
Ta'rif gives no generation or grade to check, one of his nisba words must also
stand among the next `nisba_window` words, and all the lineage and nisba the entry
writes must be his (names.Index.written). Anything not one-to-one goes to the gap.
"""
from __future__ import annotations

from backend.services.usul import names
from backend.services.usul.books import Entry
from backend.services.usul.level import fold_word


def level_of(entry: Entry, cfg: dict) -> int | None:
    """1 to 5 from the heading the entry stands under (المرتبة الثالثة), None if it names none."""
    heading = tuple(fold_word(w) for w in entry.heading.split())
    return next((i + 1 for i, name in enumerate(cfg["levels"])
                 if heading[-len(name.split()):] == tuple(fold_word(w) for w in name.split())), None)


def written_name(entry: Entry, cfg: dict) -> tuple[str, ...]:
    """The entry's name words, the book signs before it taken off."""
    signs = {fold_word(s) for s in cfg["marks"]}
    shown = entry.text.split()
    while shown and fold_word(shown[0]) in signs:
        shown = shown[1:]
    return names.words(" ".join(shown))


def join(entries: dict[int, tuple[str, ...]], people: list[names.Person], size: int, window: int) -> tuple[dict[int, int], dict[int, str]]:
    """({entry key: narrator id}, {entry key: why not}) for entries given as their written name words."""
    index = names.Index(people, size)
    return names.one_to_one({key: [p.id for p in index.written(written, window)] for key, written in entries.items()})


def resolve(written: str, people: list[names.Person], size: int, window: int) -> int:
    """The one narrator a name written in usul.json stands for, by the same rule as the join. Stops, saying why, when
    it stands for none or for several: the name is then written more fully."""
    found = {p.id for p in names.Index(people, size).written(names.words(written), window)}
    if len(found) != 1:
        raise ValueError(f"the name {written!r} stands for {len(found)} narrators ({sorted(found)}); write it more fully")
    return found.pop()
