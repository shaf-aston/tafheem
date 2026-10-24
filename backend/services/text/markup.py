"""Marked-up text from somewhere else, as plain paragraphs. Pure.

Every book this app takes in from outside arrives as HTML: Quran.com sends it,
and the Quranic Universal Library's exports keep whatever tags the source data
had. Nothing in this app renders HTML from a third party, so it is stripped once,
at the edge, on the way into the database. What is stored is text, and there is
then no way for markup to reach a page at all.

This lives in services rather than beside one importer because two importers need
it and a second copy of a stripper is a second set of rules about what a
paragraph break is. It touches no file and no network; it is a string in and a
string out.
"""
from __future__ import annotations

import html
import re

# A footnote marker goes with its number. Quran.com writes them as
# "Allah,<sup foot_note=195932>1</sup> the Entirely Merciful": stripping the tag
# alone would leave the 1 stuck to the sentence, reading as part of it. Nothing
# in this app shows footnotes, so the marker has nothing to point at either way.
_FOOTNOTE = re.compile(r"<sup\b[^>]*>.*?</sup>", re.I | re.S)

# Block-level markup becomes a paragraph break; everything else simply goes.
_BLOCK_END = re.compile(r"</(p|div|h[1-6]|li|tr|blockquote)\s*>", re.I)
_BREAK = re.compile(r"<br\s*/?>", re.I)
_TAG = re.compile(r"<[^>]+>")
_BLANK_LINES = re.compile(r"\n{3,}")

# Characters that are not text but instructions to whatever draws the text.
#
#   The C0 controls, minus the newline this function's whole job is to produce.
#   The bidi overrides and isolates, U+202A-202E and U+2066-2069, plus the marks
#   U+200E/200F. An unterminated right-to-left override in a downloaded book
#   does not stop at the passage: it reverses the reading order of everything
#   drawn after it. In a page that already mixes Arabic and English, that is not
#   a cosmetic problem, it is the page telling the reader something false about
#   which script a line is in.
_CONTROLS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f‎‏‪-‮⁦-⁩]")


def as_text(markup: str) -> str:
    """The passage as paragraphs of plain text, with all markup removed."""
    text = _FOOTNOTE.sub("", markup or "")
    text = _BREAK.sub("\n", text)
    text = _BLOCK_END.sub("\n\n", text)
    text = _TAG.sub("", text)
    text = html.unescape(text)
    # Again, after unescaping. A source that writes &lt;script&gt; has no tag for
    # the pass above to find, and unescaping then turns it into one. Nothing here
    # renders HTML, so this is not the thing standing between a reader and a
    # script; it is what keeps that true of the stored text rather than only of
    # today's components.
    text = _TAG.sub("", text)
    text = _CONTROLS.sub("", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _BLANK_LINES.sub("\n\n", text).strip()
