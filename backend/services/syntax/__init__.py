"""Roles for a typed sentence, worked out from the links between its words.

Three steps, each in its own file: `catib_onnx` draws the links (which word hangs
off which), `naming` turns a link into the word a nahw book uses, and `teacher`
re-reads the finished sentence and dashes any word whose name breaks a rule. This file is
the seam the rest of the app talks to, so a different parser can be put behind
it without anything else changing.

If the parser is off or fails, every role comes back empty and each card
says only what its word is, with no job (iraab.cards).
"""
from __future__ import annotations

import logging
from contextlib import suppress

from backend.config import get_settings
from backend.services import provenance
from backend.services.arabic_text import words as split_words
from backend.services.syntax import teacher, tree
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


def disambiguator():
    """The parser's BERT, loaded now, to rank readings (morphology.pick); None when the
    parser is off or did not load (catib_onnx.warm logged why), so the cards fall back to the MLE."""
    with suppress(Exception):
        warm()
    from backend.services.syntax import catib_onnx

    return catib_onnx.disambiguator() if status() == "ready" else None


def read(sentence: str, picks: list[dict]) -> dict:
    """One reading of a typed sentence: `roles` per word, and the `tree` they draw.
    `picks`: one reading per word (morphology.pick), shared with the cards.
    Read once, used twice, so the cards and the picture can never disagree.
    Both come back empty when the parser is off or cannot manage the sentence.
    """
    typed = split_words(sentence)
    nothing = {"roles": [{"role": None, "case": None} for _ in typed], "tree": None}
    if not typed or not get_settings().catib_parser_enabled:
        return nothing
    try:
        from backend.services.syntax import catib_onnx

        tokens = catib_onnx.parse(typed, picks)
        found = teacher.review(typed, tokens, name_roles(typed, tokens))
        drawn = tree.build(typed, tokens, found)
        # a word with no job of its own is called by what the picture calls it (مَنْ heading
        # its صلة is the اسم موصول; شكرًا is the object of an understood verb), so its card
        # says the same and never guesses apart
        for word, name in zip(found, drawn.pop("printed", [])):
            if not word["role"] and name:
                word["role"] = name
                word.pop("gap", None)
        drawn["source"] = provenance.of("nahw")  # worked out here, not looked up
        return {"roles": found, "tree": drawn if tree.is_drawable(drawn) else None}
    except Exception:  # a missing model file, or a sentence it chokes on
        logger.exception("Syntax parser unavailable, every word left unnamed")
        return nothing
