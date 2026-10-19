"""Roles for a typed sentence, worked out from the links between its words.

Four steps, each in its own file: `catib_onnx` draws the links, `correct` is the one
place they and the words' kinds are corrected, `naming` turns a link into the word a nahw
book uses, and `teacher` re-reads the finished sentence and dashes any word whose name breaks a rule. This file is
the seam the rest of the app talks to, so a different parser can be put behind
it without anything else changing.

If the parser is off or fails, every role comes back empty and each card
says only what its word is, with no job (iraab.cards).
"""
from __future__ import annotations

import json
import logging
from contextlib import suppress

from backend.config import get_settings
from backend.services import provenance
from backend.services.arabic_text import words as split_words
from backend.services.syntax import teacher, tree
from backend.services.syntax.repair import correct
from backend.services.syntax.naming import NAMED, roles as name_roles
from backend.services.harakat import CASE_NAME

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


def _link(token: dict) -> dict:
    """A token as show_parse prints it: its link and the features the rules read."""
    keep = ("id", "form", "lemma", "pos", "pos_camel", "head", "rel", "stt", "cas", "typed", "token_type", "diac")
    return {key: token[key] for key in keep if key in token}


def _as_json(parse: dict) -> dict | None:
    """The parse as plain JSON, or None: a value the answer cannot carry would turn the
    whole reply into a server error, and the parse is only a debugging aid."""
    try:
        return json.loads(json.dumps(parse, ensure_ascii=False, allow_nan=False))
    except (TypeError, ValueError):
        logger.exception("show_parse: the parse would not go into JSON, left out")
        return None


def read(sentence: str, picks: list[dict]) -> dict:
    """One reading of a typed sentence: `roles` per word, and the `tree` they draw.
    `picks`: one reading per word (morphology.pick), shared with the cards.
    Read once, used twice, so the cards and the picture can never disagree.
    Both come back empty when the parser is off or cannot manage the sentence;
    `failed` then says it broke, so a crash is not mistaken for words it cannot name.
    """
    typed = split_words(sentence)
    nothing = {"roles": [{"role": None, "case": None} for _ in typed], "tree": None}
    if not typed or not get_settings().catib_parser_enabled:
        return nothing
    try:
        from backend.services.syntax import catib_onnx

        tokens = catib_onnx.parse(typed, picks)
        before = [_link(t) for t in tokens]
        correct(typed, tokens)
        found = teacher.review(typed, tokens, name_roles(typed, tokens))
        drawn = tree.build(typed, tokens, found)
        # شكرًا is the object of an understood verb: the card says the job the picture
        # gives it. Only that; a picture's unit name (مضاف, اسم موصول) is not a job.
        for word, job in zip(found, drawn.pop("unsaid", [])):
            if job and not word["role"]:
                word["role"] = job
                word.pop("gap", None)
        # the card says the same finer name the picture prints, read off the one tree
        for word, finer in zip(found, drawn.pop("finer", [])):
            if finer and word["role"]:
                word["name"] = finer
        # and the doer drawn inside a verb (ضمير مستتر تقديره هو), so its card says the same
        for word, doer in zip(found, drawn.pop("doer", [])):
            if doer and word["role"]:
                word["doer"] = doer
        for word, ma in zip(found, drawn.pop("ma", [])):
            if ma:
                job, case = ma
                word.update(role=job or NAMED.harf, case=CASE_NAME[case] if case else None, built=bool(job))
                if not job:
                    word["named"] = tree.FRAMES["masdar"]["named_by_word"]["ما"]
                word.pop("gap", None)
        drawn["source"] = provenance.of("nahw")  # worked out here, not looked up
        read = {"roles": found, "tree": drawn if tree.is_drawable(drawn) else None}
        if get_settings().show_parse:
            read["parse"] = _as_json({"parsed": before, "repaired": [_link(t) for t in tokens]})
        return read
    except Exception:  # a missing model file, or a sentence it chokes on
        logger.exception("Syntax parser unavailable, every word left unnamed")
        return {**nothing, "failed": True}
