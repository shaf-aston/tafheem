"""Where a search looks: one hadith by number ("muslim 8", "Sahih al-Bukhari 1379",
"muslim:157c", "البخاري ١"), a whole collection ("bukhari"), or collections to
search within ("fasting in bukhari").

A collection is named by a run of typed words that are all its own words (its
id, short, full and Arabic names as the database stores them, so a new
collection needs no change here) and hold one whole name: "sahih bukhari"
names Bukhari, "dawud" alone does not name Abu Dawud. A word may be a slip or
two off (spelling.slips), as the word search allows, and an Arabic one may drop
its ال. Words two collections both claim name neither ("sahih 8" stays a word
search). A run of everyday words ("muslim") names a collection only alone or
with a number, since "rights of a muslim" is about Muslims; a word is everyday
when the hadith use it often (`hadith_name_common_share`, measured by `share`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from backend.config import get_settings
from backend.services.hadith.words import ARABIC_WORD, ENGLISH_WORD, MAX_NUMBER, without_article
from backend.services.spelling import fold, slips

# What parts the typed words: "bukhari:2", "Sahih al-Bukhari", "prayer, bukhari".
_PARTS = re.compile(r"[\s:/#,;.!?()\[\]\"\-،؛؟]+")
# A hadith number, with the letter of a part (157c).
_NUMBER = re.compile(r"(\d+)([a-z]?)")


@dataclass(frozen=True)
class Asked:
    collections: tuple[str, ...] = ()
    # Set when the search names one hadith; with no number and no words left, it names the whole collection.
    number: int | None = None
    part: str = ""
    # The words left to search for, collection names taken out.
    rest: str = ""


def read(query: str, collections: list[tuple[str, str, str, str, str, bool]], share: Callable[[str], float]) -> Asked:
    """What `query` names among `collections` (loader.collections rows), and what is left to search for."""
    common = get_settings().hadith_name_common_share
    tokens = [t for t in _PARTS.split(query) if t]
    bare = [_name_word(t) for t in tokens]
    claims = [(cid, run) for cid, *names, _ in collections for run in _naming(bare, (cid, *names))]
    claimed = [i for _, run in claims for i in run]
    claims = [(cid, run) for cid, run in claims if all(claimed.count(i) == 1 for i in run)]

    def left(kept) -> list[str]:
        taken = {i for _, run in kept for i in run}
        return [t for i, t in enumerate(tokens) if i not in taken]

    def at_most_a_number(rest: list[str]) -> bool:
        return len(rest) <= 1 and all(map(_number, rest))

    if not at_most_a_number(left(claims)):
        claims = [(cid, run) for cid, run in claims if not all(share(bare[i]) >= common for i in run)]
    named = tuple(dict.fromkeys(cid for cid, _ in claims))
    rest = left(claims)
    if len(named) == 1 and at_most_a_number(rest):
        number = _number(rest[0]) if rest else None
        return Asked(named, int(number[1]) if number else None, number[2] if number else "")
    if not named or not rest:
        # Naming nothing, or only several collections with nothing to search within them: all words.
        return Asked(rest=query)
    return Asked(named, rest=" ".join(rest))


def _naming(bare: list[str], names: tuple[str, ...]) -> list[list[int]]:
    """The runs of typed words (by position) that name the collection called `names`."""
    wholes = [w for w in map(_words, names) if w]
    known = set().union(*wholes)
    runs, run = [], []
    for i, word in enumerate([*bare, ""]):
        if word and any(_near(word, k) for k in known):
            run.append(i)
        elif run:
            runs.append(run)
            run = []
    return [run for run in runs if any(all(any(_near(bare[i], k) for i in run) for k in whole) for whole in wholes)]


def _number(token: str) -> re.Match | None:
    """A hadith number (with its part letter), or None; one larger than any hadith is no number."""
    match = _NUMBER.fullmatch(token.lower())
    return match if match and int(match[1]) < MAX_NUMBER else None


def _near(word: str, known: str) -> bool:
    return slips(word, known) <= int(len(known) * get_settings().spelling_edits_per_letter)


def _name_word(word: str) -> str:
    return without_article(fold(word.replace("'", "")))


def _words(name: str) -> set[str]:
    """A name's words, split and spelt as typed words are."""
    return {w for w in map(_name_word, _PARTS.split(name)) if ARABIC_WORD.fullmatch(w) or ENGLISH_WORD.fullmatch(w)}
