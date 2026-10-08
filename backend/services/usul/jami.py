"""Read an entry of al-'Ala'i's Jami' al-Tahsil: who a narrator is said not to have heard from. Pure: no I/O.

An entry names a narrator and quotes what scholars said of his links. Only the
forms usul.json lists are read:

    لم يسمع من X     لم يدرك X     لم يلق X     عن X ... مرسل

X is found among the narrator's own known teachers or not at all: its words
must be the start of exactly one teacher's name, lineage or kunya (the longest
run of words that is). A statement whose X is a pronoun (منه), a relation
(أبيه) or a name that opens two teachers is returned unjoined with why, never
guessed at. The scholar is the one the entry names in the same clause.
"""
from __future__ import annotations

from collections import Counter
from typing import NamedTuple

from backend.services.usul import names
from backend.services.usul.books import Entry
from backend.services.usul.level import fold_word

Teachers = list[tuple[int, tuple[tuple[str, ...], ...]]]   # (narrator id, his name, lineage and kunyas as words)


class Statement(NamedTuple):
    kind: str
    quote: str
    scholar: str
    teacher: int | None
    why: str            # "" when joined; otherwise none (no teacher begins with X), many, longer (X goes on past a teacher's name) or unnamed (X is no name)


def _find(rest: list[str], teachers: Teachers, cfg: dict, vocab: frozenset[str]) -> tuple[int, int | None, str]:
    """(how many words X takes, the teacher it names, why not) from the words after a verb.

    X is the longest run of words that begins one of the narrator's teachers' names. It stands for him only if the
    run is the whole name, or the word after it is no word of any narrator's name (`vocab`): "جابر بن سمرة" does not
    name a teacher called "جابر بن عبد الله"."""
    for k in range(min(len(rest), cfg["name_words_max"]), 0, -1):
        hits = {who: [f for f in forms if f[:k] == tuple(rest[:k])] for who, forms in teachers}
        hits = {who: forms for who, forms in hits.items() if forms}
        if hits:
            if k == 1 and rest[0] in cfg["lone"]:
                return 1, None, "unnamed"
            if len(hits) > 1:
                return k, None, "many"
            (who, forms), = hits.items()
            if k < len(rest) and rest[k] in vocab and not any(len(f) == k for f in forms):
                return k, None, "longer"
            return k, who, ""
    return 1, None, "none"


