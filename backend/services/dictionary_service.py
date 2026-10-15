"""Arabic-English dictionary: indexed lookup by word, root or meaning.

Built from Wiktionary (CC BY-SA) by scripts/build_dictionary.py. Hans Wehr is
under copyright and is deliberately not shipped.
"""

from __future__ import annotations

import json
import logging
import re
import time
from functools import lru_cache
from pathlib import Path

from backend.config import get_settings
from backend.services import conjugation, spelling
from backend.services.arabic_text import bare_letters, normalize_root, strip_diacritics

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_DICTIONARY_JSON = _DATA_DIR / "arabic_dictionary.json"

_WORD_RE = re.compile(r"\b\w+\b")
_MIN_INDEX_WORD_LEN = 2


def folded(text: str) -> str:
    """The letters a search matches on (see _folded), for a caller comparing a result with what was typed."""
    return _folded(text)


def _folded(text: str) -> str:
    """The letters a search is matched on: marks gone, every hamza an alif.

    bare_letters already folds أ إ آ ٱ to ا, but Wiktionary files a root by its
    bare hamza, ءخذ, and no keyboard types that: أخذ and its seven root-mates
    were unreachable from the اخذ a reader actually types. For matching only,
    never for what is shown.
    """
    return bare_letters(text).replace("ء", "ا")

# Read once: the repeat-search cache is sized for the life of the process.
_CACHE_SIZE = get_settings().dictionary_cache_size

_dictionary: list[dict] = []
_arabic_index: dict[str, list[dict]] = {}
_english_index: dict[str, list[dict]] = {}
_loaded = False


def load_dictionary() -> None:
    """Read the JSON dictionary into memory and build the Arabic/English indices."""
    global _dictionary, _arabic_index, _english_index, _loaded
    if _loaded:
        return

    if not _DICTIONARY_JSON.exists():
        logger.warning("arabic_dictionary.json not found. Run scripts/build_dictionary.py")
        _loaded = True
        return

    with open(_DICTIONARY_JSON, encoding="utf-8") as f:
        _dictionary = json.load(f)

    # Wiktionary writes a root spaced out, "ف ه م". That is three letters read
    # aloud, not a word: it is what the entry shows, what the root chip carries,
    # and what the Define and In-the-Qur'an buttons search with, and no index
    # holds it. Folded once here, on the way in, so every reader of an entry
    # gets the same plain root and the index is keyed by it too.
    for entry in _dictionary:
        if root := entry.get("root"):
            entry["root"] = normalize_root(root)

    _arabic_index, _english_index = _build_indices(_dictionary)
    _loaded = True
    logger.info("Loaded %d dictionary entries", len(_dictionary))


def search_arabic(query: str, limit: int = 10) -> list[dict]:
    """Find entries by Arabic word, the word it is a form of, its root, or partial match (diacritic-insensitive)."""
    return search_arabic_read(query, limit)[0]


def search_arabic_read(query: str, limit: int = 10) -> tuple[list[dict], tuple[str, str] | None]:
    """search_arabic, and the (lemma, root) it was read as when the word as typed is no headword.

    مُنْتَصِرًا is in no dictionary; مُنْتَصِر may be, and its root نصر is. The
    reading is said, so the page can tell the reader which word it looked up.
    """
    load_dictionary()
    key = strip_diacritics(query.strip())
    if not key:
        return [], None
    started = time.perf_counter()
    entries, reading = _arabic_matches(query.strip(), limit)
    # A fresh list each time: the caller owns what it gets, the cache keeps its own.
    found = [_with_synonym_meanings(entry) for entry in entries]
    _log_timing("arabic", key, len(found), started)
    return found, reading


def search_english(query: str, limit: int = 10) -> list[dict]:
    """Find entries whose definitions contain the English keyword."""
    load_dictionary()
    keyword = query.strip().casefold()
    if not keyword:
        return []
    started = time.perf_counter()
    found = [_with_synonym_meanings(entry) for entry in _english_matches(keyword, limit)]
    _log_timing("english", keyword, len(found), started)
    return found


def meant(query: str, lang: str) -> str | None:
    """The indexed word a query that found nothing was likeliest meant to be (services/spelling.py), or None."""
    load_dictionary()
    typed = _folded(query.strip()) if lang == "ar" else query.strip().casefold()
    return _vocabulary(lang).nearest(typed)


@lru_cache(maxsize=2)
def _vocabulary(lang: str) -> spelling.Vocabulary:
    """Every indexed word, weighted by how common it is in everyday writing; built on the first slip."""
    return spelling.Vocabulary(spelling.everyday_weights(_arabic_index if lang == "ar" else _english_index, lang))


def _log_timing(side: str, key: str, results: int, started: float) -> None:
    """One line per search, kept permanently.

    The word itself is not logged, only how long it was: what is being watched
    is whether a short query is the slow one, and a study session's searches are
    nobody else's business.
    """
    logger.info(
        "dictionary search  side=%s  chars=%d  results=%d  %.1fms",
        side, len(key), results, (time.perf_counter() - started) * 1000,
    )


