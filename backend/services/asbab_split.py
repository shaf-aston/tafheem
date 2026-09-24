"""Cutting al-Suyuti's Lubab al-Nuqul into reports, and finding each one's ayah.

The book is running prose with no ayah numbers in it. It has surah headings, and
inside a heading every report opens the same way: قوله تعالى, then the opening
words of the ayah, then الآية (or الآيات for a run), then the report itself with
its chain. So a report is "from one قوله تعالى to the next", and its ayah is the
ayah in that surah whose words those opening words are.

Matching is by folded letters (arabic_text.bare_letters), because the book is
unvowelled and the Qur'an here is not, and only inside the surah the heading
named. A report whose words match no ayah, or more than one, is returned as
unmatched and listed. It is never attached to a best guess: attaching a report to
the wrong ayah would put a story about Badr on an ayah about inheritance, and
nothing downstream could tell.

Pure: text in, passages and misses out. No files, no network, no database.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from backend.services.arabic_text import bare_letters

# The heading that opens a surah's reports, "### | سورة البقرة".
HEADING = re.compile(r"^###\s*\|\s*(.+)$", re.MULTILINE)
# Every report opens with these words. Kept as one expression because "قوله
# تعالى" is also how the book quotes an ayah mid-report, which is why the cut is
# made on the opening of a line's worth of prose and then checked for an ayah.
OPENING = "قوله تعالى"
# Where the quoted words stop and the report starts. The book ends a quotation
# in three ways and uses all of them: the word الآية, its own ayah number in
# brackets (the editor's, and the surest of the three), or nothing at all, the
# prose simply carrying on with the words that open a chain.
ENDS = ("الآيتين", "الآيات", "الآية")
NUMBERED = re.compile(r"\[(\d{1,3})\]")
CHAIN_OPENS = ("أخرج", "وأخرج", "روى", "وروى", "أورد", "وقال", "ذكر")
# Headings that are the book talking about itself rather than about a surah.
NOT_A_SURAH = ("مقدمة", "تنبيهات", "خاتمة")
# OpenITI's own marks, which belong to the file and not to the book.
NOISE = re.compile(r"PageV\d+P\d+|ms\d+|~~|^#\s?|﻿", re.MULTILINE)
# Two words are enough when they open an ayah and no other ayah in the surah
# starts the same way, which is the check below; one word never is.
SHORTEST_QUOTE_WORDS = 2
# Past this, a "quotation" is the report's own prose and matching it is hopeless.
LONGEST_QUOTE_WORDS = 10


@dataclass(frozen=True)
class Report:
    """One report, before its ayah is known."""

    surah_heading: str
    quote: str          # the ayah's opening words, as the book wrote them
    text: str           # the report itself, chain and all
    run: bool           # the book said الآيات: about a run of ayahs, not one
    numbered: int | None = None   # the ayah number the edition printed, where it did


def clean(text: str) -> str:
    """The book's prose with OpenITI's page and milestone marks taken out.

    Line breaks go with them: the file wraps mid-sentence, and a quotation cut
    across two lines would be compared against an ayah that has no line break in
    it and match nothing at all.
    """
    return re.sub(r"\s+", " ", NOISE.sub(" ", text)).strip()


def sections(book: str) -> list[tuple[str, str]]:
    """(heading, body) per surah heading, in the book's own order."""
    found = []
    marks = list(HEADING.finditer(book))
    for mark, next_mark in zip(marks, marks[1:] + [None]):
        body = book[mark.end():next_mark.start() if next_mark else len(book)]
        # The heading is cleaned too: OpenITI drops its word-count milestones
        # inside them ("سورة ms139 الشعراء"), and a milestone in the middle of a
        # name matches no surah.
        found.append((clean(mark.group(1)), body))
    return found


def reports(book: str) -> list[Report]:
    """Every report in the book, each still carrying its surah's heading."""
    found = []
    for heading, body in sections(book):
        body = clean(body)
        pieces = body.split(OPENING)[1:]    # before the first opening is the preamble
        for piece in pieces:
            quote, numbered, run, rest = _cut_quote(piece)
            if not quote or not rest.strip():
                continue
            found.append(Report(heading, quote, rest.strip(), run=run, numbered=numbered))
    return found


def _cut_quote(piece: str) -> tuple[str, int | None, bool, str]:
    """The quoted words, the ayah number the edition printed, whether it said "the
    ayahs", and the report that follows.

    Cut at whichever of the three endings comes first: a quotation that swallows
    the chain behind it matches no ayah at all, and one cut at a later ending
    takes half a report along with it.
    """
    # `at` is where the quotation stops, `after` where the report starts: the two
    # differ by the ending itself, and a report that keeps the last letter of
    # الآية begins with a stray letter on every card that shows it.
    at, after, said, number = len(piece), len(piece), "", None
    for word in ENDS:
        found = piece.find(f" {word}")
        if found != -1 and found < at:
            at, after, said = found, found + 1 + len(word), word
    if (found := NUMBERED.search(piece)) and found.start() < at:
        at, after, said, number = found.start(), found.end(), "", int(found.group(1))
    for word in CHAIN_OPENS:
        found = piece.find(f" {word} ")
        if found != -1 and found < at:
            at, after, said, number = found, found, "", None
    return piece[:at].strip(), number, said in ("الآيات", "الآيتين"), piece[after:]


