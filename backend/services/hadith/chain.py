"""The Arabic of a hadith as parts: the chain of narrators, the one who tells it, and the hadith it carries.

The one cutter: the app, the index and the usul build all take the cut from chain_of, by the rule in
data/hadith/chain.json, which the page also builds in (lib/hadithWords.js). Pure but for that one read.
"""
from __future__ import annotations

import json
import re
from typing import NamedTuple

from backend.config import data_path

_RULE = json.loads((data_path("hadith_dir") / "chain.json").read_text(encoding="utf-8"))
# A passing-on verb with its ending (حدثه); only one hands a chain on past أن.
_VERBS = {verb + ending for verb in _RULE["links"]["verbs"] for ending in _RULE["links"]["endings"]}
_LINKS = {*_RULE["links"]["words"], *_VERBS}
_SAYS = set(_RULE["says"])
_ABOUT = set(_RULE["about"])
_FREE = set(_RULE["free"])
_PROPHET = set(_RULE["prophet"])
_KIN = set(_RULE["kin"])
_HANDS = set(_RULE["hands"])
# Two spellings of one word in a name (أبا, أبي and أبو), read as one when two names are matched.
SPELLINGS: dict[str, str] = _RULE["spellings"]
# The chain-words guide: each word it explains, by the stem a form of it starts with (حدثتني is حدث).
_TERMS = {m: {**term, "way": group["way"]} for group in _RULE["terms"]["groups"]
          for term in group["terms"] for m in term.get("match", [])}
_STEMS = sorted(_RULE["links"]["verbs"], key=len, reverse=True)
# Anything but a letter goes: vowels, tatweel, direction marks, commas, colons.
_NOT_LETTER = re.compile("[^\u0621-\u063A\u0641-\u064A\u0671]")
# A quote or a bracket is the hadith's own words or a verse, never a name.
_QUOTED = re.compile('["\u201c\u201d\u00ab\u00bb{}()]')
# A full stop ends a sentence; a name never runs on past one.
_STOP = re.compile("[.\u061f!]")
# The wa or fa joined to the front of a word, with its vowel.
_ATTACHED = re.compile("^[وف][ً-ٰٟ]*")
# A word as printed: its letters and vowels, with commas and direction marks gone.
_SHOWN = re.compile("[^\u0621-\u063a\u0641-\u065f\u0670\u0671]")


class Cut(NamedTuple):
    """chain: the text before the body. teller: from the latest teller's link up to the body. body: the hadith, from
    its saying word on. at: (teller_at, body_at), where teller and body start in the text. When the end of the chain
    is not plain: chain and teller are empty, body is the whole text and at is None."""
    chain: str
    teller: str
    body: str
    at: tuple[int, int] | None


class _Word(NamedTuple):
    at: int
    word: str
    quoted: bool
    stop: bool


def _bare(word: str) -> str:
    plain = _NOT_LETTER.sub("", word)
    unjoined = plain[1:] if plain[:1] in "\u0648\u0641" and plain else ""
    return unjoined if unjoined in _LINKS or unjoined in _SAYS else plain


def term_of(word: str) -> dict | None:
    """The guide's entry for one chain word as written (its `way`, `arabic`, `match`), or None."""
    plain = _bare(word)
    return _TERMS.get(next((stem for stem in _STEMS if plain.startswith(stem)), plain))


def passed_on(gap: str, then: str = "") -> tuple[str, str]:
    """(the word that passed the hadith on, "") from the text between two narrators the chain names, as it is written.
    `then` is the text after the upper narrator's name: a gap ending on a hands word (أن طاوسا أخبره) is passed on by
    the link that opens it, as chain_of reads it.

    ("", why) when there is no such rung: strand (a ح starts another strand there), unnamed (words that are neither a
    passing-on word, a saying word nor a blessing: a name left unplaced, say) or no_link (no passing-on or saying word)."""
    tokens = gap.split()
    bare = [_bare(t) for t in tokens]
    if _RULE["strand"] in bare:
        return "", "strand"
    if any(b and b != "و" and b not in _LINKS and b not in _SAYS and b not in _FREE for b in bare):
        return "", "unnamed"
    last = next((t for t, b in zip(reversed(tokens), reversed(bare)) if b in _LINKS or b in _SAYS), None)
    if last is None:
        return "", "no_link"
    if _bare(last) in _HANDS:
        opener = next((t for t in then.split() if _bare(t)), "")
        last = opener if _bare(opener) in _VERBS else last
    shown = _SHOWN.sub("", last)
    # An attached wa or fa is not part of the word it joins.
    return (_ATTACHED.sub("", shown) if _bare(last) != _NOT_LETTER.sub("", last) else shown), ""


