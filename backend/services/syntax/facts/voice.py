"""Axis `voice`: active or passive, for a verb and the noun that stands for its doer."""
from __future__ import annotations

from backend.services.syntax.facts.word import is_passive
from backend.services.syntax.facts.sentence import Sentence, verb_above


def _voice(token: dict, s: Sentence) -> str:
    """Whether the verb the word hangs on (itself or through its noun) is active or
    passive: under a passive verb the subject is the deputy of the doer. none where no
    verb is above the word."""
    verb = verb_above(token, s)
    return "none" if verb is None else "passive" if is_passive(verb) else "active"
