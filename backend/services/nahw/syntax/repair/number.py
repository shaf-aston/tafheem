"""Repair: the two words of a compound number (11 to 19) are one number."""
from __future__ import annotations

from backend.services.nahw.syntax.facts import listed, typed_tanween


def compound_number(bases: list[dict]) -> None:
    """ثَلَاثَةَ عَشَرَ طَالِبًا، أَحَدَ عَشَرَ كَوْكَبًا: a unit and the عشر typed after it are one number, built on the
    fatha of both parts, with the one place the sentence gives it (closed_words compound_number). The عشر hangs on
    the unit, so the number's place is decided once, on the unit; the fatha typed on either is its build, no nasb.
    اثنا عشر is the exception: its اثنا is ملحق بالمثنى and inflects by its letters, only the عشر is built."""
    for unit, ten in zip(bases, bases[1:]):
        # ثلاثةٌ وعشرةٌ: a و between, or a tanween on the unit, makes two numbers, never one
        if ten["id"] != unit["id"] + 1 or typed_tanween(unit) or not listed(ten, "compound_number", "second"):
            continue
        part = next((part for part, kind in _UNITS if listed(unit, "compound_number", kind)), None)
        if part is None:
            continue
        unit["compound"], ten["compound"] = part, "second"
        if unit["head"] == ten["id"]:  # the parser hung the unit on the عشر: the unit takes the عشر's place
            unit["head"], unit["rel"] = ten["head"], ten["rel"]
        ten["head"], ten["rel"] = unit["id"], "IDF"
        for kid in bases:  # what the parser hung on the عشر (the counted noun) is the number's
            if kid["head"] == ten["id"] and kid is not ten:
                kid["head"] = unit["id"]


# a unit's list in closed_words compound_number, and the part it plays: a cardinal or an ordinal (الحادي عشر,
# its noun's صفة) is built on both fathas, اثنا is ملحق بالمثنى
_UNITS = (("built", "words"), ("ordinal", "ordinals"), ("dual", "dual"))
