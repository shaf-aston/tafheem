"""One username, one learner. No password, so this only decides spelling.

The only copy of these rules: the page sends what was typed and keeps the
spelling the server hands back (POST /api/progress/signup and /login).

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


def _kind(ch: str) -> str:
    """'name' for a letter or digit, 'mark' for what may sit beside one, else ''."""
    category = unicodedata.category(ch)
    if category[0] == "L" or category == "Nd":
        return "name"
    # Marks are tashkeel; the extras are the separators people put in names.
    return "mark" if category[0] == "M" or ch in _EXTRA else ""


def clean_name(raw: str) -> str:
    """The one spelling of a username. Raises ValueError when it is not a name."""
    settings = get_settings()
    name = unicodedata.normalize("NFC", re.sub(r"\s+", " ", raw).strip()).casefold()
    if not name:
        raise ValueError("Type a username")
    if len(name) > settings.profile_name_max:
        raise ValueError(f"Names are at most {settings.profile_name_max} characters")
    kinds = {_kind(ch) for ch in name}
    if "" in kinds or "name" not in kinds:
        raise ValueError(BAD_CHARACTERS)
    if name in settings.profile_reserved:
        raise ValueError("That name is taken by the app, pick another")
    return name
