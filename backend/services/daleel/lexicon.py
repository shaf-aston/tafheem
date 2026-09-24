"""The already-made mappings, fetched from the dictionary the app already has.

expand.py says *what* it wants looked up; this says *where* those answers come
from. Splitting them is what keeps the matching rules testable without the
23,715-entry dictionary, and keeps this file free of any rule about matching.

Nothing new is built here. The dictionary is already loaded once at startup and
already indexed both ways; this only asks it questions.

The caches are module level rather than per instance, so the answers survive
whichever object asks and a cache never holds an object alive.
"""
from __future__ import annotations

from functools import lru_cache

from backend.services import dictionary_service
from backend.services.arabic_text import bare_letters


@lru_cache(maxsize=2048)
def _root_of(word: str) -> str:
    for entry in dictionary_service.search_arabic(word, limit=1):
        return entry.get("root") or ""
    return ""


@lru_cache(maxsize=2048)
def _synonyms_of(word: str) -> tuple[str, ...]:
    out: list[str] = []
    for entry in dictionary_service.search_arabic(word, limit=1):
        # Synonyms are stored a list per sense, so a word with three senses has
        # three lists. Flattened here: Daleel is looking for the passage, it is
        # not deciding which sense was meant.
        for sense in entry.get("synonyms") or []:
            for synonym in sense or []:
                text = synonym if isinstance(synonym, str) else synonym.get("word", "")
                if text and text not in out:
                    out.append(text)
    return tuple(out)


@lru_cache(maxsize=2048)
def _arabic_for(english_word: str) -> tuple[str, ...]:
    out: list[str] = []
    for entry in dictionary_service.search_english(english_word, limit=8):
        arabic = bare_letters(entry.get("arabic") or "")
        if arabic and arabic not in out:
            out.append(arabic)
    return tuple(out)


class DictionaryLexicon:
    """Roots, synonyms and the English bridge, straight from the dictionary."""

    def root_of(self, word: str) -> str:
        return _root_of(word)

    def synonyms_of(self, word: str) -> tuple[str, ...]:
        return _synonyms_of(word)

    def arabic_for(self, english_word: str) -> tuple[str, ...]:
        return _arabic_for(english_word)
