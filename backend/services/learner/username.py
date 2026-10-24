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

# Whose record an answer is when nobody is logged in and the page sends no device id (a page from
# before devices had one), so never a username.
GUEST = "local"
# A device's own guest record: this, then the 32 hex the page made (lib/learner/profile.js deviceId).
# ":" is not a name character, so no username is ever one.
DEVICE = "guest:"
_DEVICE_ID = re.compile(r"[0-9a-f]{32}")

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
    max_length = get_settings().username_max
    name = unicodedata.normalize("NFC", re.sub(r"\s+", " ", raw).strip()).casefold()
    if not name:
        raise ValueError("Type a username")
    if len(name) > max_length:
        raise ValueError(f"Names are at most {max_length} characters")
    kinds = {_kind(ch) for ch in name}
    if "" in kinds or "name" not in kinds:
        raise ValueError(BAD_CHARACTERS)
    if name == GUEST:
        raise ValueError("That name is taken by the app, pick another")
    return name


def device_key(raw: str) -> str:
    """The record key of the device that sent `raw`. Raises ValueError unless it is 32 lowercase hex."""
    if not _DEVICE_ID.fullmatch(raw):
        raise ValueError("Not a device id")
    return DEVICE + raw


def is_guest(user: str) -> bool:
    """True for the shared guest record and for a device's own: nobody's account."""
    return user == GUEST or user.startswith(DEVICE)
