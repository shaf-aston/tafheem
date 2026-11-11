"""A Maqayees entry cut into its words, each with the book's lines beside it.

Ibn Faris's entry runs as one paragraph: a word, what it means, a saying or
two that use it, the next word. A model reads the numbered lines and says which
lines belong to which word, what that word is, and what it means. This module
checks that answer against the book before anything keeps or shows it.

The Arabic is never the model's. Each sense names its lines by number, so the
book's own lines are what the card prints; the word and every example saying
must be found in those lines (the vowel marks aside, which a model drops), and
what is shown is the book's spelling of it, cut from the line. Every line is
printed under exactly one sense, in order (see check). A word or a saying that
cannot be found is dropped, never shown as the model wrote it.

Kept shape, one dict per sense: {"lines": [first, last], "word", "say",
"gloss", "examples": [{"line", "arabic", "say", "english"}]}, lines counted
from 0. `shown` turns it into what the card reads, with the Arabic lines in.
"""
from __future__ import annotations

import json
import logging

from backend.services.core.ratelimit import OverBudget
from backend.services.text.arabic_text import DIACRITICS_RE

logger = logging.getLogger(__name__)


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
    `lines` is the entry as root_gloss.line_budget cut it. Every line ends up
    under exactly one sense, in order. A line the model skipped or gave twice
    stays with the word before it, as the book runs on from a word into the
    next, and so do the lines of a word given without line numbers or without
    a gloss; an answer that leaves more than a third of the lines to that is
    refused, as one that misread the entry.
    """
    raw = answer.get("senses") if isinstance(answer, dict) else None
    if not isinstance(raw, list) or not raw or not lines:
        logger.warning("word by word refused: no senses in the answer")
        return None
    spans, given = [], 0
    for item in raw:
        span = item.get("lines") if isinstance(item, dict) else None
        if not (isinstance(span, list) and span and all(isinstance(n, int) for n in span)):
            continue
        gloss = _text(item.get("gloss"))
        if not gloss:
            continue
        first = max(min(span) - 1, spans[-1][1] + 1 if spans else 0)
        last = min(max(span) - 1, len(lines) - 1)
        if first <= last:  # else only lines an earlier word already has
            spans.append([first, last, item, gloss])
            given += last - first + 1
    if not spans or len(lines) - given > len(lines) // 3:
        logger.warning("word by word refused: the answer placed %d of %d lines", given, len(lines))
        return None
    spans[0][0] = 0
    for before, after in zip(spans, spans[1:]):
        before[1] = after[0] - 1
    spans[-1][1] = len(lines) - 1

    senses = []
    for first, last, item, gloss in spans:
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
    return _joined_to_quotes(senses, lines)


def _leads_in(text: str) -> bool:
    """A line that only introduces what follows: قال الشاعر:, قال:."""
    return text.rstrip().endswith(":")


def _joined_to_quotes(senses: list[dict], lines: list[str]) -> list[dict]:
    """Each wordless sense whose lines only lead in, folded into the sense after
    it, so a poem is one row, not "The poet said" and then a row of verse."""
    out: list[dict] = []
    carry: int | None = None
    for i, sense in enumerate(senses):
        first, last = sense["lines"]
        if carry is not None:
            sense["lines"] = [carry, last]
            carry = None
        if (not sense["word"] and i + 1 < len(senses)
                and all(_leads_in(lines[n]) for n in range(first, last + 1))):
            carry = first
            continue
        out.append(sense)
    return out


def cut(ask, lines: list[str]) -> list[dict] | None:
    """`lines` cut into senses by `ask(lines)`, the model's answer, checked; one
    more go for an answer that does not fit, does not parse, or never came (the
    model service refuses an answer of its own that was not JSON). None after
    two; a call that failed both times raises its error, a timeout at once."""
    failed = []
    for _ in range(2):
        try:
            senses = check(ask(lines), lines)
        except (TimeoutError, OverBudget):
            raise
        except Exception as exc:  # a failed call is a failed try, not a crash
            logger.warning("word by word try failed: %s: %s", type(exc).__name__, exc)
            failed.append(exc)
            continue
        if senses is not None:
            return senses
    if len(failed) == 2 and not isinstance(failed[-1], json.JSONDecodeError):
        raise failed[-1]
    return None


def joined(parts: list[list[dict] | None]) -> list[dict] | None:
    """Senses cut chunk by chunk (root_gloss.chunks) as one entry's: line
    numbers moved along to where each chunk starts. None when any chunk failed,
    since a gap would leave lines with no word. A word whose lines straddle two
    chunks becomes two senses."""
    if not parts or any(part is None for part in parts):
        return None
    senses, start = [], 0
    for part in parts:
        for sense in part:
            senses.append({
                **sense,
                "lines": [n + start for n in sense["lines"]],
                "examples": [{**e, "line": e["line"] + start} for e in sense["examples"]],
            })
        start += part[-1]["lines"][1] + 1  # check covers a chunk to its last line
    return senses


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
