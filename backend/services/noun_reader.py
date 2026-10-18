"""A typed noun the dictionary lacks, read off sarf's own shapes: the masdar of a derived
form (تَبَسُّمٌ is Form V's تَفَعُّل) and the elative (أَدْوَمُ is أَفْعَلُ), with a pronoun
joined on (تَبَسُّمُكَ، أَدْوَمُهَا).

verb_reader does this for verbs. CAMeL has no تَبَسُّم and offers the verb تَبَسَّمَكَ or a
guessed name instead, which the typed vowels contradict; the parser then reads the ك's
fatha as the word's case. The shapes are the book's (data/sarf/patterns.json `masdar`,
closed_words.json `elative_patterns`), never a list of words, and a reading stands only
when the reader typed a vowel on every letter before the case: the vowels are the evidence.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.services.harakat import CAMEL_CASE, SHADDA, VOWEL, fits_shape, letters
from backend.services.nahw_book import book_words

_PATTERNS = Path(__file__).parent.parent / "data" / "sarf" / "patterns.json"
_ROOT = "فعل"  # how harakat.fits_shape writes the root's letters in a shape
# CAMeL's name for each pronoun joined to a noun, by its letters and, for ك, its vowel
_ENCLITIC = {"ي": "1s", "نا": "1p", "كَ": "2ms", "كِ": "2fs", "كما": "2d", "كم": "2mp", "كن": "2fp",
             "ه": "3ms", "ها": "3fs", "هما": "3d", "هم": "3mp", "هن": "3fp"}
_CASE = {vowel: camel for camel, vowel in CAMEL_CASE.items()}


@lru_cache(maxsize=1)
def _shapes() -> list[tuple[str, str, str]]:
    """(shape in فعل letters, the analyser's digit pattern, part of speech), the elative first."""
    elative = [(shape.replace("1", "ف").replace("2", "ع") + "ل", shape + "3", "adj")
               for shape in book_words("elative_patterns")]
    masdars = []
    for form in json.loads(_PATTERNS.read_text(encoding="utf-8"))["forms"].values():
        shape = form.get("masdar") or ""
        if shape and "{4}" not in shape:  # fits_shape holds a root of three
            masdars.append((shape.format("", *_ROOT), shape.format("", 1, 2, 3), "noun"))
    return elative + masdars


def _pronoun(marked: list[tuple[str, set]]) -> tuple[int, str]:
    """(how many letters at the end are a pronoun joined on, CAMeL's name for it); (0, "0") for none.
    The longest first: هما before ها. A letter left bare before it says nothing, so the case vowel
    typed before the pronoun is what tells it from the word's own last letters."""
    for size in (3, 2, 1):
        if len(marked) <= size + 2:
            continue
        said = "".join(letter for letter, _ in marked[-size:])
        if said not in book_words("damir_muttasil", "on_nouns"):
            continue
        if not marked[-size - 1][1] & VOWEL.keys():
            continue  # the word before the pronoun ends on its case vowel
        # كَ is "you" said to a man, كِ to a woman; a bare ك is taken as the man's
        name = _ENCLITIC.get(said) or _ENCLITIC["كِ" if "ِ" in marked[-1][1] else "كَ"]
        return size, name
    return 0, "0"


def reading_of(word: str) -> dict | None:
    """The noun this typed word is, in the dictionary's own features ({pos, diac, atbtok, ...}),
    or None when no shape fits it, or a letter before its case was left bare (a long letter needs none)."""
    marked = letters(word)
    size, enclitic = _pronoun(marked)
    stem = marked[:len(marked) - size]
    # a long letter (the ا of تَعَاوُن) carries no vowel of its own; a bare ا opening the word is
    # hamzat al-wasl, a command's (افْعَلِي), never the hamza of أَفْعَل
    if len(stem) < 3 or not all(marks or (letter in "اوي" and i) for i, (letter, marks) in enumerate(stem[:-1])):
        return None
    case = next((VOWEL[m] for m in stem[-1][1] if m in VOWEL), None)
    # the shape is the word less its case: the last letter's vowel is the case, not the shape's
    shaped = "".join(letter + "".join(sorted(marks)) for letter, marks in stem[:-1])
    shaped += stem[-1][0] + (SHADDA if SHADDA in stem[-1][1] else "")
    for shape, pattern, pos in _shapes():
        if not fits_shape(shaped, shape):
            continue
        typed_stem = "".join(letter + "".join(sorted(marks)) for letter, marks in stem)
        pronoun = "".join(letter + "".join(sorted(marks)) for letter, marks in marked[len(stem):])
        return {"pos": pos, "diac": word, "lex": "".join(letter for letter, _ in stem), "pattern": pattern,
                "atbtok": f"{typed_stem}_+{pronoun}" if size else typed_stem,
                "catib6": "NOM+NOM" if size else "NOM", "ud": ("NOUN" if pos == "noun" else "ADJ") + ("+PRON" if size else ""),
                "enc0": f"{enclitic}_poss" if size else "0", "stt": "c" if size else "i",
                "cas": _CASE.get(case, "u") if case else "na", "num": "s", "gen": "m",
                "asp": "na", "vox": "na", "per": "na", "mod": "na",
                "prc0": "0", "prc1": "0", "prc2": "0", "prc3": "0", "source": "sarf"}
    return None
