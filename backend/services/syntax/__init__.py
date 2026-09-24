"""Roles for a typed sentence, worked out from the links between its words.

Two steps, each in its own file: `catib_onnx` draws the links (which word hangs
off which), `naming` turns a link into the word a nahw book uses. This file is
the seam the rest of the app talks to, so a different parser can be put behind
it without anything else changing.

The parser is preferred over `rule_engine` because it is measured better, and
this is the one place those numbers are written down: 81% of roles against the
book examples and 97% against the checked sentences, where the rule engine alone
gets 56% and 63% (`backend/scripts/score_iraab.py`). A word the
parser cannot name keeps the rule engine's answer, and if the parser is off or
fails, nothing changes at all.
"""
from __future__ import annotations

import logging

from backend.config import get_settings
from backend.services import provenance, rule_engine
from backend.services.arabic_text import words as split_words
from backend.services.syntax import tree
from backend.services.syntax.naming import role_key
from backend.services.syntax.naming import roles as name_roles

logger = logging.getLogger(__name__)


def read(sentence: str) -> dict:
    """One reading of a typed sentence: `roles` per word, and the `tree` they draw.

    Read once, used twice, so the cards and the picture can never disagree.
    Both come back empty when the parser is off or cannot manage the sentence.
    """
    typed = split_words(sentence)
    nothing = {"roles": [{"role": None, "case": None} for _ in typed], "tree": None}
    if not typed or not get_settings().catib_parser_enabled:
        return nothing
    try:
        from backend.services.syntax import catib_onnx

        tokens = catib_onnx.parse(typed)
        found = name_roles(typed, tokens)
        drawn = tree.build(typed, tokens, found)
        drawn["source"] = provenance.of("nahw")  # worked out here, not looked up
        return {"roles": found, "tree": drawn if tree.is_drawable(drawn) else None}
    except Exception as exc:  # a missing model file, or a sentence it chokes on
        logger.warning("Syntax parser unavailable, keeping the rule engine: %s", exc)
        return nothing


def with_parser_roles(rule_result: dict, parser_roles: list[dict]) -> dict:
    """The rule engine's answer with every role the parser could name written over it.

    Confidence is what the router uses to decide whether to ask an AI. A word the
    parser named needs no AI, so it counts as sure; the rest keep what the rules
    scored, which is already baked into the engine's own number.
    """
    entries = rule_result.get("words", [])
    if len(parser_roles) != len(entries) or not any(found["role"] for found in parser_roles):
        return rule_result
    named = 0
    for entry, found in zip(entries, parser_roles):
        if found["role"]:
            entry["role"] = found["role"]
            # the colour must follow the new name, never the one it replaced
            entry["role_key"] = role_key(found["role"])
            # the ending must not contradict the reader's own vowel, and a verb
            # or a particle is mabni rather than carrying a case
            if found["case"]:
                entry["case"] = found["case"]
            named += 1
    share = named / len(entries)
    confidence = round(share + (1 - share) * rule_result.get("confidence", 0.0), 2)
    summary = _sentence_type(parser_roles) or rule_result.get("summary")
    return {**rule_result, "words": entries, "summary": summary, "confidence": confidence}


def _sentence_type(parser_roles: list[dict]) -> str | None:
    """Verbal when a verb opens it. The words themselves are the rule engine's."""
    names = [found["role"] for found in parser_roles if found["role"]]
    if not names or (names[0] == "حرف" and "اسم إن" not in names):
        return None
    return rule_engine.sentence_type(is_verbal=names[0] == "فعل", is_inna="اسم إن" in names)
