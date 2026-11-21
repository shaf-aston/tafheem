"""A picture of Arabic text, read into text: the page reader's first step.

    picture.py    the upload checked and tidied: upright, grey, dark pages turned light, small type enlarged
    tesseract.py  Tesseract on this computer: 0.3s a screenshot, 1-2s a full page, free, near perfect on
                  plain print and screenshots, lost on a fully vowelled page (it takes the marks for letters)
    vision.py     a hosted vision model on the Groq key, asked only when Tesseract is unsure

Cheapest first. A small picture (a phone screenshot) is read enlarged twice over: its type is small,
and read at its own size Tesseract misspells words it is sure of. An unsure reading is tried again
turned upright when Tesseract's orientation check finds a photo held sideways; the surer of the two
stands. Tesseract's own confidence tells the two kinds of page apart (86-91 on a clean read,
35-55 on a vowelled one, `read_sure_confidence` between them), so a plain page never waits on a model
and a vowelled one is not left as Tesseract's guess when a model can do better. A picture in which
Tesseract found no words at all (a blank, a photo of a cat) is not sent to the model either: it
would spend the AI budget every visitor shares on nothing. What comes back is
always shown to the reader to check against the picture and correct before it is translated: the
text is the start of the page reader, never its last word.
"""
from __future__ import annotations

import logging
import re

from backend.config import get_settings
from backend.services.core import provenance
from backend.services.core.ratelimit import OverBudget
from backend.services.reading import picture, tesseract, vision
from backend.services.reading.picture import NotAPicture

__all__ = ["NoReader", "NotAPicture", "NotRead", "health", "read"]

logger = logging.getLogger(__name__)


class NoReader(RuntimeError):
    """Neither reader can be used on this server: no Tesseract with Arabic, and no vision model."""


class NotRead(RuntimeError):
    """The only reader here (the vision model) failed on this picture: worth trying again."""


# Tesseract writes the Latin marks for the Arabic ones. Not a comma between digits (1,000).
_MARKS = ((re.compile(r",(?!\d)"), "،"), (re.compile(r";"), "؛"), (re.compile(r"\?"), "؟"))
_BLANKS = re.compile(r"\n{3,}")
_SPACES = re.compile(r"[ \t ]+")


def tidy(text: str) -> str:
    """Arabic punctuation for Latin, one space between words, at most one empty line between paragraphs."""
    for latin, arabic in _MARKS:
        text = latin.sub(arabic, text)
    lines = (_SPACES.sub(" ", line).strip() for line in text.replace("\r", "").split("\n"))
    return _BLANKS.sub("\n\n", "\n".join(lines)).strip()


def read(body: bytes) -> dict:
    """{"text", "source", "unsure"} for an uploaded picture; `unsure` when only an unsure reading was had.

    NotAPicture when the file is not one; NoReader when nothing here can read; OverBudget when the model
    was needed, Tesseract had nothing, and this visitor's model calls are spent for the minute.
    """
    page = picture.prepare(body)
    here = tesseract.available()
    first = _surest(page) if here else None  # None too when it failed on this picture
    if first and first.confidence >= get_settings().read_sure_confidence:
        return _answer(first.text, "tesseract")
    if vision.available() and (first is None or first.text.strip()):
        try:
            return _answer(vision.read(page.jpeg()), "vision")
        except OverBudget:
            if first is None:
                raise
        except Exception as exc:  # noqa: BLE001, Tesseract's reading still stands
            logger.warning("page reader  the vision model failed, keeping Tesseract's reading: %s", exc)
    if not here:
        if vision.available():  # it was asked above and failed
            raise NotRead("the vision model could not read this picture just now")
        raise NoReader("No reader on this server: install tesseract-ocr-ara, or set GROQ_API_KEY")
    return _answer(first.text if first else "", "tesseract", unsure=True)


def _surest(page: picture.Prepared) -> tesseract.Reading | None:
    """Tesseract's reading (a small picture enlarged first: its type is small), read again turned upright when unsure."""
    scale = 2 if page.small() else 1
    first = tesseract.read(page.grey(scale=scale))
    if first is None:  # it failed or ran out of time: a second read would only do the same, holding the slot
        return None
    if first.confidence >= get_settings().read_sure_confidence:
        return first
    turn = tesseract.upright(page.grey())
    again = tesseract.read(page.grey(scale=scale, turn=turn)) if turn else None
    return max((one for one in (first, again) if one), key=lambda one: one.confidence)


# A word of Arabic: two of its letters together. A lone comma, tatweel (U+0640) or digit is not one.
_ARABIC_WORD = re.compile(r"[\u0621-\u063A\u0641-\u064A]{2}")


def _answer(text: str, source: str, unsure: bool = False) -> dict:
    """The reading, tidied; no text at all when it has no Arabic word in it (an English page, noise)."""
    text = tidy(text)
    if not _ARABIC_WORD.search(text):
        text, unsure = "", True
    return {"text": text, "source": provenance.of(source), "unsure": unsure}


def health() -> str:
    """Which readers this server has, for /api/health: "tesseract", "tesseract + vision", or "none".
    Never the model's name: which model reads is this server's business."""
    found = [name for name, there in (("tesseract", tesseract.available()), ("vision", vision.available())) if there]
    return " + ".join(found) or "none"
