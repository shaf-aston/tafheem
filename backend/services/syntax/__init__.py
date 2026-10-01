"""Roles for a typed sentence, worked out from the links between its words.

Three steps, each in its own file: `catib_onnx` draws the links (which word hangs
off which), `naming` turns a link into the word a nahw book uses, and `teacher`
re-reads the finished sentence and dashes any word whose name breaks a rule. This file is
the seam the rest of the app talks to, so a different parser can be put behind
it without anything else changing.

The parser is preferred over `rule_engine` because it is measured better
(`backend/scripts/score_iraab.py` holds the scores). A word the
parser has no name for keeps the rule engine's answer; a word the teacher dashed
stays dashed, with its reason. If the parser is off or
fails, nothing changes at all.
"""
from __future__ import annotations

import logging

from backend.config import get_settings
from backend.services import provenance, rule_engine
from backend.services.arabic_text import words as split_words
from backend.services.nahw_book import reason
from backend.services.syntax import teacher, tree
from backend.services.tarkeeb import term_ar
from backend.services.syntax.naming import opens_with_verb, role_key
from backend.services.syntax.naming import roles as name_roles

logger = logging.getLogger(__name__)


def status() -> str:
    """"off", "missing files", "not loaded", "loading", "ready" or "failed: <why>",
    for /api/health: no silent absence, and no "ready" for a parser that is not."""
    if not get_settings().catib_parser_enabled:
        return "off"
    from backend.services.syntax import catib_onnx

    return catib_onnx.state() if catib_onnx.files_present() else "missing files"


def warm() -> None:
    """Load the parser now rather than on the first sentence typed. Does
    nothing when it is off or its files are absent, as read() would."""
    if status() in ("off", "missing files"):
        return
    from backend.services.syntax import catib_onnx

    catib_onnx.warm()


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
        found = teacher.review(typed, tokens, name_roles(typed, tokens))
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
    if len(parser_roles) != len(entries) or not any(found["role"] or found.get("gap") for found in parser_roles):
        return rule_result
    named = 0
    for entry, found in zip(entries, parser_roles):
        if not found["role"] and not found.get("gap") and (
                why := teacher.fallback_gap(entry.get("role"), found)):
            found = {**found, "gap": why}  # the rule engine's name clashes with the typed vowel
        if found.get("gap"):
            # the teacher caught the parser's name breaking a rule; the rule engine's
            # guess must not stand in for it, so the card shows the no-role dash and why
            entry.update(role="–", role_key=None, case=found["case"], sign=None,
                         reason=found["gap"]["ar"], notes=found["gap"]["en"])
        elif found["role"]:
            renamed = found["role"] != entry.get("role")
            entry["role"] = found["role"]
            # the colour must follow the new name, never the one it replaced
            entry["role_key"] = role_key(found["role"])
            moved = found["case"] and found["case"] != entry.get("case")
            if found["role"] == "فعل":
                # a word CAMeL took for a noun (ضُرِبَ، كان) or a mood the particle before
                # settled (لن يذهب): the card is the verb's own, by the parser's tense
                if entry.get("type") != "fi'l" or moved:
                    aspect = found.get("aspect") or ("i" if found["case"] != "mabni" else None)
                    entry.update(type="fi'l", **rule_engine.verb_card(entry["word"], aspect, found["case"]))
            else:
                if renamed:
                    entry["reason"] = reason(found["role"])  # the reason must explain the new name
                if moved:
                    # the sign must show the new case, never the one it replaced
                    entry.update(case=found["case"], sign=rule_engine.sign(found["case"]))
                if entry["case"] == "mabni" and entry.get("type") != "harf":
                    entry["reason"] = reason(found["role"], mabni=True)  # الذي، هذا: in the place of a case
            named += 1
    share = named / len(entries)
    confidence = round(share + (1 - share) * rule_result.get("confidence", 0.0), 2)
    summary = _sentence_type(parser_roles) or rule_result.get("summary")
    return {**rule_result, "words": entries, "summary": summary, "confidence": confidence}


def _sentence_type(parser_roles: list[dict]) -> str | None:
    """The type the parser's names give, or None when it named nothing."""
    names = [found["role"] for found in parser_roles if found["role"]]
    if not names:
        return None
    if "منادى" in names and not opens_with_verb(names):
        return term_ar("jumlah_nidaiyyah")  # يا عبدَ الله: a call, the same words the tree uses
    return rule_engine.sentence_type(is_verbal=opens_with_verb(names), is_inna="اسم إن" in names)
