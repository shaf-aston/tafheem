"""A hosted vision model, on the Groq key: a picture's Arabic as text, vowel marks and all.

Asked only when Tesseract is unsure (see the package's docstring), so a plain page costs no model
call. Its answer is checked the way every model answer a reader sees is: text, Arabic, no links,
no longer than a page. A failure that will not mend itself (a rejected key, a model Groq has
withdrawn: it is a preview) strikes it off for the run, here, and the text answers carry on.
"""
from __future__ import annotations

import base64
import logging
import re

from backend.config import get_settings
from backend.services import ai
from backend.services.core.fallback import Retirable, permanent_failure
from backend.services.core.ratelimit import OverBudget
from backend.services.text.arabic_text import has_arabic

logger = logging.getLogger(__name__)

_engine = Retirable()
# A page of text in characters, with room to spare; past it the model is not copying a page.
_LONGEST = 20_000
_LINKISH = re.compile(r"https?:|www\.|</?[A-Za-z]")


def name() -> str:
    return get_settings().read_model.strip()


def available() -> bool:
    return bool(get_settings().has_groq and name() and not _engine.retired_reason)


def read(jpeg: bytes) -> str:
    try:
        answer = ai.read_picture(base64.b64encode(jpeg).decode("ascii"), "image/jpeg")
    except OverBudget:
        raise
    except Exception as exc:
        if reason := permanent_failure(exc):
            _engine.retire(reason)
            logger.warning("page reader  retiring %s for this run, %s", name(), reason)
        raise
    return checked(answer.get("text") if isinstance(answer, dict) else None)


def checked(text: object) -> str:
    """The model's text if it reads as a copy of a page, else ValueError."""
    if not isinstance(text, str):
        raise ValueError("the model sent no text")
    if text.strip() and not has_arabic(text):
        raise ValueError("the model's text has no Arabic in it")
    if len(text) > _LONGEST or _LINKISH.search(text):
        raise ValueError("the model's text is not a copy of a page")
    return text
