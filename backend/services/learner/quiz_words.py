"""Which items a quiz answer may name: the quiz's own word list, the one the page asks from
(frontend/public/words/words.json, its `meaningKey`s).

The page grades its own answers, by design (docs/plans/2026-11-11-security.md §3 T9), so "words learnt",
the ranking's measure, would otherwise count whatever ids a script made up. Held to the real list, the
most anyone can claim is the list itself, and each word still has to be answered into the review schedule
(services/learner/review_schedule.is_known).

Only the quiz modules ("quiz", and "quiz:<language>" for its other languages: frontend
lib/quiz/quizBanks.js moduleFor) are checked: they are what the rankings are read in. The other panels'
answers earn XP, which is the learner's own and ranks nothing.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

QUIZ = "quiz"
# The same file services/learner/sentence_check.py reads (not imported from there: that loads the analyser).
WORDS = Path(__file__).resolve().parents[3] / "frontend" / "public" / "words" / "words.json"


def checked(module: str) -> bool:
    """Whether this module's items must be quiz words."""
    return module == QUIZ or module.startswith(QUIZ + ":")


@lru_cache(maxsize=1)
def _keys() -> frozenset[str] | None:
    """The quiz's meaningKeys, read once. None when the list is not on this machine: then nothing is refused,
    because refusing every answer is a worse failure than an unchecked ranking."""
    try:
        words = json.loads(WORDS.read_text(encoding="utf-8"))["words"]
        return frozenset(word["meaningKey"] for word in words if word.get("meaningKey"))
    except (OSError, ValueError, KeyError, TypeError):
        logger.warning("quiz word list unreadable at %s: quiz answers are not checked", WORDS)
        return None


def allowed(module: str, item: str) -> bool:
    """Whether an answer about `item` may be filed (and counted) under `module`."""
    if not checked(module):
        return True
    keys = _keys()
    return keys is None or item in keys