def meaning_of(word: str) -> str:
    """What one Arabic word means, in a few words; or "" if we cannot say.

    The first definition of the entry for that exact word. First because
    Wiktionary writes the commonest sense first, and one line is all a reader
    glancing at a synonym wants.

    Empty is a real answer and must stay one: about a fifth of the words listed
    as synonyms are phrases or names the dictionary has no entry for, and
    inventing something for them would turn a gap into a claim.
    """
    return next(iter(meanings_of(word)), "")


def meanings_of(word: str) -> list[str]:
    """Every definition of the entry for that exact word, commonest first; [] if none."""
    load_dictionary()
    if not (key := strip_diacritics(word.strip())):
        return []
    return next(
        (
            list(entry["definitions"])
            for entry in _arabic_index.get(key, ())
            if strip_diacritics(entry.get("arabic", "")) == key
            and entry.get("definitions")
        ),
        [],
    )


def verb_forms_of(word: str) -> list[dict]:
    """The "verbs" this entry's exact spelling carries, or [] if it has none.

    Same exact-word guard as meaning_of(), after conjugation.bare() has
    folded the joining alif: strip_diacritics alone left ٱ in place, so
    ٱجْتَمَعَ missed the entry stored as اِجْتَمَعَ. The index itself is keyed
    without shaddah (كتب holds كَتَبَ and كَتَّبَ together), so the shaddah
    bare() keeps is stripped again here and verb_forms._pick tells the two
    forms apart afterwards.
    """
    load_dictionary()
    if not (key := strip_diacritics(conjugation.bare(word.strip()))):
        return []
    return next(
        (
            entry.get("verbs") or []
            for entry in _arabic_index.get(key, ())
            if strip_diacritics(entry.get("arabic", "")) == key
        ),
        [],
    )


def _with_synonym_meanings(entry: dict) -> dict:
    """The entry as it goes out: each synonym carrying what it means.

    Worked out here rather than stored in arabic_dictionary.json, because it is
    already in the file twice over, the meaning of كَتَبَ is the entry for
    كَتَبَ. Writing it beside every mention would be the same words copied
    thousands of times, and stale the moment the dictionary is rebuilt.

    A copy, never a change in place: the entries are the loaded dictionary
    itself, shared by every search.
    """
    lists = entry.get("synonyms") or []
    if not any(lists):
        return entry
    return {
        **entry,
        "synonyms": [
            [{"word": word, "meaning": meaning_of(word)} for word in words]
            for words in lists
        ],
    }


def is_loaded() -> bool:
    """Whether the dictionary is *available*, which is not the same as read.

    backend/main.py reads the file while the server is starting, so by the time
    anyone can search it is already in memory; but a caller that reaches this
    before then, or a script that never runs the app's startup at all, would see
    an empty dictionary. Reporting the in-memory flag alone made the health check
    say "not installed" for a dictionary that was installed, and the panel showed
    a set-up notice to someone with nothing to set up.
    """
    return bool(_dictionary) or _DICTIONARY_JSON.exists()


# The same word is looked up again and again, from the Recent chips, from a root
# handed over by another tab, from simply searching twice. A second search cannot
# find anything a first did not, so it is not searched a second time.
#
def is_root(letters: str) -> bool:
    """Whether the dictionary files any entry under the root `letters`."""
    load_dictionary()
    key = _folded(letters)
    return bool(key) and any(_folded(entry.get("root") or "") == key for entry in _arabic_index.get(key, ()))


def headword_roots(word: str) -> list[str]:
    """The roots the headwords spelled like `word` are filed under; [] when it is no headword."""
    load_dictionary()
    key = _folded(strip_diacritics(word.strip()))
    return list(dict.fromkeys(entry["root"] for entry in _arabic_index.get(key, ())
                              if entry.get("root") and _folded(entry.get("arabic", "")) == key))


def _by_reading(word: str) -> tuple[list[dict], tuple[str, str] | None]:
    """Entries for the words `word` is a form of, then for their roots, likeliest reading first.

    The readings come from services/roots.py, the one place every tab asks for
    a root, so a word the grammar tabs can place is a word the dictionary finds.
    """
    from backend.services import roots as root_finder  # it asks this module back

    read = root_finder.readings(word)
    spelt = [lemma for lemma, _ in read]  # as written: آتى (give) before أتى (come), which fold alike
    lemmas: list[str] = []
    for lemma in spelt:
        if (folded := _folded(lemma)) not in lemmas:
            lemmas.append(folded)
    found = [entry for lemma in lemmas for entry in _arabic_index.get(lemma, ())]
    # The roots of the words found first, then the readings' own.
    roots = list(dict.fromkeys(r for e in found if (r := e.get("root") or "")))
    roots += [r for _, r in read if r and _folded(r) not in {_folded(x) for x in roots}]
    found += [entry for root in roots for entry in _arabic_index.get(_folded(root), ())]
    if not found:
        return [], None

    def rank(entry: dict) -> tuple[int, int]:
        word_itself = _folded(entry.get("arabic", ""))
        if word_itself in lemmas:  # the word it is a form of, likeliest first
            return lemmas.index(word_itself), strip_diacritics(entry.get("arabic", "")) not in spelt
        return len(lemmas) + (word_itself not in {_folded(r) for r in roots}), 0  # then the root's own verb

    ordered = sorted(_dedupe(found), key=rank)
    lead = ordered[0]
    shown = strip_diacritics(lead.get("arabic", "")) if rank(lead)[0] < len(lemmas) else ""
    return ordered, (shown, lead.get("root") or (roots[0] if roots else ""))