def statements(text: str, teachers: Teachers, cfg: dict, vocab: frozenset[str] = frozenset()) -> list[Statement]:
    """Every statement of the forms cfg lists in one entry's text, in order. cfg is usul.json's `jami`; `vocab` the
    words narrators' names are written with."""
    shown = [t for t in text.split() if names.word(t)]
    plain = [fold_word(t) for t in shown]
    ident = [names.word(t) for t in shown]
    lone = {names.word(w) for w in cfg["lone"]}
    cfg = {**cfg, "lone": lone}
    says = {fold_word(w) for w in cfg["scholar"]["says"]}
    qualified = {fold_word(w) for w in cfg["qualified"]}   # "لم يسمع من جابر إلا أربعة أحاديث" is not a plain no
    after_stop = {fold_word(w) for w in cfg["scholar"]["after_stop"]}
    out: list[Statement] = []

    named = {w for w in ident[:next((i for i, t in enumerate(plain) if t.lstrip("و") in says), len(plain))]
             if w not in lone}   # the words of the man the entry is about, up to the first "قال"

    def scholar_of(start: int, end: int) -> tuple[str, int]:
        """(the scholar named in the clause, where the clause begins). Words between "قال" and the statement are the
        scholar only if none is a word of the man's own name ("قال الدارقطني عبد الكريم لم يدرك" cannot be split), all
        are words narrators' names are written with ("قال فيه الترمذي" is not), and the statement follows them
        directly, without a "و"."""
        said = next((i for i in range(start - 1, max(start - cfg["scholar"]["before_max"] - 2, -1), -1)
                     if plain[i].lstrip("و") in says), None)
        if said is not None and start > said + 1:
            # "قال أبو حاتم لم يسمع": the statement is what he said. "قال أبو حاتم رأى فلانا ولم يسمع": it is not.
            between = ident[said + 1:start]
            a_name = not vocab or all(w in vocab or w[1:] in vocab for w in between)   # a scholar is written with name words only
            return ("" if named & set(between) or plain[start].startswith("و") or not a_name else " ".join(shown[said + 1:start])), said
        after = cfg["scholar"]["after"]
        if end < len(shown) and plain[end] in {fold_word(w) for w in after}:
            tail = []
            for token in shown[end + 1:end + 1 + cfg["scholar"]["after_max"]]:
                if fold_word(token) in after_stop:
                    break
                tail.append(token)
            return " ".join(tail), start
        return "", start

    def add(kind: str, start: int, at: int, found: tuple[int, int | None, str], reach: int = 0) -> None:
        """A statement of `kind` beginning at word `start`, its X (`found`, from _find) at `at`; the quote runs to the
        end of X or to word `reach` if that is later."""
        used, teacher, why = found
        end = max(at + used, reach)
        if end < len(plain) and plain[end] in qualified:
            why = why or "qualified"
        scholar, begin = scholar_of(start, end)
        out.append(Statement(kind, " ".join(shown[begin:end]), scholar, teacher, why))

    for form in cfg["statements"]:
        pattern = [fold_word(w) for w in form["words"].split()]
        for i in range(len(plain) - len(pattern) + 1):
            if [plain[i + n].lstrip("و") if n == 0 else plain[i + n] for n in range(len(pattern))] == pattern:
                at = i + len(pattern)
                add(form["kind"], i, at, _find(ident[at:], teachers, cfg, vocab))
    mursal = cfg["mursal"]
    word, stops = fold_word(mursal["word"]), says | {fold_word(mursal["from"])}
    for i, token in enumerate(plain):
        if token == fold_word(mursal["from"]):
            found = _find(ident[i + 1:], teachers, cfg, vocab)
            after = plain[i + 1 + found[0]:i + 2 + found[0] + mursal["between"]]
            if word in after and not stops & set(after[:after.index(word)]):
                add("mursal", i, i + 1, found, reach=i + 1 + found[0] + after.index(word) + 1)
    return out


def join(entries: dict[int, Entry], people: list[names.Person], size: int, window: int) -> tuple[dict[int, int], dict[int, str]]:
    """({entry key: narrator id}, {entry key: why not}): the man the entry opens with, by names.Index.opened.
    Two entries may be about one man (a repeat), so a narrator need not be unique to an entry."""
    index = names.Index(people, size)
    return names.one_to_one({key: [p.id for p in index.opened(names.words(entry.text), window)] for key, entry in entries.items()},
                            exclusive=False)


class Pair(NamedTuple):
    student: int        # the narrator the entry is about, who is said not to have heard
    teacher: int
    kind: str
    quote: str
    scholar: str
    page: str           # where the statement is printed (Entry.where)


def pairs(items: list[tuple[int, Entry, Teachers]], cfg: dict, vocab: frozenset[str] = frozenset()) -> tuple[list[Pair], Counter]:
    """(the pairs the entries state, how many statements were left out by (kind, why)).

    `items` are (the entry's narrator, the entry, that narrator's known teachers). The same statement twice (an entry
    the book repeats, or two narrators' entries quoting alike) is one pair."""
    found: dict[tuple, Pair] = {}
    left: Counter = Counter()
    for who, entry, teachers in items:
        for said in statements(entry.text, teachers, cfg, vocab):
            if said.why or said.teacher == who:
                left[said.kind, said.why or "self"] += 1
                continue
            at = max(entry.text.find(" ".join(said.quote.split()[:4])), 0)
            found.setdefault((who, said.teacher, said.kind, said.quote),
                             Pair(who, said.teacher, said.kind, said.quote, said.scholar, entry.where(at)))
    return list(found.values()), left
