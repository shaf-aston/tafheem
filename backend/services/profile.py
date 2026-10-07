"""One typed name, one learner. No password, so this only decides spelling.

"Amina", " amina " and "AMINA" are one person: spaces are squashed, the text is
put in one Unicode form, then case is folded. Tashkeel is kept, so a name
written with vowels is its own name; stripping it would merge names people
chose to write differently.
"""
from __future__ import annotations

import re
import unicodedata

from backend.config import get_settings

BAD_CHARACTERS = "Names use letters, numbers, spaces, - _ ."

# Zero-width non-joiner and joiner stay: Persian and Urdu names need them.
_EXTRA = set(" -_.\u200c\u200d")


def _counts(ch: str) -> bool:
    return unicodedata.category(ch)[0] == "L" or unicodedata.category(ch) == "Nd"


def _allowed(ch: str) -> bool:
    # Letters and marks of any script (Arabic tashkeel are marks), and digits.
    return ch in _EXTRA or unicodedata.category(ch)[0] in "LM" or unicodedata.category(ch) == "Nd"


def clean_name(raw: str) -> str:
    """The one spelling of a typed name. Raises ValueError when it is not a name."""
    settings = get_settings()
    name = unicodedata.normalize("NFC", re.sub(r"\s+", " ", raw).strip()).casefold()
    if not name:
        raise ValueError("Type a name")
    if len(name) > settings.profile_name_max:
        raise ValueError(f"Names are at most {settings.profile_name_max} characters")
    if not all(_allowed(ch) for ch in name) or not any(_counts(ch) for ch in name):
        raise ValueError(BAD_CHARACTERS)
    if name in settings.profile_reserved:
        raise ValueError("That name is taken by the app, pick another")
    return name