# Both fallbacks below test every key in the index and stop once they hold more
# candidates than the answer can use. A one-letter query matches thousands of
# keys, and collecting them all spent a fifth of a second choosing the same ten
# entries. The loops are written out rather than shared: passing the test in as a
# function costs a call on each of 26,000 keys, which measured slower than the
# duplication saves.
@lru_cache(maxsize=_CACHE_SIZE)
def _arabic_matches(typed: str, limit: int) -> tuple[tuple[dict, ...], tuple[str, str] | None]:
    # Looked up folded, so أخذ and اخذ are one search and both answer with the
    # whole أخذ family. Which spelling was typed decides the order, not what is
    # found: ranking below puts the word as written first.
    key = strip_diacritics(typed)
    folded = _folded(key)
    results = _arabic_index.get(folded)
    reading = None
    if not results:
        # Not a headword: the word it is a form of, before any word that merely
        # holds its letters. The typed vowels go along, they choose the reading.
        results, reading = _by_reading(typed)
        if results:
            return tuple(results[:limit]), reading
        settings = get_settings()
        ceiling, shortest = settings.dictionary_fuzzy_candidates, settings.dictionary_fuzzy_min_key
        results = []
        for index_key, entries in _arabic_index.items():
            # A shorter word is only a partial match when it is a word: every
            # single letter sits inside every query, which is how a search for
            # اخذ answered with alif, khaa and dhal before their own entries.
            if folded in index_key or (len(index_key) >= shortest and index_key in folded):
                results.extend(entries)
                if len(results) >= ceiling:
                    break
    # The word itself first, then everything else off its root. One key holds
    # both: كتب indexes the verb and the sixteen words built on it, and in the
    # index's own order the verb fell past the tenth, so a search for كتب
    # answered with أكتب and إكتاب and never showed the word that was typed.
    ordered = sorted(_dedupe(results), key=lambda e: (
        strip_diacritics(e.get("arabic", "")) != key, _folded(e.get("arabic", "")) != folded))
    return tuple(ordered[:limit]), reading


@lru_cache(maxsize=_CACHE_SIZE)
def _english_matches(keyword: str, limit: int) -> tuple[dict, ...]:
    # An exact hit is ranked in full, however many entries mention the word: the
    # entry the word is *about* can sit anywhere in that list, and cutting the
    # list short is how a search for "the" stopped finding ال.
    results = _english_index.get(keyword)
    if not results:
        ceiling = get_settings().dictionary_fuzzy_candidates
        results = []
        for index_key, entries in _english_index.items():
            if keyword in index_key:
                results.extend(entries)
                if len(results) >= ceiling:
                    break
    return tuple(sorted(_dedupe(results), key=lambda e: _english_rank(e, keyword))[:limit])


def _build_indices(entries: list[dict]) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    arabic: dict[str, list[dict]] = {}
    english: dict[str, list[dict]] = {}
    for entry in entries:
        for key in (entry.get("root", ""), entry.get("arabic", "")):
            # Under both spellings: as written, and folded, so أخذ and the
            # root ءخذ are both found by the plain اخذ a keyboard types.
            for normalized in {strip_diacritics(key), _folded(key)} - {""}:
                arabic.setdefault(normalized, []).append(entry)
        for definition in entry.get("definitions", []):
            for word in _WORD_RE.findall(definition.casefold()):
                if len(word) > _MIN_INDEX_WORD_LEN:
                    english.setdefault(word, []).append(entry)
    return arabic, english


def _english_rank(entry: dict, keyword: str) -> tuple[int, int]:
    """Best match first: the word a definition is *about* beats one that merely
    mentions it. A definition that is the keyword alone ranks above one where it
    is the tenth word of a long gloss."""
    for position, definition in enumerate(entry.get("definitions", [])):
        words = _WORD_RE.findall(definition.casefold())
        if keyword in words:
            return (position, words.index(keyword) + len(words))
    return (99, 999)


def _dedupe(entries: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for entry in entries:
        key = (entry.get("root", ""), entry.get("arabic", ""))
        if key not in seen:
            seen.add(key)
            out.append(entry)
    return out
