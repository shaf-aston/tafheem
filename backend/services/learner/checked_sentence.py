"""A short AI sentence using only words this learner has learnt, every word checked by sentence_check.
Returns the sentence with the words it was asked to use, or a Refused naming why not."""
from __future__ import annotations

import random
from enum import Enum

from backend.config import get_settings
from backend.services import ai
from backend.services.learner import attempts, sentence_check


class Refused(Enum):
    TOO_FEW = "too few learnt words"
    NO_AI = "no model to ask"
    FAILED = "no sentence passed the check"


def make(user: str) -> dict | Refused:
    settings = get_settings()
    words = sentence_check.learnt_words([row for row in attempts.summary("quiz", user) if row["known"]])
    if len(words) < settings.sentence_min_learnt:
        return Refused.TOO_FEW
    if not ai.is_ai_available():
        return Refused.NO_AI
    allowed = sentence_check.allowed(words)
    given = random.sample([word["ar"] for word in words], min(len(words), settings.sentence_prompt_words))
    made = ai.checked_sentence(given, lambda ar: not sentence_check.check(ar, allowed))
    return Refused.FAILED if made is None else {**made, "words": given}
