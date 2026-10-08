"""What a ruling book says of one unit (one hadith's entry), quoted. Pure: no I/O.

Three books, three kinds of ruling (data/usul/usul.json `rulings`):

    nasikh_chapter   Ibn Shahin: the chapter heading the hadith stands under, and his closing remark where he makes one
    ilal             Ibn Abi Hatim: each answer of his father or of Abu Zur'a to the question about the hadith
    mawdu_listed     Ibn al-Jawzi: the sentence that judges the hadith, his own or a critic's he cites

A unit with no such sentence, or with more than one hadith, is not forced: `read` returns why instead. A quote is the
book's own words from where the rule starts to the end of the sentence, and goes on through a qualifier (إلا, لكن ...),
so it is never cut short. Only the editors' footnote numbers are taken out of it.
"""
from __future__ import annotations

import re
from typing import NamedTuple

from backend.services.usul.books import Entry

# Paragraphs are joined by this where a text runs on across them; `sentence` reads it.
PARAGRAPH = "\n"


class Ruling(NamedTuple):
    scholar: str   # who said it, as the book names him
    quote: str     # his words
    chapter: str   # the chapter it stands under
    head: str      # the unit's text before the ruling: the hadith as the book gives it, for matching it to ours
    at: int        # where the quote starts in the entry's text, for its page


def paragraphs(entry: Entry, strip: re.Pattern) -> list[tuple[int, str]]:
    """(offset in the entry's text, the paragraph) for each paragraph the book printed, footnote numbers out."""
    cuts = [0] + sorted({b for b in entry.breaks if 0 < b < len(entry.text)})
    found = []
    for start, end in zip(cuts, cuts[1:] + [len(entry.text)]):
        raw = entry.text[start:end]
        if raw.strip():
            found.append((start + len(raw) - len(raw.lstrip()), strip.sub("", raw).strip()))
    return found


def sentence(text: str, cfg: dict) -> str:
    """The first sentence of `text` (paragraphs joined by PARAGRAPH), whole: it ends at a full stop, a question mark or
    the end, and goes on through a qualifier (إلا, لكن ...) that opens the next one. A paragraph that opens with
    another speaker (وقال النسائي) ends it; a page break inside a sentence does not."""
    text = re.split(f"{PARAGRAPH}(?={cfg['speaker']})", text.lstrip(), maxsplit=1)[0].replace(PARAGRAPH, " ")
    stop = re.compile(cfg["stop"])
    qualifier = re.compile(cfg["qualifier"])
    end = 0
    while True:
        found = stop.search(text, end)
        if not found:
            return text.strip()
        end = found.end()
        if not qualifier.match(text[end:].lstrip()):
            return text[:end].strip()


def shahin(entry: Entry, cfg: dict) -> tuple[list[Ruling], str]:
    """The heading the hadith stands under; his remark where he closes it (قال الشيخ ..., هذا حديث ...)."""
    if not entry.heading:
        return [], "no heading"
    strip = re.compile(cfg["strip"])
    if sum(1 for _, p in paragraphs(entry, strip) if re.match(cfg["another"], p)) > 1:
        return [], "more than one hadith in the unit"
    text = strip.sub("", entry.text)
    opener = re.search(cfg["remark"], text)
    head, quote = (text[:opener.start(1)], text[opener.start(1):].strip()) if opener else (text, "")
    return [Ruling(cfg["scholar"], quote, _clean(entry.heading, strip), head.strip(), 0)], ""


def ilal(entry: Entry, cfg: dict) -> tuple[list[Ruling], str]:
    """The answers to the one question the unit asks: each scholar's first sentence after قال أبي / قال أبو زرعة ...,
    or after a bare قال / قالا that follows a question mark and answers the scholar last asked (the question's own, or
    a follow-up: قلت لأبي: أيهما أصح؟ قال: ...). It stops where Ibn Abi Hatim himself comments (قال أبو محمد)."""
    strip = re.compile(cfg["strip"])
    ps = paragraphs(entry, strip)
    asked = [i for i, (_, p) in enumerate(ps) if re.match(cfg["question"], p)]
    if len(asked) != 1:
        return [], f"{len(asked)} questions in the unit"
    q = asked[0]
    end = q + 1
    while end < len(ps) and not re.match(cfg["author"], ps[end][1]):
        end += 1
    region = PARAGRAPH.join(p for _, p in ps[q:end])
    first_end = len(ps[q][1])
    asker = _speakers(re.match(cfg["question"], ps[q][1])["who"], cfg)
    # What happens in the region, by place: whom a follow-up question puts to, and what answers.
    asks = [(m.start(), _speakers(m["who"], cfg)) for m in re.finditer(cfg["followup"], region)]
    answers = [(m.start(), _speakers(m["who"], cfg)) for m in re.finditer(cfg["answer"], region)]
    for m in re.finditer(cfg["bare_answer"], region):
        at = m.start("open")
        if m["dual"] == "قالا":   # both of the two asked
            if " و" in asker:
                answers.append((at, asker))
        elif at > first_end and (region[at - 1] == PARAGRAPH or any(place < at and PARAGRAPH not in region[place:at] for place, _ in asks)):
            # a bare قال heads its paragraph or follows a follow-up question; the hadith's own questions and answers do neither
            to = next((who for place, who in reversed(asks) if place < at), asker)
            if " و" not in to:
                answers.append((at, to))
    found: list[Ruling] = []
    taken = 0
    for start, scholars in sorted(answers):
        if start < taken or not scholars or any(r.scholar == scholars for r in found):   # inside the last answer, no one named, or his second
            continue
        quote = sentence(region[start:], cfg)
        taken = start + len(quote)
        head = region[:start].replace(PARAGRAPH, " ")
        found.append(Ruling(scholars, quote, _clean(entry.heading, strip), head, _entry_offset(ps[q:end], start)))
    return found, "" if found else "no answer"


