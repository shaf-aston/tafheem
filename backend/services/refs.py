"""The rules for a reference (a Qur'an ayah, a hadith or a book), shared by Timelines and Dawah.

The only reader of data/timelines/library.json, which declares the collections
a reference may name. A reference is checked when its file loads, so an ayah past
the end of its surah or a collection nobody declared stops the app and names it.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from backend.config import data_path

SURAHS = 114
# "12", "2:255" or "2:30-37". A range never crosses a surah.
QURAN_REF = re.compile(r"^(\d+)(?::(\d+)(?:-(\d+))?)?$")


def _quran_faults(ref: str, ayahs: dict[int, int]) -> list[str]:
    """What is wrong with one Qur'an reference. Bounds are skipped when counts are unknown."""
    match = QURAN_REF.match(ref)
    if not match:
        return [f"Qur'an reference {ref!r} is not S, S:A or S:A-B"]
    surah, first, last = (int(n) if n else None for n in match.groups())
    if not 1 <= surah <= SURAHS:
        return [f"Qur'an reference {ref!r} names surah {surah}, which does not exist"]
    if first is None:
        return []
    last = last or first
    if first < 1 or last < first:
        return [f"Qur'an reference {ref!r} runs backwards or from zero"]
    if ayahs and last > ayahs[surah]:
        return [f"Qur'an reference {ref!r} passes the end of surah {surah} ({ayahs[surah]} ayahs)"]
    return []


def refs_faults(refs: list[dict], collections: dict, ayahs: dict[int, int]) -> list[str]:
    """Each reference sound, and none given twice: a repeat prints two identical pills."""
    said = [why for ref in refs for why in ref_faults(ref, collections, ayahs)]
    keys = [json.dumps(ref, sort_keys=True) for ref in refs]
    said += [f"reference {k} is given twice" for k in sorted({k for k in keys if keys.count(k) > 1})]
    return said


def ref_faults(ref: dict, collections: dict, ayahs: dict[int, int]) -> list[str]:
    kinds = [k for k in ("quran", "hadith", "book") if ref.get(k) is not None]
    if len(kinds) != 1:
        return [f"reference {ref} must name exactly one of quran, hadith or book"]
    if kinds[0] == "quran":
        return _quran_faults(ref["quran"], ayahs)
    key = ref[kinds[0]]
    if collections.get(key, {}).get("kind") != kinds[0]:
        return [f"reference names {kinds[0]} {key!r}, which library.json does not declare as one"]
    if kinds[0] == "hadith" and not isinstance(ref.get("number"), int):
        return [f"hadith reference to {key!r} has no number"]
    # sunnah.com letters the narrations that share one reference number. One
    # letter, lower case: anything else would build a link to a page that is not
    # there and look up words under a key nothing wrote.
    if ref.get("part") is not None and not re.fullmatch(r"[a-z]", str(ref["part"])):
        return [f"reference to {key!r} {ref.get('number')} has part {ref['part']!r}, which is not a single letter a-z"]
    # A number said to be checked has to be reachable, or the reader is asked to
    # take it on trust with the caution taken away and nothing put in its place.
    if ref.get("checked") and not collections[key].get("cite"):
        return [f"reference to {key!r} says its number is checked, but library.json gives it no cite link"]
    # A page link needs its page, and a page needs a link to fill.
    if (ref.get("page") is not None) != ("{page}" in collections[key].get("cite", "")):
        return [f"reference to {key!r} and its library.json cite link disagree on whether it has a page"]
    return []


@lru_cache(maxsize=1)
def declared() -> dict:
    library = json.loads((data_path("timelines_dir") / "library.json").read_text(encoding="utf-8"))
    library.pop("_about", None)
    return library


def collections() -> dict:
    """The hadith collections references may name; other tabs cite through these."""
    return declared()["collections"]
