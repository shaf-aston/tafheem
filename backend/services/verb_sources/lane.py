"""Lane's Lexicon's stated Form I babs, read from the file build_lane_verbs.py built.

data/sarf/lane_verbs.json: bare past -> [{form: "I", past, babs: [codes]}], the
same shape Wiktionary's dictionary entries carry their verbs in. Loaded once
and kept in memory; the file is rebuilt offline by
`python -m backend.scripts.build_lane_verbs`, never touched at request time.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.services import conjugation

_LANE_VERBS = Path(__file__).parent.parent.parent / "data" / "sarf" / "lane_verbs.json"


@lru_cache(maxsize=1)
def _verbs() -> dict:
    with open(_LANE_VERBS, encoding="utf-8") as handle:
        return json.load(handle)


def verb_forms_of(word: str) -> list[dict]:
    """Every Form I verb Lane states for this word's bare spelling, or [].

    Contract every source in this package keeps (README.md here): every verb
    form filed under the typed word's letters.
    """
    return _verbs().get(conjugation.bare(word), [])
