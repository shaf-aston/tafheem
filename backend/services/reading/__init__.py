"""A picture of Arabic text, read into text: the page reader's first step.

    picture.py    the upload checked and tidied: upright, grey, dark pages turned light, small type enlarged
    tesseract.py  Tesseract on this computer: about 0.3s a page, free, near perfect on plain print and
                  screenshots, lost on a fully vowelled page (it takes the marks for letters)
    vision.py     a hosted vision model on the Groq key, asked only when Tesseract is unsure

Cheapest first. Tesseract's own confidence tells the two kinds of page apart (86-91 on a clean read,
35-55 on a vowelled one, `read_sure_confidence` between them), so a plain page never waits on a model
and a vowelled one is not left as Tesseract's guess when a model can do better. What comes back is
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

__all__ = ["NoReader", "NotAPicture", "health", "read"]

logger = logging.getLogger(__name__)


class NoReader(RuntimeError):
    """Neither reader can be used on this server: no Tesseract with Arabic, and no vision model."""


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
    first = tesseract.read(page.grey) if tesseract.available() else None
    if first and first.confidence >= get_settings().read_sure_confidence:
        return _answer(first.text, "tesseract")
    if vision.available():
        try:
            return _answer(vision.read(page.colour), "vision")
        except OverBudget:
            if first is None:
                raise
        except Exception as exc:  # noqa: BLE001, Tesseract's reading still stands
            logger.warning("page reader  the vision model failed, keeping Tesseract's reading: %s", exc)
    if first is None:
        raise NoReader("No reader on this server: install tesseract-ocr-ara, or set GROQ_API_KEY")
    return _answer(first.text, "tesseract", unsure=True)


def _answer(text: str, source: str, unsure: bool = False) -> dict:
    return {"text": tidy(text), "source": provenance.of(source), "unsure": unsure}


def health() -> str:
    """Which readers this server has, for /api/health: "tesseract", "tesseract + <model>", or "none"."""
    found = [name for name, there in (("tesseract", tesseract.available()), (vision.name(), vision.available())) if there]
    return " + ".join(found) or "none"
