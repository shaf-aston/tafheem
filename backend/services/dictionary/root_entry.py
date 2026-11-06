"""A Maqayees entry retold in English: the shipped whole-book English first, the model only for
what is not kept. Returns the answer, or a Refused naming why not; the route maps that to a status."""
from __future__ import annotations

import sys
from enum import Enum
from functools import partial
from typing import NamedTuple

from backend.config import get_settings
from backend.services import ai
from backend.services.dictionary import root_english, root_gloss, root_meaning, root_senses


class Refused(Enum):
    NO_BOOK = "the classical entries are not loaded"
    NO_ENTRY = "the book prints no entry under those letters"
    NO_REST = "the book prints nothing after the origin sense"
    NO_AI = "no model to ask and no English kept"
    EMPTY = "the model answered with nothing"
    MISPAIRED = "the model's lines do not match the Arabic lines"


class Retold(NamedTuple):
    english: str
    truncated: bool
    source: str  # a provenance key


class Lined(NamedTuple):
    lines: list[tuple[str, str]]  # (Arabic, English)
    truncated: bool
    source: str


class Worded(NamedTuple):
    senses: list[dict]  # each word with its own lines of the book
    truncated: bool
    source: str


def _book_entry(root: str) -> tuple[str, dict] | Refused:
    """(the spelling the book files it under, its entry). Readings are kept under the book's
    spelling: a reader who writes هدى reaches the same entry and English as the book's هدي."""
    if root_meaning.status() != root_meaning.READY:
        return Refused.NO_BOOK
    return root_meaning.book_root_of(root) or root, root_meaning.lookup(root) or {}


def english(root: str) -> Retold | Refused:
    """The entry retold, minus the opening sentence the card already prints as the origin sense
    (a one-sentence answer is kept whole). English made here, on the spot, is badged "ai" and never
    kept: kept, it would come back wearing the whole-book run's badge."""
    book = _book_entry(root)
    if isinstance(book, Refused):
        return book
    book_root, entry = book
    arabic = entry.get("body", "")
    if not arabic:
        return Refused.NO_ENTRY  # nothing to retell is not a failure of the model
    text, source = root_english.get(book_root), "maqayees_translation"
    if text is None:
        if not ai.is_ai_available():
            return Refused.NO_AI
        text, source = str(ai.explain_root_entry(root, arabic).get("english", "")).strip(), "ai"
        if not text:
            return Refused.EMPTY
    return Retold(
        text.removeprefix(root_gloss.opening_of(text)).lstrip() or text,
        len(arabic) > get_settings().root_entry_truncate_chars,
        source,
    )


def lines(root: str) -> Lined | Refused:
    """The rest of the entry, one English line under each Arabic line, paired here so the screen
    never lines them up itself. English kept for every line (the shipped run) is answered whole;
    only when none is kept is the opening cut to what the model can read, and asked for."""
    book = _book_entry(root)
    if isinstance(book, Refused):
        return book
    book_root, entry = book
    rest = root_gloss.rest_of(entry)
    every_line, _ = root_gloss.line_budget(rest, sys.maxsize)
    if not every_line:
        return Refused.NO_REST
    # Trusted only while it still matches the entry line for line: a changed book file makes
    # the kept English a mispairing.
    kept = root_english.get_lines(book_root, len(every_line))
    if kept is not None:
        shipped = root_english.shipped_lines(book_root, len(every_line))
        return Lined(list(zip(every_line, kept)), False, "maqayees_lines" if shipped else "ai")
    cut, truncated = root_gloss.line_budget(rest, get_settings().root_entry_truncate_chars)
    kept = root_english.get_lines(book_root, len(cut)) if truncated else None  # uncut is the entry already asked for
    if kept is None:
        if not ai.is_ai_available():
            return Refused.NO_AI
        made = ai.explain_root_entry_lines(root, cut, root_english.get(book_root)).get("lines")
        kept = [str(line).strip() for line in made] if isinstance(made, list) else []
        if len(kept) != len(cut) or not all(kept):
            return Refused.MISPAIRED  # English under the wrong Arabic is a false claim about the book
        root_english.put_lines(book_root, kept)
    return Lined(list(zip(cut, kept)), truncated, "ai")


def senses(root: str) -> Worded | Refused:
    """The rest of the entry cut into the words it explains, each beside its lines: the same rest, cut
    the same way, as `lines`. The model only says which lines go with which word and root_senses holds
    that against the book. Asked a chunk at a time, one after another, because at once a long entry's
    chunks spent the model service's tokens-per-minute together and failed."""
    book = _book_entry(root)
    if isinstance(book, Refused):
        return book
    book_root, entry = book
    rest = root_gloss.rest_of(entry)
    every_line, _ = root_gloss.line_budget(rest, sys.maxsize)
    if not every_line:
        return Refused.NO_REST
    kept = root_english.get_senses(book_root, len(every_line))
    if kept is not None:
        shipped = root_english.shipped_senses(book_root, len(every_line))
        return Worded(root_senses.shown(kept, every_line), False, "maqayees_senses" if shipped else "ai")
    cut, truncated = root_gloss.line_budget(rest, get_settings().root_entry_truncate_chars)
    kept = root_english.get_senses(book_root, len(cut)) if truncated else None
    if kept is None:
        if not ai.is_ai_available():
            return Refused.NO_AI
        ask = partial(ai.explain_root_entry_senses, root, reference=root_english.get(book_root))
        parts = []
        for chunk in root_gloss.chunks(cut, get_settings().root_senses_chunk_chars):
            parts.append(root_senses.cut(ask, chunk))
            if parts[-1] is None:
                break
        kept = root_senses.joined(parts)
        if kept is None:
            return Refused.MISPAIRED
        root_english.put_senses(book_root, kept)
    return Worded(root_senses.shown(kept, cut), truncated, "ai")
