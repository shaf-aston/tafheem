"""The root a word is built from. The one place in the app that answers it.

The Sarf table, the Nahw chart, the dictionary, the Qur'an's root search and
Daleel all ask here. Before, each had its own idea, and a word one tab could
place another could not: قالوا had a root in none of them, so Sarf had no table
for it and the dictionary had no entry.

Where an answer comes from, surest first:
  1. the Qur'an corpus, every word of the Qur'an tagged by hand;
  2. the dictionary, whose headword spelled as typed files its root;
  3. CAMeL (services/sarf/morphology.py), which reads any form, prefixes, endings
     and all, to the word it is a form of and that word's root; a classical form
     it cannot read (أتريد، لنصدقن), read again with the book's joined letters off.

CAMeL writes # for a weak radical it cannot pin down (ق#ل for قالوا, ب#ت for
بيوت). That is settled here against the roots the books really file (the
corpus, the dictionary, Maqayees), choosing by the word it comes from. A
letter no book files under is never offered as a root.
"""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from itertools import product

from backend.services.dictionary import service as dictionary_service
from backend.services.nahw import book as nahw_book
from backend.services.quran import corpus as quran_corpus
from backend.services.dictionary import root_meaning
from backend.services.text.arabic_text import (
    as_root_letters,
    bare_letters,
    normalize_root,
    root_letters_in_order,
    strip_diacritics,
)

log = logging.getLogger(__name__)

# What CAMeL's # stands for: a weak radical, or a hamza it could not seat.
UNKNOWN = "#"
WEAK = ("و", "ي", "ء")
# No Arabic root has fewer letters: CAMeL's لس for ليس is a slip, no root.
FEWEST_RADICALS = 3
# Nor more than a bare noun's five («ومنتهى اسمٍ خمسٌ إن تجرّدا», سفرجل), nor a mark among
# them: CAMeL's بللّه for بالله and ٱثنتن for اثنتين are slips.
ROOT_SHAPE = re.compile("[ء-ي]{3,5}")


def _corpus(call, *args, default):
    """A corpus question, or `default` while corpus.db is not built (CI, a fresh checkout)."""
    try:
        return call(*args)
    except Exception as exc:  # no file, an empty file, a table not there yet
        log.debug("corpus not readable for roots: %s", exc)
        return default


@lru_cache(maxsize=1)
def _corpus_roots() -> dict[str, str]:
    """Every root the corpus tags, by its folded letters, as the corpus spells it."""
    rows = _corpus(lambda: quran_corpus._db().execute(
        "SELECT DISTINCT root FROM segment WHERE root <> ''").fetchall(), default=[])
    return {_key(row["root"]): row["root"] for row in rows}


@lru_cache(maxsize=1)
def _book_opened() -> bool:
    """Maqayees read once: the app's startup reads it too, a script or a test may not have."""
    if root_meaning.status() != root_meaning.READY:
        root_meaning.load()
    return root_meaning.status() == root_meaning.READY


def _key(root: str) -> str:
    """Letters compared across books: ءتي, أتي and اتي are one root."""
    return bare_letters(normalize_root(root)).replace("ء", "ا")


def spelling(root: str) -> str:
    """The root as a book files it, or "" when no book here does.

    The corpus's spelling first, so a root found here is one the Qur'an's root
    search can open; then the dictionary's; then Maqayees', which files a
    doubled root with two letters (فر for فرر), so that is asked too.
    """
    key = _key(root)
    if not key:
        return ""
    if found := _corpus_roots().get(key):
        return found
    if filed := dictionary_service.filed_root(root):
        return normalize_root(filed)
    doubled = key[:2] if len(key) == 3 and key[1] == key[2] else None
    if _book_opened() and any(letters and root_meaning.book_root_of(letters) for letters in (root, key, doubled)):
        return normalize_root(root)
    return ""


