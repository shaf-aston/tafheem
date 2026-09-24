"""Al-Muqaddimah al-Jazariyyah, the tajweed poem, one bayt per passage.

The only book of recitation the app holds, and until now the only book it held
that Daleel could not reach: a reader asking how to pronounce a letter was sent
to a grammar book, because the book that answers that question was not in the
index.

One bayt is one passage. A bayt is a single printed line split into two halves,
the sadr read first and the ajuz second, and the pair is what a person memorises
and what they cite. Splitting them into two passages would return half a
sentence; joining them is the line as the page has it.

The file lives in frontend/public because the Memorise tab fetches it straight
from the browser with no backend in the way, and its README tells the reader to
edit it there. It is read here rather than copied so there is still exactly one
copy of the poem; two would drift the first time a verse was corrected. Read
once at index build time, never while a search is being answered, the same
crossing backend/scripts/export_quiz_words.py already makes in the other
direction.

The English is ours, not the poet's and not a translator's: a short gloss of
what each verse says, written from the Arabic alone. It is carried so an English
question can reach the verse at all, and data/sources.json says on the badge
exactly what it is, so nobody mistakes it for a translation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from backend.services.daleel.model import Passage
from backend.services.daleel.sources.roots import roots_in

_POEM = (
    Path(__file__).resolve().parents[4]
    / "frontend" / "public" / "jazariyya" / "poem.json"
)


class JazariyyaSource:
    """Every bayt of the poem that has both of its halves."""

    id = "jazariyya"

    def passages(self) -> Iterable[Passage]:
        if not _POEM.exists():
            return

        poem = json.loads(_POEM.read_text(encoding="utf-8"))
        for bayt in poem.get("bayt", []):
            # Both halves or none. A line missing one of them is a line the
            # scan lost, and half a verse of poetry quoted as a whole one is
            # worse than not offering it.
            sadr, ajuz = bayt.get("sadr", ""), bayt.get("ajuz", "")
            if not sadr or not ajuz:
                continue
            line = f"{sadr} {ajuz}"
            yield Passage(
                source="jazariyya",
                locator=f"Bayt {bayt.get('n', '')}".strip(),
                arabic=line,
                english=bayt.get("english", ""),
                roots=roots_in(line.split()),
            )
