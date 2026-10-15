"""Axis `voice`: active or passive, for a verb and the noun that stands for its doer."""
from __future__ import annotations

from backend.services.syntax.facts.word import is_participle, is_passive
from backend.services.syntax.facts.sentence import Sentence, verb_above

PASSIVE_PARTICIPLE = "مَ1ْ2ُو3"  # مَفْعُول: مفتوحٌ بابُه, its noun the نائب فاعل


def _voice(token: dict, s: Sentence) -> str:
    """Whether the verb the word hangs on (itself or through its noun) is active or
    passive: under a passive verb the subject is the deputy of the doer. A participle
    working as its verb does (كريمٌ أبوه، مفتوحٌ بابُه) counts as that verb. none where no
    verb is above the word."""
    verb = verb_above(token, s)
    if verb is None:
        head = s.head(token)
        if head and is_participle(head):
            return "passive" if head.get("pattern", "").removeprefix("ال").startswith(PASSIVE_PARTICIPLE) else "active"
        return "none"
    return "passive" if is_passive(verb) else "active"
