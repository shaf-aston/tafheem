"""A Maqayees entry cut into its words, each with the book's lines beside it.

Ibn Faris's entry runs as one paragraph: a word, what it means, a saying or
two that use it, the next word. A model reads the numbered lines and says which
lines belong to which word, what that word is, and what it means. This module
checks that answer against the book before anything keeps or shows it.

The Arabic is never the model's. Each sense names its lines by number, so the
book's own lines are what the card prints; the word and every example saying
must be found in those lines (the vowel marks aside, which a model drops), and
what is shown is the book's spelling of it, cut from the line. An answer whose
lines do not cover the entry in order is refused whole: English under the wrong
Arabic is a false claim about the book. A word or a saying that cannot be found
is dropped, never shown as the model wrote it.

Kept shape, one dict per sense: {"lines": [first, last], "word", "say",
"gloss", "examples": [{"line", "arabic", "say", "english"}]}, lines counted
from 0. `shown` turns it into what the card reads, with the Arabic lines in.
"""
from __future__ import annotations

from backend.services.text.arabic_text import DIACRITICS_RE


def find(text: str, phrase: str) -> str:
    """`phrase` as `text` spells it, matched with the vowel marks left out of
    both; "" when it is not there. A model writes الرطب for the book's
    الرَّطْبُ, and the card must print the book's."""
    bare_phrase = DIACRITICS_RE.sub("", phrase or "").strip()
    if not bare_phrase:
        return ""
    # Where each letter of the bare text sits in the marked one.
    at = [i for i, ch in enumerate(text) if not DIACRITICS_RE.match(ch)]
    bare = "".join(text[i] for i in at)
    start = bare.find(bare_phrase)
    if start < 0:
        return ""
    end = start + len(bare_phrase)
    # Up to the next letter, so the last letter keeps its own marks.
    stop = at[end] if end < len(at) else len(text)
    return text[at[start]:stop].strip()


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _example(raw: object, first: int, last: int, lines: list[str]) -> dict | None:
    """One saying, kept only when it is in one of its sense's own lines."""
    if not isinstance(raw, dict):
        return None
    english = _text(raw.get("english"))
    line = raw.get("line")
    if not english or not isinstance(line, int) or not first <= line - 1 <= last:
        return None
    arabic = find(lines[line - 1], _text(raw.get("arabic")))
    if not arabic:
        return None
    return {"line": line - 1, "arabic": arabic, "say": _text(raw.get("say")), "english": english}


def check(answer: object, lines: list[str]) -> list[dict] | None:
    """The model's answer as kept senses, or None when it does not fit the book.

    `answer` is the model's JSON ({"senses": [...]}, lines numbered from 1);
    `lines` is the entry as root_gloss.line_budget cut it.
    """
    raw = answer.get("senses") if isinstance(answer, dict) else None
    if not isinstance(raw, list) or not raw or not lines:
        return None
    senses, expected = [], 0
    for item in raw:
        if not isinstance(item, dict):
            return None
        span = item.get("lines")
        if not (isinstance(span, list) and span and all(isinstance(n, int) for n in span)):
            return None
        first, last = min(span) - 1, max(span) - 1
        gloss = _text(item.get("gloss"))
        # In order, nothing skipped, nothing twice: the lines are the book's,
        # and every one of them is printed under exactly one sense.
        if first != expected or last >= len(lines) or not gloss:
            return None
        expected = last + 1
        word = find(" ".join(lines[first:last + 1]), _text(item.get("word")))
        examples = [e for e in (_example(x, first, last, lines) for x in item.get("examples") or []) if e]
        senses.append({
            "lines": [first, last],
            "word": word,
            # A Latin spelling of a word that was not found would spell nothing on the page.
            "say": _text(item.get("say")) if word else "",
            "gloss": gloss,
            "examples": examples,
        })
    return senses if expected == len(lines) else None


def fits(senses: object, count: int) -> bool:
    """Whether kept senses still cover an entry of `count` lines in order. A
    book file that has changed shape since makes them a mispairing."""
    if not isinstance(senses, list) or not senses:
        return False
    expected = 0
    for sense in senses:
        span = sense.get("lines") if isinstance(sense, dict) else None
        if not (isinstance(span, list) and len(span) == 2 and span[0] == expected and span[1] >= span[0]):
            return False
        if not _text(sense.get("gloss")):
            return False
        expected = span[1] + 1
    return expected == count


def shown(senses: list[dict], lines: list[str]) -> list[dict]:
    """Kept senses as the card reads them: each with its own lines of the book."""
    return [
        {
            "arabic": lines[s["lines"][0]:s["lines"][1] + 1],
            "word": s.get("word", ""),
            "say": s.get("say", ""),
            "gloss": s["gloss"],
            "examples": [
                {k: e.get(k, "") for k in ("arabic", "say", "english")}
                for e in s.get("examples") or []
            ],
        }
        for s in senses
    ]
