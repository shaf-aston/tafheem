"""An Arabic word's dictionary form, from the app's own analyser (CAMeL).

One function so the index and the query agree: بالصبر and الصبر are صبر, and
the name صَبْرَة stays صبره rather than becoming patience. "" when the analyser
does not know the word; the written form still matches it then.
"""
from __future__ import annotations

from functools import lru_cache

from backend.services import morphology
from backend.services.hadith.words import fold


# Unbounded: the build meets each distinct written word (a few hundred thousand)
# and must analyse each once; a query adds only the words typed.
@lru_cache(maxsize=None)
def lemma(word: str) -> str:
    found = morphology.analyze_word(word)
    if found.get("engine") != "camel":
        return ""
    return fold(found.get("lemma") or "")