def match_surah(heading: str, names: dict[int, str], aliases: dict[str, int]) -> int | None:
    """The surah a heading names, by folded name, with the book's own spellings.

    The Lubab writes some names its own way (براءة for at-Tawbah) and some with a
    stray letter (الآنفال). Those live in a data file as aliases rather than in
    this code, so a spelling this misses is one line of JSON.
    """
    if any(word in heading for word in NOT_A_SURAH):
        return None
    folded = bare_letters(heading).replace("سورة", "").strip()
    if folded in aliases:
        return aliases[folded]
    for number, name in names.items():
        if bare_letters(name).strip() == folded:
            return number
    return None


def match_ayah(quote: str, ayahs: dict[int, str], numbered: int | None = None) -> tuple[int | None, str]:
    """The ayah in this surah the quoted words open, or why there is no answer.

    The edition's own bracketed number is taken first, and still checked: the
    quoted words have to be in that ayah, or the number is somebody's slip and
    the words decide instead.

    Otherwise the quotation is looked for at the start of an ayah, which is what
    the book is doing, and only then anywhere inside one; and it is shortened a
    word at a time, because the book runs into its chain without warning and the
    tail of a quotation is often the opening of a report. Several ayahs matching
    is refused rather than settled by taking the first: the Qur'an repeats
    phrases, and يا أيها الذين آمنوا opens dozens of ayahs.
    """
    folded = re.sub(r"\s+", " ", bare_letters(quote)).strip()
    words = folded.split()
    if len(words) < SHORTEST_QUOTE_WORDS:
        return None, "the quotation is too short to place"
    texts = {number: bare_letters(text) for number, text in ayahs.items()}

    if numbered in texts and " ".join(words[:SHORTEST_QUOTE_WORDS]) in texts[numbered]:
        return numbered, "numbered by the edition"

    for length in range(min(len(words), LONGEST_QUOTE_WORDS), SHORTEST_QUOTE_WORDS - 1, -1):
        part = " ".join(words[:length])
        for where in ("opens", "inside"):
            hits = [
                number for number, text in texts.items()
                if (text.startswith(part) if where == "opens" else part in text)
            ]
            if len(hits) == 1:
                return hits[0], where
    return None, "the words match no single ayah of this surah"


def passages(book: str, names: dict[int, str], aliases: dict[str, int], text_of) -> tuple[list[dict], list[dict]]:
    """Every report placed on its ayah, and every report that could not be placed.

    `text_of(surah)` gives {ayah: text} for one surah. Reports landing on the same
    ayah are kept in the book's order and joined into one passage, numbered, so a
    reader is never shown one report where the book gives three.
    """
    placed: dict[tuple[int, int], list[Report]] = {}
    missed: list[dict] = []
    for report in reports(book):
        if any(word in report.surah_heading for word in NOT_A_SURAH):
            continue    # the book's own preface and notes, not a surah's reports
        surah = match_surah(report.surah_heading, names, aliases)
        if surah is None:
            missed.append({"heading": report.surah_heading, "quote": report.quote, "why": "the heading names no surah"})
            continue
        ayah, why = match_ayah(report.quote, text_of(surah), report.numbered)
        if ayah is None:
            missed.append({"surah": surah, "heading": report.surah_heading, "quote": report.quote, "why": why})
            continue
        placed.setdefault((surah, ayah), []).append(report)

    rows = []
    for (surah, ayah), found in sorted(placed.items()):
        rows.append({"surah": surah, "ayah": ayah, "text": _one_passage(found)})
    return rows, missed


def _one_passage(found: list[Report]) -> str:
    """The reports on one ayah as one passage, numbered when there is more than one.

    Each keeps the word the book closed its quotation with: الآيات means the
    report is about a run of ayahs and is only filed on the one it opens with,
    and printing الآية over it would have the book say something it did not.
    """
    said = lambda report: "الآيات" if report.run else "الآية"   # noqa: E731, one line, one use
    if len(found) == 1:
        return f"{OPENING} {found[0].quote} {said(found[0])}\n{found[0].text}"
    return "\n\n".join(
        f"[{i} / {len(found)}] {OPENING} {report.quote} {said(report)}\n{report.text}"
        for i, report in enumerate(found, start=1)
    )
