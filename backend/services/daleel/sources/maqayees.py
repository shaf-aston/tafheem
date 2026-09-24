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
from pathlib import Path
from typing import Iterable

from backend.services.arabic_text import normalize_root
from backend.services.daleel.model import Passage

_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "maqayees"
_ROOTS = _DATA_DIR / "roots.json"
_ENGLISH = _DATA_DIR / "english_entries.json"


class MaqayeesSource:
    """Every root the book has an entry for."""

    id = "maqayees"

    def passages(self) -> Iterable[Passage]:
        if not _ROOTS.exists():
            return

        roots = json.loads(_ROOTS.read_text(encoding="utf-8"))
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
    if not _ENGLISH.exists():
        return {}
    raw = json.loads(_ENGLISH.read_text(encoding="utf-8"))
    return {
        root: (value if isinstance(value, str) else value.get("english", ""))
        for root, value in raw.items()
    }
