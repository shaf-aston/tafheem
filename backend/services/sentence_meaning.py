"""A phrase or sentence in English: what it means, then word by word.

Two lines, the way al-Maany sets them out: the sense first, the words under it.

The words come from CAMeL on this machine, every time, in milliseconds: each
word's sense as its tagger read it from the words around it. The sense comes
from the surest source that has one. A whole ayah has its published translation
and the Qur'an's own word-by-word; anything else goes to the language model,
handed the word-by-word too so its sentence stays tied to those words. A model
answer is kept for the life of the process, so the same text asks once and
reads the same each time.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from itertools import pairwise

from backend.config import get_settings
from backend.services import ai, morphology, quran_library, quran_meanings
from backend.services.arabic_text import words
from backend.services.quran_search import local

logger = logging.getLogger(__name__)

_TAGS_RE = re.compile(r"\[[^\]]*\]|<[^>]*>")


def literal(gloss: str) -> str:
    """CAMeL's gloss as English: each joined piece's first senses, tags dropped.

    and+write+he;it_<verb> reads "and write he/it"; the+child;son reads "the
    child/son". More than one sense shows the choice rather than guessing it.
    """
    senses = get_settings().sentence_senses
    pieces = ("/".join(_TAGS_RE.sub("", piece).split(";")[:senses]).replace("_", " ").strip() for piece in gloss.split("+"))
    return " ".join(piece for piece in pieces if piece)


def kind_of(text: str, read: list[dict]) -> str:
    """"sentence" when it says something, else "phrase".

    It says something when it has a verb, ends like a sentence, or names
    something definite and then tells you about it: البيت كبير and الحمد لله are
    sentences, البيت الكبير and رب العالمين are phrases.
    """
    told = any(
        a["pos"] in morphology.NOUNISH and a["state"] == "d" and (b["state"] == "i" or b["pos"] == "prep")
        for a, b in pairwise(read)
    )
    ends = text.rstrip()[-1:] in get_settings().sentence_end_marks
    return "sentence" if told or ends or any(w["pos"] == "verb" for w in read) else "phrase"


def translate(text: str) -> dict:
    """The sense, its source, and the words; the sense is None when nothing could give one."""
    read = morphology.analyze_sentence(text)
    pairs = [{"arabic": w["word"], "english": literal(w["gloss"]), "base": w.get("base") or w["word"]} for w in read]
    found = _whole_ayah(text, pairs) or _model_sense(text, pairs)
    return {"kind": kind_of(text, read), **found}


def _whole_ayah(text: str, pairs: list[dict]) -> dict | None:
    """The ayah's published sense, when the text is one whole ayah and nothing more,
    and its published words too unless their count disagrees with the ayah's own,
    when CAMeL's stand rather than English landing under the wrong word."""
    if (hit := local.whole_ayah(text)) is None:
        return None
    books = quran_library.for_ayah(hit.surah, hit.ayah, [get_settings().sentence_translation])
    if not books:
        return None
    english = quran_meanings.for_ayah(hit.surah, hit.ayah)
    ayah_words = words(hit.arabic_text)
    if len(english) != len(ayah_words):
        return {"meaning": books[0]["text"], "source": "translation", "ref": f"{hit.surah}:{hit.ayah}",
                "words": pairs, "words_source": "camel"}
    return {
        "meaning": books[0]["text"],
        "source": "translation",
        "ref": f"{hit.surah}:{hit.ayah}",
        "words": [{"arabic": w, "english": english.get(n, ""), "base": w} for n, w in enumerate(ayah_words, 1)],
        "words_source": "translation",
    }


def _model_sense(text: str, pairs: list[dict]) -> dict:
    """The model's sense over CAMeL's words; no sense when the model is unreachable."""
    try:
        meaning = _asked(text, " | ".join(f"{p['arabic']} = {p['english']}" for p in pairs))
    except Exception as exc:  # noqa: BLE001, a dead model leaves the word-by-word standing
        logger.info("sentence meaning  model failed: %s", exc)
        meaning = None
    return {"meaning": meaning, "source": "ai" if meaning else None, "ref": None,
            "words": pairs, "words_source": "camel"}


@lru_cache(maxsize=get_settings().dictionary_cache_size)
def _asked(text: str, word_by_word: str) -> str:
    """One model answer per text. Kept only when it worked: a failure raises, and lru_cache keeps no exceptions."""
    if not (english := ai.translate_sentence(text, word_by_word)["english"].strip()):
        raise ValueError("the model answered with nothing")
    return english
