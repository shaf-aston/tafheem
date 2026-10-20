"""Cutting al-Tahawi's Sharh Mushkil al-Athar into issues, one per bab.

The book is a run of chapters. Each opens with a heading, "باب بيان مشكل ما روي
عن رسول الله ... في ...", names a topic where narrations seem to disagree, lists
the narrations, and ends with Tahawi's own reconciliation. So one bab is one
issue, and the grouping is the scholar's, never ours.

OpenITI marks the file like this, and the cutter reads only these marks:
  "# | 12 باب ..."   a chapter heading (the number is the edition's, and not in
                      order; one heading in ten has lost its first letter, "اب")
  "# 345 ..."        a paragraph, numbered: the edition's own hadith number
  "# ..."            a paragraph without a number
  "~~..."            the same paragraph, carried on to the next line
A paragraph in a bab is a narration when it carries a hadith number or opens
with a chain word; anything else is Tahawi talking, and stays as discussion.

A paragraph outside any bab (the preface, the basmala) or repeating the one
before it is returned as unplaced with the reason. Never dropped silently.

Pure: text in, issues and unplaced out. No files, no network.
"""
from __future__ import annotations

import re

# Where the book's text begins; everything above is OpenITI's metadata.
HEADER_END = "#META#Header#End#"
# What follows "# |" in a bab heading: an optional edition number, then باب (or
# its damaged form اب, a letter lost in the scan).
HEADING = re.compile(r"^(?:\d+\s+)?(?:ب)?اب\b")
# The words a chain opens with. A numbered paragraph needs none of them.
NARRATION_OPENERS = ("حدثنا", "أخبرنا", "حدثني", "أخبرني", "أنبأ", "أنبأنا", "وحدثنا")
# Tahawi's own voice. The file breaks paragraphs rarely, so his reconciliation
# often runs on at the end of the narration's paragraph; the cut is made here.
VOICE = "قال أبو جعفر"
# The edition's hadith number at the start of a paragraph.
NUMBER = re.compile(r"^\d+\s")
# OpenITI's own marks, which belong to the file and not to the book: page and
# word-count milestones, the Qur'an quotation brackets, and the manuscript
# variants "( ( ( x ) ) )", which are the editor's footnote and not the text.
NOISE = re.compile(r"PageV\d+P\d+|\bms\d+\b|@QB@|@QE@|\(\s*\(\s*\(.*?\)\s*\)\s*\)")


def clean(text: str) -> str:
    """The prose with OpenITI's marks taken out and the whitespace folded."""
    return re.sub(r"\s+", " ", NOISE.sub(" ", text)).strip()


def paragraphs(book: str) -> list[tuple[int, str, str]]:
    """(line number, kind, cleaned text) per paragraph, in the book's order.

    kind is "heading" for a "# |" line and "para" for any other "# " line; the
    "~~" lines under either are joined onto it.
    """
    head, found, rest = book.partition(HEADER_END)
    first = head.count("\n") + 1 if found else 1
    rows: list[list] = []
    for number, line in enumerate((rest if found else book).split("\n"), start=first):
        line = line.rstrip("\r")
        if line.startswith("~~") and rows:
            rows[-1][2] += " " + line[2:]
        elif line.startswith("#"):
            kind = "heading" if line.startswith("# |") else "para"
            body = line[1:].strip().removeprefix("|").strip()
            rows.append([number, kind, body])
    return [(n, kind, clean(text)) for n, kind, text in rows if clean(text)]


def is_narration(text: str) -> bool:
    return bool(NUMBER.match(text)) or text.split(" ", 1)[0] in NARRATION_OPENERS


def split(book: str) -> tuple[list[dict], list[dict]]:
    """(issues, unplaced). Each issue: id, heading, narrations, discussion, offset."""
    issues: list[dict] = []
    unplaced: list[dict] = []
    previous = None
    for offset, kind, text in paragraphs(book):
        if kind == "heading" and HEADING.match(text):
            title = "باب" + HEADING.sub("", text, count=1)
            issues.append({"id": len(issues) + 1, "heading": title, "narrations": [], "discussion": "", "offset": offset})
            previous = None
            continue
        if not issues:
            unplaced.append({"offset": offset, "why": "before the first bab", "text": text})
        elif kind == "heading":
            unplaced.append({"offset": offset, "why": "a heading line that is not a bab", "text": text})
        elif text == previous:
            unplaced.append({"offset": offset, "why": "repeats the paragraph before it", "text": text})
        elif is_narration(text):
            matn, _, voice = text.partition(VOICE)
            if len(matn.split()) > 1:
                issues[-1]["narrations"].append(matn.strip())
            if voice:
                issues[-1]["discussion"] = (issues[-1]["discussion"] + " " + VOICE + voice).strip()
        else:
            issues[-1]["discussion"] = (issues[-1]["discussion"] + " " + text).strip()
        previous = text
    return issues, unplaced
