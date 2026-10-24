"""Ibn Faris's Maqayees al-Lugha, one passage per root.

The whole entry is quoted, not the opening sense. Ibn Faris often states what a
root means several lines in, so an index built from the first sentence would
miss the sentence a reader is actually looking for.

The English beside it is the app's own translation of that entry where one has
been made. It is filed under this source rather than a separate one because it
is here only to be searched against; what gets shown is the book's Arabic.
"""
from __future__ import annotations

import json
from typing import Iterable

from backend.config import data_path
from backend.services.text.arabic_text import normalize_root
from backend.services.daleel.sources.model import Passage
from backend.services.dictionary.root_english import STORE_FILE


class MaqayeesSource:
    """Every root the book has an entry for."""

    id = "maqayees"

    def passages(self) -> Iterable[Passage]:
        roots_file = data_path("root_meaning_path")
        if not roots_file.exists():
            return

        roots = json.loads(roots_file.read_text(encoding="utf-8"))
        english = _english()

        for root, entry in roots.items():
            body = entry.get("body") or entry.get("core_meaning") or ""
            if not body:
                continue
            key = normalize_root(root)
            yield Passage(
                source="maqayees",
                locator=root,
                arabic=body,
                english=english.get(root, ""),
                roots=key,
            )


def _english() -> dict[str, str]:
    """The translated entries, keyed the same way as the book's own."""
    if not STORE_FILE.exists():
        return {}
    raw = json.loads(STORE_FILE.read_text(encoding="utf-8"))
    return {
        root: (value if isinstance(value, str) else value.get("english", ""))
        for root, value in raw.items()
    }
