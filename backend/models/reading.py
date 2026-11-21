"""Reply type for routers/read.py."""
from __future__ import annotations

from pydantic import BaseModel

from backend.models.common import Source


class PictureText(BaseModel):
    """The Arabic a picture holds, as text for the reader to check before it is translated.

    Lines as they sat on the page, an empty line between paragraphs; empty when the picture holds
    no Arabic. `unsure` when the one reading had was a doubtful one (Tesseract on a page it could
    not read well, with no model to ask), so the page says to check it with extra care."""

    text: str
    source: Source
    unsure: bool = False
