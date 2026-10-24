"""Axis `voice`: active or passive, for a verb and the noun that stands for its doer."""
from __future__ import annotations

from backend.services.nahw.syntax.facts.word import works_as_verb
from backend.services.nahw.syntax.facts.sentence import Sentence, verb_above


def _voice(token: dict, s: Sentence) -> str:
    """Whether the verb the word hangs on (itself or through its noun) is active or
    passive: under a passive verb the subject is the deputy of the doer. A participle
    working as its verb does (كريمٌ أبوه، مفتوحٌ بابُه) counts as that verb. none where no
    verb is above the word."""
    worker = verb_above(token, s) or s.head(token)
    return (worker and works_as_verb(worker)) or "none"