def _outside_asides(words: list, marks: list[bool]) -> list:
    """The words not set between a pair of aside marks; a mark with no partner is ignored."""
    at = [i for i, mark in enumerate(marks) if mark]
    inside = {i for start, end in zip(at[::2], at[1::2]) for i in range(start, end + 1)}
    return [w for i, w in enumerate(words) if i not in inside]


def without_asides(text: str) -> str:
    """The text with each remark set between two aside marks (- يعنيان ابن علية -) gone."""
    words = text.split()
    return " ".join(_outside_asides(words, [w == _RULE["aside"] for w in words]))


def chain_of(arabic: str | None) -> Cut:
    """The text cut into chain, teller and body.

    The books do not mark where the chain ends, so it is walked, link by link: a passing-on word (حدثنا، عن) then a
    name, until a saying word (قال، أنها) that no further link follows. The body starts at that last saying word,
    so "قالت النساء" keeps its verb. A name past `name` words, running on past a full stop, or holding a quote, a
    bracket or the chain's note on itself (بهذا الإسناد), or a text that does not open with a link, means the end is
    not plain: the whole text comes back as the body, or the cut made before the latest hands word (أن طاوسا
    أخبره reads on; أن النبي نهى عن reads on and fails, so the cut at أن stands)."""
    text = arabic or ""
    whole = Cut("", "", text, None)
    tokens = list(re.finditer(r"\S+", text))
    words = [_Word(m.start(), _bare(m.group()), bool(_QUOTED.search(m.group())), bool(_STOP.search(m.group())))
             for m in _outside_asides(tokens, [m.group() == _RULE["aside"] for m in tokens])]
    words = [w for w in words if w.word or w.quoted or w.stop]
    if not words or words[0].word not in _LINKS:
        return whole

    last = 0   # the latest link: from it on is the one who tells the hadith

    def word(k: int) -> str | None:
        return words[k].word if k < len(words) else None

    # A kin word counts only standing alone: أبي ذر is a name, عن أبيه، قال is not.
    def alone(k: int) -> bool:
        return word(k + 1) is None or word(k + 1) in _LINKS or word(k + 1) in _SAYS

    # A link to the Prophet, to a kin word, or straight to a saying word (حدثه أنه) names no new teller.
    def before(k: int) -> bool:
        return word(k) in _PROPHET or (word(k) in _KIN and alone(k))

    def teller(k: int) -> int:
        return last if before(k + 1) or word(k + 1) in _SAYS else k

    # After a hands word (أن), a passing-on verb within one name: the narrator named before it hands the hadith on.
    # A bare link word is the hadith's own (أن النبي نهى عن), never this.
    def handed(k: int) -> int:
        if words[k].word not in _HANDS:
            return -1
        nxt = next((j for j in range(k + 1, len(words))
                    if words[j].word in _LINKS or words[j].word in _SAYS or words[j].quoted or words[j].stop), -1)
        return nxt if nxt > k + 1 and nxt - k - 1 <= _RULE["name"] and words[nxt].word in _VERBS else -1

    def cut(t: int, b: int) -> Cut:
        teller_at, body_at = words[t].at, words[b].at
        return Cut(text[:body_at].strip(), text[teller_at:body_at].strip(), text[body_at:], (teller_at, body_at))

    held = whole   # the plain cut before the latest hands word: where reading on from it fails, it stands
    i = 1
    while i < len(words):
        name = 0
        ended = False   # past a full stop only a link or a saying word may come
        while i < len(words) and words[i].word not in _LINKS and words[i].word not in _SAYS:
            if words[i].quoted or words[i].word in _ABOUT or (ended and words[i].word):
                return held
            if words[i].word and words[i].word not in _FREE:
                name += 1
                if name > _RULE["name"]:
                    return held
            ended = ended or words[i].stop
            i += 1
        if i == len(words):
            return held
        if words[i].word in _LINKS:
            last = teller(i)
            i += 1
            continue
        while i + 1 < len(words) and words[i + 1].word in _SAYS:
            i += 1
        if i + 1 < len(words) and words[i + 1].word in _LINKS:
            last = teller(i + 1)
            i += 2
            continue
        link = handed(i)
        if link > 0:
            held = cut(last, i)
            last = last if before(i + 1) else i
            i = link + 1
            continue
        return cut(last, i)
    return held


def cut_of(arabic: str | None) -> list[int] | None:
    """chain_of's `at` as the page reads it: [teller_at, body_at], or None where the cut is not plain."""
    at = chain_of(arabic).at
    return list(at) if at else None


def name_tokens(chain: str) -> list[str]:
    """The words of a chain that are not its passing-on or saying words, letters only: the names, run together."""
    return [plain for word in chain.split()
            if (plain := _NOT_LETTER.sub("", word)) and _bare(word) not in _LINKS | _SAYS]
