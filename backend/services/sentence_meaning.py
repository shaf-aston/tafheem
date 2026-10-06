"""A phrase or sentence in English: what it means, then word by word.

Two lines, the way al-Maany sets them out: the sense first, the words under it.

The words come from CAMeL on this machine, every time, in milliseconds: each
word's sense as its tagger read it from the words around it. The sense comes
from the surest source that has one. A whole ayah has its published translation
and the Qur'an's own word-by-word; anything else goes to the language model,
handed the word-by-word too so its sentence stays tied to those words. A model
answer is filed on disk, so the same text asks once and reads the same each
time, on every server process.
"""
from __future__ import annotations

import logging
import re
from itertools import pairwise

from backend.config import get_settings
from backend.services import ai, iraab, morphology, progress_store, quran_library, quran_meanings
from backend.services.arabic_text import words
from backend.services.nahw_book import term_ar
from backend.services.quran_search import local

logger = logging.getLogger(__name__)

_TAGS_RE = re.compile(r"\[[^\]]*\]|<[^>]*>")
# The word every clause's name opens with (data/nahw_rules/tarkeeb.json).
_CLAUSE = term_ar("jumlah_ismiyyah").split()[0]
# Where a model's sense is filed (progress_store), so every server process reads the first one kept.
_KEPT = "dict"


def literal(gloss: str) -> str:
    """CAMeL's gloss as English: each joined piece's first senses, tags dropped.

    and+write+he;it_<verb> reads "and write he/it"; the+child;son reads "the
    child/son". More than one sense shows the choice rather than guessing it.
    """
    senses = get_settings().sentence_senses
    pieces = ("/".join(_TAGS_RE.sub("", piece).split(";")[:senses]).replace("_", " ").strip() for piece in gloss.split("+"))
    return " ".join(piece for piece in pieces if piece)


def kind_of(summary: str | None, read: list[dict]) -> str:
    """"sentence" when it says something, else "phrase".

    `summary` is the grammar's name for the whole (iraab.analyse, as the Analyse
    page shows it), and every clause it names is a جُمْلَةٌ: the verbal, nominal,
    question and call clauses alike. It reads البيت الكبير as a described noun and
    هل أنت جائع as a question. It does not yet see a definite noun told about by
    what follows (الحمد لله, الولد في البيت), so that is checked here too.
    """
    told = any(
        a["pos"] in morphology.NOUNISH and a["state"] == "d" and (b["state"] == "i" or b["pos"] == "prep")
        for a, b in pairwise(read)
    )
    return "sentence" if told or (summary or "").startswith(_CLAUSE) else "phrase"


def translate(text: str) -> dict:
    """The sense, its source, and the words; the sense is None when nothing could give one."""
    read = morphology.analyze_sentence(text)
    pairs = [{"arabic": w["word"], "english": literal(w["gloss"]), "base": w.get("base") or w["word"]} for w in read]
    found = _whole_ayah(text, pairs) or _model_sense(text, pairs)
    return {"kind": kind_of(iraab.analyse(text)["summary"], read), **found}


def _whole_ayah(text: str, pairs: list[dict]) -> dict | None:
    """The ayah's published sense, when the text is one whole ayah and nothing more,
    and its published words too unless their count disagrees with the ayah's own,
    when CAMeL's stand rather than English landing under the wrong word."""
    if (hit := local.whole_ayah(text)) is None:
        return None
    books = quran_library.for_ayah(hit.surah, hit.ayah, [get_settings().sentence_translation])
    if not books:
        return None
    found = {"meaning": standing(books[0]["text"]), "source": "translation", "ref": f"{hit.surah}:{hit.ayah}"}
    english = quran_meanings.for_ayah(hit.surah, hit.ayah)
    ayah_words = words(hit.arabic_text)
    if len(english) != len(ayah_words):
        return {**found, "words": pairs, "words_source": "camel"}
    return {**found, "words_source": "translation",
            "words": [{"arabic": w, "english": english.get(n, ""), "base": w} for n, w in enumerate(ayah_words, 1)]}


_PAIRS = {"(": ")", "[": "]", "“": "”"}
# What a sentence carried on past the ayah leaves at the cut: a dash, a comma, a colon.
_CUT_RE = re.compile(r"[\s,;:\-–—]+$")


def standing(text: str) -> str:
    """One ayah's slice of a running translation, made to stand on its own.

    The translation is prose cut at each ayah's end, so a sentence that runs on
    leaves its comma or dash at the cut, and a quote opened in one ayah closes in
    another. The cut is trimmed, and each mark left open, or closed with no
    opening, gets its partner at the other end.
    """
    text = _CUT_RE.sub("", text.strip())
    opened = []
    head = ""
    for c in text:
        if c in _PAIRS:
            opened.append(c)
        elif c in _PAIRS.values():
            if opened and _PAIRS[opened[-1]] == c:
                opened.pop()
            else:
                head = next(o for o, shut in _PAIRS.items() if shut == c) + head
    tail = "".join(_PAIRS[o] for o in reversed(opened))
    if text.count('"') % 2:
        # The odd quote opens when words follow it, else it closes one from before.
        last = text.rindex('"')
        tail, head = (tail + '"', head) if text[last + 1:].strip() else (tail, '"' + head)
    text = head + text + tail
    return text[:1].upper() + text[1:]


def _model_sense(text: str, pairs: list[dict]) -> dict:
    """The model's sense over CAMeL's words; no sense when the model is unreachable."""
    try:
        meaning = _asked(text, " | ".join(f"{p['arabic']} = {p['english']}" for p in pairs))
    except Exception as exc:  # noqa: BLE001, a dead model leaves the word-by-word standing
        logger.info("sentence meaning  model failed: %s", exc)
        meaning = None
    return {"meaning": meaning, "source": "ai" if meaning else None, "ref": None,
            "words": pairs, "words_source": "camel"}


def _asked(text: str, word_by_word: str) -> str:
    """One model answer per text, filed on disk: the server runs several processes,
    and a cache in each gave the same sentence two wordings by turns. A failure or
    an empty answer raises and is not filed. Two first askings at once both ask, and
    both return the one the store kept first."""
    if not (kept := progress_store.kept_questions(_KEPT, text)):
        if not (english := ai.translate_sentence(text, word_by_word)["english"].strip()):
            raise ValueError("the model answered with nothing")
        progress_store.keep_questions(module=_KEPT, sentence=text, source="ai",
                                      questions=[{"question": "meaning", "answer": english}])
        kept = progress_store.kept_questions(_KEPT, text)
    return kept[0]["answer"]