def _entry_offset(group: list[tuple[int, str]], at: int) -> int:
    """Where in the entry's text the place `at` of the group's paragraphs (joined by PARAGRAPH) stands."""
    here = 0
    for offset, p in group:
        if at <= here + len(p):
            return offset + at - here
        here += len(p) + len(PARAGRAPH)
    return group[-1][0]


def _clean(text: str, strip: re.Pattern) -> str:
    return strip.sub("", text).strip()


def _speakers(text: str, cfg: dict) -> str:
    """The scholars `text` names, each once, as the book calls them: أبي is Abu Hatim, أبا زرعة is Abu Zur'a."""
    found = [name for pattern, name in cfg["speakers"] if re.search(pattern, text)]
    return " و".join(found)


def mawduat(entry: Entry, cfg: dict) -> tuple[list[Ruling], str]:
    """The first sentence after each hadith that judges it (هذا حديث موضوع, هذا لا يصح, لا أصل له ...), at the start of a
    paragraph, after a stop or a closing quote, or after قال فلان: . It is Ibn al-Jawzi's own, or a critic's he cites:
    قال أبو حاتم هذا حديث ... is Abu Hatim's, and the scholar is the one the book names.

    A bab with more than one hadith (حديث آخر, الحديث الثاني ...) is read a hadith at a time. A hadith with no verdict
    of its own takes a later one that judges them together (هذان حديثان موضوعان)."""
    ps = paragraphs(entry, re.compile(cfg["strip"]))
    cuts = [0] + [i for i, (_, p) in enumerate(ps) if i and re.match(cfg["another"], p)]
    parts = list(zip(cuts, cuts[1:] + [len(ps)]))
    chapter = _chapter(entry, ps[0][1], cfg)
    own, together = re.compile(cfg["verdict"]), re.compile(cfg["together"])
    found: list[Ruling] = []
    waiting: list[tuple[int, int]] = []   # parts with no verdict of their own yet
    for part in parts:
        if got := _verdict(ps, *part, own, cfg, chapter):
            found.append(got)
        else:
            waiting.append(part)
        if (joint := _verdict(ps, *part, together, cfg, chapter)) and waiting:
            found += [joint._replace(head=" ".join(q for _, q in ps[a:b])) for a, b in waiting]
            waiting = []
    return found, "" if found else "no verdict sentence"


def _verdict(ps: list[tuple[int, str]], start: int, end: int, opener: re.Pattern, cfg: dict, chapter: str) -> Ruling | None:
    """The first sentence of paragraphs start..end that `opener` finds, as a Ruling; None where there is none."""
    for i in range(start, end):
        if hit := opener.search(ps[i][1]):
            quote = sentence(PARAGRAPH.join([ps[i][1][hit.start(1):], *(q for _, q in ps[i + 1:end])]), cfg)
            who = (hit.groupdict().get("who") or "").strip()
            head = " ".join([q for _, q in ps[start:i]] + [ps[i][1][:hit.start(1)]])
            return Ruling(who if who and who not in cfg["self"] else cfg["scholar"], quote, chapter, head, ps[i][0] + hit.start(1))
    return None


def _chapter(entry: Entry, first: str, cfg: dict) -> str:
    """The book's chapter and the title of the section (باب ...) up to where the chain begins."""
    chain = re.search(cfg["chain_start"], first)
    title = first[:chain.start()].strip() if chain else first
    return "، ".join(part for part in (entry.heading, title) if part)


READERS = {"nasikh_chapter": shahin, "ilal": ilal, "mawdu_listed": mawduat}


def read(entry: Entry, kind: str, cfg: dict) -> tuple[list[Ruling], str]:
    """(the rulings the unit holds, "") or ([], why not). cfg is usul.json `rulings`."""
    return READERS[kind](entry, {**cfg["shared"], **cfg["kinds"][kind]})
