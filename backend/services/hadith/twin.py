"""Which hadith of the six a further book's hadith is, so it can show the grade its twin carries. Pure: no I/O.

A book like Mishkat ends each hadith naming who recorded it ("رواه الترمذي والنسائي"). That line says which books
to look in; the matn then finds the twin there with the same matcher the ruling books use (usul/match.py, knobs in
usul.json `rulings.match`). A hadith whose line names none of the six, or whose matn no named book holds closely
enough, has no twin and so no grade: it is never guessed.
"""
from __future__ import annotations

from typing import Iterable, Mapping

from backend.services.hadith.usul import match
from backend.services.text.spelling import fold

Key = tuple[str, int, str]  # (collection, number, part)


def _bare(word: str) -> str:
    """A word of the closing line without its "and" (و) and "the" (ال): والترمذي as ترمذي."""
    word = word[1:] if word.startswith("و") and len(word) > 3 else word
    return word[2:] if word.startswith("ال") and len(word) > 3 else word


def recorders(arabic: str, forms: Mapping[str, list[str]], line: Mapping) -> list[str]:
    """The collections the closing line of `arabic` names.

    forms: each collection's spellings in that line. line: `words` (how many of the text's last words the line can
    span), `cue` (the words that open it, رواه or متفق), `agreed_upon` (the collections متفق عليه names). Words
    before the first cue word are matn, never read as a recorder (حق المسلم)."""
    cues = tuple(fold(c) for c in line["cue"])
    words = match.tokens(arabic)[-line["words"]:]
    opens = [i for i, w in enumerate(words) if w.lstrip("و").startswith(cues)]
    if not opens:
        return []
    tail = [_bare(w) for w in words[opens[0]:]]
    found = [c for c, spellings in forms.items() if any(_bare(s) in tail for f in spellings for s in match.tokens(f))]
    if any(w.startswith(fold("متفق")) for w in tail):
        found += [c for c in line["agreed_upon"] if c not in found]
    return found


def twins(arabic: str, recorded: Iterable[str], indexes: Mapping[str, match.Index], knobs: Mapping) -> list[Key]:
    """The best hadith of each `recorded` collection that `arabic` is, if any holds it closely enough.

    indexes: each collection's matn n-grams (match.Index). knobs: usul.json `rulings.match`."""
    words = match.tokens(arabic)
    found: list[tuple[Key, float]] = []
    for collection in recorded:
        index = indexes[collection]
        chosen, _ = match.choose(index.scores(words, knobs["df_max"]), index.possible(words, knobs["df_max"]),
                                 lambda key: True, knobs)
        found += chosen[:1]
    return [key for key, _ in sorted(found, key=lambda pair: -pair[1])]


def borrowed(keys: Iterable[Key], grades_of: Mapping[Key, list[dict]], books: Mapping[str, Mapping]) -> list[dict]:
    """The grades the twins `keys` carry, each marked with the twin it comes from ("of": "Tirmidhi 1655").

    A twin in a Sahih collection (books[c]["sahih"]) has no grades of its own: that collection grades it Sahih.
    books: collections.json."""
    out: list[dict] = []
    for collection, number, part in keys:
        meta = books[collection]
        own = [{"by": meta["name"], "grade": "Sahih"}] if meta.get("sahih") else grades_of[collection, number, part]
        out += [{**g, "of": f"{meta['short']} {number}{part}"} for g in own]
    return out
