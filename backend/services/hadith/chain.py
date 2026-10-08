"""The Arabic of a hadith as two parts: the chain of narrators, and the hadith it carries.

A port of chainOf in frontend/src/lib/hadithWords.js, reading the same rule from
frontend/src/hadith.json (key `chain`), so the app hides the chain and the index
leaves it out by one definition. Pure but for that one read.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_RULE = json.loads((Path(__file__).resolve().parents[3] / "frontend" / "src" / "hadith.json")
                   .read_text(encoding="utf-8"))["chain"]
_LINKS = {*_RULE["links"]["words"],
          *(verb + ending for verb in _RULE["links"]["verbs"] for ending in _RULE["links"]["endings"])}
_SAYS = set(_RULE["says"])
_ABOUT = set(_RULE["about"])
_FREE = set(_RULE["free"])
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


def _bare(word: str) -> str:
    plain = _NOT_LETTER.sub("", word)
    unjoined = plain[1:] if plain[:1] in "\u0648\u0641" and plain else ""
    return unjoined if unjoined in _LINKS or unjoined in _SAYS else plain


def term_of(word: str) -> dict | None:
    """The guide's entry for one chain word as written (its `way`, `arabic`, `match`), or None."""
    plain = _bare(word)
    return _TERMS.get(next((stem for stem in _STEMS if plain.startswith(stem)), plain))


def passed_on(gap: str) -> tuple[str, str]:
    """(the word that passed the hadith on, "") from the text between two narrators the chain names, as it is written.

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
    shown = _SHOWN.sub("", last)
    # An attached wa or fa is not part of the word it joins.
    return (_ATTACHED.sub("", shown) if _bare(last) != _NOT_LETTER.sub("", last) else shown), ""


def _outside_asides(words: list, marks: list[bool]) -> list:
    """The words not set between a pair of aside marks; a mark with no partner is ignored."""
    at = [i for i, mark in enumerate(marks) if mark]
    inside = {i for start, end in zip(at[::2], at[1::2]) for i in range(start, end + 1)}
    return [w for i, w in enumerate(words) if i not in inside]


def chain_of(arabic: str | None) -> tuple[str, str]:
    """(chain, body). Where the end of the chain is not plain: ("", the whole text)."""
    text = arabic or ""
    whole = ("", text)
    words = [(m.start(), _bare(m.group()), bool(_QUOTED.search(m.group())), bool(_STOP.search(m.group())))
             for m in re.finditer(r"\S+", text)]
    words = _outside_asides(words, [m.group() == _RULE["aside"] for m in re.finditer(r"\S+", text)])
    words = [w for w in words if w[1] or w[2] or w[3]]
    if not words or words[0][1] not in _LINKS:
        return whole

    i = 1
    while i < len(words):
        name = 0
        ended = False   # past a full stop only a link or a saying word may come
        while i < len(words) and words[i][1] not in _LINKS and words[i][1] not in _SAYS:
            _, word, quoted, stop = words[i]
            if quoted or word in _ABOUT or (ended and word):
                return whole
            if word and word not in _FREE:
                name += 1
                if name > _RULE["name"]:
                    return whole
            ended = ended or stop
            i += 1
        if i == len(words):
            return whole
        if words[i][1] in _LINKS:
            i += 1
            continue
        while i + 1 < len(words) and words[i + 1][1] in _SAYS:
            i += 1
        if i + 1 < len(words) and words[i + 1][1] in _LINKS:
            i += 2
            continue
        return text[:words[i][0]].strip(), text[words[i][0]:]
    return whole
