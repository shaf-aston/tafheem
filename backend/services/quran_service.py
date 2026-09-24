"""Quranic ayah lookup, word by word.

Two sources, each doing the thing it is actually good at:

  Grammar comes from the hand-tagged corpus (quran_corpus), offline and exact.
  English comes from api.quran.com, free, no key; and is cached on disk, so an
  ayah you have already opened works with no network at all.

This used to run a general-purpose Arabic tagger over Qur'anic spelling and print
whatever came back. That was wrong often enough to mislead a learner, so it is
gone; if the corpus has nothing for a word, the word says so rather than guessing.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx

from backend.config import get_settings
from backend.services import quran_corpus, quran_layout, quran_meanings

logger = logging.getLogger(__name__)

API = "https://api.quran.com/api/v4"
_CACHE_DIR = Path(__file__).parent.parent / "data" / "quran_cache"


def _cached(name: str) -> Path:
    return _CACHE_DIR / f"{name}.json"


def _get(path: str, cache_as: str | None = None) -> dict:
    """One API call, cached on disk when it is an ayah we may want offline."""
    if cache_as and (file := _cached(cache_as)).exists():
        return json.loads(file.read_text(encoding="utf-8"))

    response = httpx.get(f"{API}{path}", timeout=get_settings().quran_timeout_seconds)
    response.raise_for_status()
    payload = response.json()

    if cache_as:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cached(cache_as).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def _translations(surah: int, ayah: int) -> dict[int, str]:
    """Word-by-word English, keyed by word number. Empty if the network is down, 
    the grammar is offline and still worth showing without it."""
    # The local build, when it exists, is the whole point: it answers in under a
    # millisecond and never needs the network. Falling through to the API keeps
    # the app working for anyone who has not run the build script.
    if local := quran_meanings.for_ayah(surah, ayah):
        return local

    try:
        payload = _get(f"/verses/by_key/{surah}:{ayah}?words=true", cache_as=f"{surah}-{ayah}")
    except (httpx.HTTPError, OSError) as exc:
        logger.info("No word-by-word English for %s:%s (%s)", surah, ayah, exc)
        return {}

    english: dict[int, str] = {
        word.get("position", 0): (word.get("translation") or {}).get(
            "text", ""
        )
        for word in payload.get("verse", {}).get("words", [])
        if word.get("char_type_name") == "word"
    }
    return english


def get_ayah(surah: int, ayah: int) -> dict | None:
    """One ayah's word rows plus its printed end-marker, or None if there is no
    such ayah. Uthmani spelling and the end mark come from the same local build
    as the English; a build that predates them just leaves those fields blank."""
    words = quran_corpus.words_for_ayah(surah, ayah)
    if not words:
        return None

    english = _translations(surah, ayah)
    uthmani = quran_meanings.uthmani_for_ayah(surah, ayah)
    for index, word in enumerate(words, start=1):
        word["meaning"] = english.get(index, "")
        word["uthmani"] = uthmani.get(index, "") or None
    return {"words": words, "end_mark": quran_meanings.ayah_end_mark(surah, ayah)}


def get_surah(surah: int, with_words: bool = False) -> dict | None:
    """A whole surah in one go, or None if there is no such surah.

    Two local queries, whatever the surah's length, the grammar in one, the
    English in another, instead of one round trip per ayah. That is what makes
    reading al-Baqarah's 286 ayahs the same cost as reading al-Fatiha's seven.

    `with_words` is the difference between reading and studying. Reading wants the
    text and nothing else; the segment-by-segment grammar is roughly fifty times
    the payload and is only fetched for the ayah actually being examined.
    """
    # Reading takes the cheap query; only studying pays for the grammar.
    ayahs: list[tuple[int, list[dict] | None, str]]
    if with_words:
        ayahs = [
            (number, words, " ".join(word["arabic"] for word in words))
            for number, words in quran_corpus.words_for_surah(surah)
        ]
    else:
        ayahs = [(number, None, text) for number, text in quran_corpus.ayah_texts(surah)]

    if not ayahs:
        return None

    english = quran_meanings.for_surah(surah)
    named = quran_meanings.surah_name(surah) or {}
    # Which printed page each ayah begins on. Empty when the layout was never
    # built, and every ayah's page is then None, a reader that wants real pages
    # checks for that rather than being handed an estimate dressed up as a fact.
    pages = quran_layout.for_surah(surah)

    return {
        "surah": surah,
        "name_en": named.get("name_en", ""),
        "name_ar": named.get("name_ar", ""),
        "ayah_count": len(ayahs),
        "ayahs": [
            {
                "ayah": number,
                "arabic": text,
                "page": pages.get(number),
                "english": " ".join(english.get(number, {}).values()),
                "words": [
                    {**word, "meaning": english.get(number, {}).get(position, "")}
                    for position, word in enumerate(words, 1)
                ]
                if words is not None
                else None,
            }
            for number, words, text in ayahs
        ],
    }


def glosses_for_surah(surah: int) -> dict[int, list[str]]:
    """Each ayah's English word by word, in the order the words are printed.

    For showing a reader what one word means without leaving the page. Cheap
    enough to fetch for a whole surah: al-Baqarah, the longest, is 121KB, where
    its grammar is nearly a megabyte.

    An ayah is included only when the corpus has exactly as many words as the
    printed text does. They agree on 6,235 of the Qur'an's 6,236 ayahs; the
    exception is 37:130, where إل ياسين is printed as two words and counted as
    one. Handing that ayah out anyway would shift every gloss after it by one
    and quietly put the wrong English on the wrong word, which is the one thing
    this feature must never do. Left out, the reader shows the ayah plain.
    """
    english = quran_meanings.for_surah(surah)
    glosses: dict[int, list[str]] = {}
    for number, text in quran_corpus.ayah_texts(surah):
        words = english.get(number, {})
        if len(words) != len(text.split()):
            continue
        glosses[number] = [words[position] for position in sorted(words)]
    return glosses


def is_loaded() -> bool:
    return quran_corpus.is_loaded()
