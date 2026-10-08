"""Which of our hadith a unit of a ruling book is about. Pure: no I/O.

c1 reads the unit's matn: each of our hadith scores the summed rarity, log(N / df), of the word 3-grams it shares with
it, a 3-gram in more than `df_max` of our hadith being too common to count. c2 then asks that the unit's chain name a
man our hadith's chain names too, so the same words in another hadith's chain are not taken for it. A hadith in
several collections is the same hadith: every one within `tie_ratio` of the best score gets the ruling.
The knobs are usul.json `rulings.match`; what a quote says is ruling.py's.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Callable, Hashable, Iterable, Mapping, Sequence

from backend.services.hadith import chain
from backend.services.hadith.words import ARABIC_WORD
from backend.services.spelling import fold
from backend.services.usul import names


def tokens(text: str) -> list[str]:
    """The words of `text` as the hadith index spells them: folded, two letters or more."""
    return ARABIC_WORD.findall(fold(text))


def grams(words: Sequence[str], size: int) -> set[str]:
    """Every run of `size` words, each as the words joined by a space."""
    return {" ".join(words[i:i + size]) for i in range(len(words) - size + 1)}


class Index:
    """Our hadith by the word n-grams in their matn, built once."""

    def __init__(self, docs: Mapping[Hashable, Sequence[str]], size: int, wanted: set[str] | None = None):
        """docs: {hadith: its matn words}. wanted: only these n-grams are filed (the ones the units hold)."""
        self.size, self.total = size, len(docs)
        self._posting: dict[str, list[Hashable]] = defaultdict(list)
        for key, words in docs.items():
            for gram in grams(words, size):
                if wanted is None or gram in wanted:
                    self._posting[gram].append(key)

    def scores(self, words: Sequence[str], df_max: int) -> dict[Hashable, float]:
        """{hadith: summed rarity of the n-grams it shares with `words`}, n-grams in over df_max hadith left out."""
        found: dict[Hashable, float] = defaultdict(float)
        for gram in grams(words, self.size):
            holders = self._posting.get(gram, ())
            if holders and len(holders) <= df_max:
                rarity = math.log(self.total / len(holders))
                for key in holders:
                    found[key] += rarity
        return dict(found)

    def possible(self, words: Sequence[str], df_max: int) -> float:
        """The most `scores` could give `words`: a hadith holding every n-gram that counts."""
        return sum(math.log(self.total / len(holders)) for gram in grams(words, self.size)
                   if (holders := self._posting.get(gram)) and len(holders) <= df_max)


def split_hadith(head: str, kind_cfg: dict, quote: Sequence[str]) -> tuple[str, str]:
    """(the chain, the matn) of the hadith as a unit gives it ("" where the book does not give one).

    The book's `matn_after` mark (the editor's (ص) for the Prophet, in 'Ilal) ends the chain; failing that, the first
    quote (`quote` is the pattern that opens one and the one that closes it): the books quote the matn, and what
    follows the closing mark is theirs; failing that, the chain-word rule (hadith/chain.py)."""
    if mark := kind_cfg.get("matn_after"):
        found = re.search(mark, head)
        return (head[:found.start()], head[found.end():]) if found else ("", "")
    if start := kind_cfg.get("chain_start"):   # a section title comes first
        found = re.search(start, head)
        head = head[found.start():] if found else head
    if opened := re.search(quote[0], head):
        closed = re.search(quote[1], head[opened.end():])
        return head[:opened.start()], head[opened.end():opened.end() + closed.start()] if closed else head[opened.end():]
    chain_text, body = chain.chain_of(head)
    return (chain_text, body) if chain_text else ("", "")


def forms(row: dict) -> list[tuple[str, ...]]:
    """A narrator's name, lineage and kunyas as folded name words (names.words), the ways a book may call him."""
    kunyas = [k for k in re.split(r"\s*،\s*", row["kunya_ar"]) if k.strip()]
    return [f for f in (names.words(row["name_ar"]), names.words(row["lineage_ar"]), *map(names.words, kunyas)) if f]


class Names:
    """Whether a unit's chain names a man a hadith's chain names (c2)."""

    def __init__(self, narrators: Iterable[Sequence[tuple[str, ...]]], min_words: int, rare: int, stop: Iterable[str],
                 max_run: int):
        """narrators: each narrator's forms. A run of `min_words` name words in common is a shared man; so is one
        word that no more than `rare` narrators carry. Runs are compared up to `max_run` words."""
        self.min_words, self.rare, self.stop, self.max_run = min_words, rare, frozenset(names.word(s) for s in stop), max_run
        self.carriers: Counter = Counter()
        for narrator_forms in narrators:
            self.carriers.update({w for f in narrator_forms for w in f if w not in self.stop})

    def _runs(self, words: Sequence[str]) -> set[tuple[str, ...]]:
        return {tuple(words[i:i + n]) for n in range(1, self.max_run + 1) for i in range(len(words) - n + 1)}

    def evidence(self, unit: Sequence[str], ours: Iterable[Sequence[str]]) -> tuple[int, int]:
        """(the most name words one run has in common between the unit's chain and `ours` (name forms), the fewest
        narrators carrying a single word they share): how much the two chains have in common."""
        mine = self._runs(unit)
        longest, rarest = 0, 10 ** 9
        for form in ours:
            for run in self._runs(form) & mine:
                real = [w for w in run if w not in self.stop]
                longest = max(longest, len(real))
                if len(real) == 1:
                    rarest = min(rarest, self.carriers[real[0]])
        return longest, rarest

    def shares(self, unit: Sequence[str], ours: Iterable[Sequence[str]]) -> bool:
        """True when the chains share a run of `min_words` name words, or one word few narrators carry."""
        longest, rarest = self.evidence(unit, ours)
        return longest >= self.min_words or rarest <= self.rare


def choose(scores: Mapping[Hashable, float], possible: float, passes: Callable[[Hashable], bool], knobs: Mapping
           ) -> tuple[list[tuple[Hashable, float]], str]:
    """(the hadith that get the ruling with their scores, how the unit fared).

    A candidate needs `floor`, or `whole_floor` when it holds `whole` of all that `possible` allows (the unit's whole
    matn is in it, so a short matn can match). It must also be within `tie_ratio` of the best score overall and pass c2.
    How the unit fared: "matched", "below_floor" (no candidate has enough) or "rejected" (some do, none passes c2)."""
    def enough(score: float) -> bool:
        return score >= knobs["floor"] or (score >= knobs["whole_floor"] and score >= knobs["whole"] * possible)
    top = max(scores.values(), default=0)
    near = [(key, score) for key, score in scores.items() if enough(score) and score >= top * knobs["tie_ratio"]]
    if not near:
        return [], "below_floor"
    chosen = sorted(((key, score) for key, score in near if passes(key)), key=lambda pair: -pair[1])
    return chosen, "matched" if chosen else "rejected"