def settle(pattern: str, lemma: str = "") -> str:
    """CAMeL's root made one a book files; "" when none does.

    A root CAMeL spells out whole is kept only if it is one: three to five
    letters, and the three a book files (تبغ for تبغِ is no root, بغي is).
    CAMeL writes # for a weak radical it cannot pin down (ق#ل for قالوا), so each
    # is tried as و, ي and ء. Two can fit: ق#ل is قول (say) and قيل (siesta) in
    Maqayees. The one the lemma itself is filed under wins (قال under قول), then
    the one whose letters the lemma carries (بيت is ب#ت with its ي), then و, the
    commoner. A root the lemma is filed under is tried too when it has CAMeL's
    sure letters in place: CAMeL has ماء as م## though the books file it under م و ه.
    """
    if UNKNOWN not in pattern and len(pattern) >= FEWEST_RADICALS:
        if not ROOT_SHAPE.fullmatch(pattern):
            return ""
        # A book files a three-letter root it knows; a longer one (خنزر, قسطس) it seldom lists as one.
        return spelling(pattern) if len(pattern) == FEWEST_RADICALS else pattern
    filed = _filed_roots(lemma) if lemma else []
    if len(pattern) < FEWEST_RADICALS:  # a slip: the lemma's own root, holding the letters CAMeL gave
        short = as_root_letters(pattern)
        return next((spelt for root in filed if root_letters_in_order(short, as_root_letters(root)) == len(short)
                     and (spelt := spelling(root))), "")
    filed_keys = {_key(root) for root in filed}
    tried = list(map("".join, product(*[WEAK if letter == UNKNOWN else (letter,) for letter in pattern])))
    tried += [root for root in filed if _in_place(as_root_letters(root), pattern)]
    fits = [(spelt, letters) for letters in tried if (spelt := spelling(letters))]
    if not fits:
        return ""
    # The lemma's letters with its hamza kept: folded for searching, قَرَأ carried no ء and ق.ر.# came out قرو.
    lemma_letters = as_root_letters(lemma)

    def score(fit: tuple[str, str]) -> tuple[int, int]:
        _, letters = fit
        return _key(letters) in filed_keys, root_letters_in_order(as_root_letters(letters), lemma_letters)

    return max(fits, key=score)[0]  # max keeps the first of equals: و before ي before ء


def _in_place(root: str, pattern: str) -> bool:
    """Whether `root` has each letter CAMeL was sure of where CAMeL put it."""
    return len(root) == len(pattern) and all(
        sure == UNKNOWN or as_root_letters(sure) == letter for sure, letter in zip(pattern, root))


def _filed_roots(word: str) -> list[str]:
    """The roots a dictionary headword or a Qur'an word spelled like `word` is filed under."""
    found = dictionary_service.headword_roots(word)
    if corpus := _corpus(quran_corpus.root_of, word, default=""):
        found.append(corpus)
    return found


def readings(word: str) -> list:
    """Every way `word` can be read alone, likeliest first, each root settled; "" where none could be.

    CAMeL reads MSA: a question أ or an oath's لَ with the نون of emphasis (أتريد، لنصدقن) it has
    no reading for. Then the word left with the book's joined letters off, the fewest first.
    """
    if read := _read_whole(word):
        return read
    stems = (stem for stem in nahw_book.joined_off(strip_diacritics(word)) if len(stem) >= FEWEST_RADICALS)
    return next(filter(None, map(_read_whole, stems)), [])  # a name read is rootless, not peeled on: ولوطا


def _read_whole(word: str) -> list:
    from backend.services.sarf import morphology  # morphology settles its own roots here

    out = []
    for reading in morphology.readings(word):
        settled = reading._replace(root=settle(reading.root, reading.lemma) if reading.root else "")
        if settled not in out:
            out.append(settled)
    return out


@lru_cache(maxsize=4096)
def roots_of(word: str) -> tuple[str, ...]:
    """Every root `word` can be built from, likeliest first; () when nothing can place it, or it has none.

    The Qur'an's own tag first, "none" included (إبراهيم, من). Then the likeliest reading:
    a harf or a word built like one has no root, whatever a headword spelled the same is
    filed under (إنه is not أنهِ, finish). Then the headwords spelled like it, then the
    other readings.
    """
    word = word.strip()
    if not word:
        return ()
    read = readings(word)
    corpus = _corpus(quran_corpus.root_of, word, default=None)
    if corpus == "" or corpus is None and read and not read[0].rooted:
        return ()
    found = [corpus] + [r.root for r in read[:1]] + dictionary_service.headword_roots(word) + [r.root for r in read]
    return tuple(dict.fromkeys(root for root in found if root))


def root_of(word: str) -> str:
    """The likeliest root of `word`, or "" when nothing can place it."""
    return next(iter(roots_of(word)), "")
