"""Repair: the two words of a compound number (11 to 19) are one number."""
from __future__ import annotations

from backend.services.nahw.syntax.facts import listed


def compound_number(bases: list[dict]) -> None:
    """ثَلَاثَةَ عَشَرَ طَالِبًا، أَحَدَ عَشَرَ كَوْكَبًا: a unit and the عشر typed after it are one number, built on the
    fatha of both parts, with the one place the sentence gives it (closed_words compound_number). The عشر hangs on
    the unit, so the number's place is decided once, on the unit; the fatha typed on either is its build, no nasb.
    اثنا عشر is the exception: its اثنا is ملحق بالمثنى and inflects by its letters, only the عشر is built."""
    for unit, ten in zip(bases, bases[1:]):
        if not listed(ten, "compound_number", "second"):
            continue
        if listed(unit, "compound_number"):
            unit["compound"] = "built"
        elif listed(unit, "compound_number", "dual"):
            unit["compound"] = "dual"
        else:
            continue
        ten["compound"] = "second"
        ten["head"], ten["rel"] = unit["id"], "IDF"
        for kid in bases:  # what the parser hung on the عشر (the counted noun) is the number's
            if kid["head"] == ten["id"]:
                kid["head"] = unit["id"]
