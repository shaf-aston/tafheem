"""The English name of a book whose own name is Arabic.

The only reader of data/books/english-titles.json. Kept apart from the source
adapters on purpose: the books needing an English name arrive from three
different places with three different manifest shapes, and an English name is
one idea, so it is answered in one place rather than added to each of them.

Empty is a real answer and stays one. A book already named in English has no
entry, and neither does one nobody has written a name for yet; the picker shows
what it has rather than transliterating a guess.
"""
from __future__ import annotations

import json
from functools import cache
from pathlib import Path

_FILE = Path(__file__).resolve().parents[2] / "data" / "books" / "english-titles.json"


@cache
def _titles() -> dict[str, str]:
    """Read once. The file is sixteen lines and never changes while serving."""
    if not _FILE.exists():
        return {}
    with _FILE.open(encoding="utf-8") as handle:
        return json.load(handle).get("titles", {})


def english_of(name: str) -> str:
    """This book in English letters, or "" if it has no English name."""
    return _titles().get(name, "")
