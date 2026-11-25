"""The book's role vocabulary: every role's name (NAMED), and the key and tone a card is
coloured by. Read by the parser and by the card wording alike, so it sits outside both.
"""
from __future__ import annotations

from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.book import family_mother, in_family, named_roles, role_table

ROLES = role_table()
NAMED = named_roles()
SISTER_FAMILIES = ("inna", "kana", "kaada")  # the families whose members lend their name to what they govern


def _entry(role: str | None) -> tuple:
    # a recorded role is fully vowelled (نَائِبُ فَاعِلٍ); it is the same role
    plain = strip_diacritics(role or "")
    if plain in ROLES:
        return ROLES[plain]
    # اسم كأن، خبر ليس: named for the sister that governs it, coloured as its mother's (اسم إن، خبر كان)
    job, _, sister = plain.rpartition(" ")
    mother = next((family_mother(family) for family in SISTER_FAMILIES if job and in_family(sister, family)), None)
    return ROLES.get(f"{job} {mother}", (None, None))


def role_key(role: str | None) -> str | None:
    """The stable name the word grid colours a card by."""
    return _entry(role)[0]


def tone(role: str | None) -> str | None:
    """The colour the bracket diagram draws this role in."""
    return _entry(role)[1]
