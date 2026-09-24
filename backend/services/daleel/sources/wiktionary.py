"""The Arabic-English dictionary, one passage per entry.

A dictionary entry is a quotation like any other: the word, and what the book
says it means. Included because a great many questions are answered by an entry
rather than by a verse, and leaving it out would send those questions to a
passage of the Qur'an that merely happens to contain the word.

The entry's root comes along, which is what lets a search for one word of a
family reach the rest of it.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from backend.services.arabic_text import normalize_root
from backend.services.daleel.model import Passage

_DICTIONARY = Path(__file__).resolve().parents[3] / "data" / "arabic_dictionary.json"


class WiktionarySource:
    """Every dictionary entry with a word and a meaning."""

    id = "wiktionary"

    def passages(self) -> Iterable[Passage]:
        if not _DICTIONARY.exists():
            return

        entries = json.loads(_DICTIONARY.read_text(encoding="utf-8"))
        for entry in entries:
            word = entry.get("arabic", "")
            definitions = [d for d in entry.get("definitions") or [] if d]
            if not word or not definitions:
                continue
            yield Passage(
                source="wiktionary",
                locator=word,
                arabic=word,
                english=" ".join(definitions),
                roots=normalize_root(entry.get("root") or ""),
            )
