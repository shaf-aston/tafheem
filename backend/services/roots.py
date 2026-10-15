"""The root a word is built from. The one place in the app that answers it.

The Sarf table, the Nahw chart, the dictionary, the Qur'an's root search and
Daleel all ask here. Before, each had its own idea, and a word one tab could
place another could not: قالوا had a root in none of them, so Sarf had no table
for it and the dictionary had no entry.

Where an answer comes from, surest first:
  1. the Qur'an corpus, every word of the Qur'an tagged by hand;
  2. the dictionary, whose headword spelled as typed files its root;
  3. CAMeL (services/morphology.py), which reads any form, prefixes, endings
     and all, to the word it is a form of and that word's root.

CAMeL writes # for a weak radical it cannot pin down (ق#ل for قالوا, ب#ت for
بيوت). That is settled here against the roots the books really file (the
corpus, the dictionary, Maqayees), choosing by the word it comes from. A
letter no book files under is never offered as a root.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from itertools import product

from backend.services import dictionary_service, quran_corpus, root_meaning
from backend.services.arabic_text import bare_letters, normalize_root

log = logging.getLogger(__name__)

# What CAMeL's # stands for: a weak radical, or a hamza it could not seat.
UNKNOWN = "#"
WEAK = ("و", "ي", "ء")
# The same letter as a root writes it and as a word spells it: آتى keeps the ي of أتي as ى.
_AS_ROOT = str.maketrans({"ى": "ي", "أ": "ء", "إ": "ء", "آ": "ء", "ؤ": "ء", "ئ": "ء", "ٱ": "ا"})


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
    if dictionary_service.is_root(root):
        return normalize_root(root)
    doubled = key[:2] if len(key) == 3 and key[1] == key[2] else None
    if _book_opened() and any(letters and root_meaning.book_root_of(letters) for letters in (root, key, doubled)):
        return normalize_root(root)
    return ""


def settle(pattern: str, lemma: str = "") -> str:
    """CAMeL's root with each # made the weak letter a book files it with; "" when none does.

    Two can fit: ق#ل is قول (say) and قيل (siesta) in Maqayees. The one whose
    letters the lemma itself carries wins (بيت is ب#ت with its ي), then the
    one the lemma is filed under in the dictionary or the corpus (قال under
    قول), then و, the commoner.
    """
    if UNKNOWN not in pattern:
        return pattern
    options = [WEAK if letter == UNKNOWN else (letter,) for letter in pattern]
    fits = [(spelt, letters) for letters in map("".join, product(*options)) if (spelt := spelling(letters))]
    if not fits:
        return ""
    lemma_letters = set(bare_letters(lemma).translate(_AS_ROOT)) if lemma else set()
    filed = {_key(r) for r in _filed_roots(lemma)} if lemma else set()

    def score(fit: tuple[str, str]) -> tuple[int, int]:
        _, letters = fit
        filled = [letters[i] for i, letter in enumerate(pattern) if letter == UNKNOWN]
        return sum(letter in lemma_letters for letter in filled), _key(letters) in filed

    return max(fits, key=score)[0]  # max keeps the first of equals: و before ي before ء


def _filed_roots(word: str) -> list[str]:
    """The roots a dictionary headword or a Qur'an word spelled like `word` is filed under."""
    found = dictionary_service.headword_roots(word)
    if corpus := _corpus(quran_corpus.root_of, word, default=""):
        found.append(corpus)
    return found


def readings(word: str) -> list[tuple[str, str]]:
    """Every (lemma, root) `word` can be, likeliest first, each root settled; "" where none could be."""
    from backend.services import morphology  # morphology settles its own roots here

    out: list[tuple[str, str]] = []
    for lemma, pattern in morphology.readings(word):
        root = settle(pattern, lemma) if pattern else ""
        if (lemma, root) not in out:
            out.append((lemma, root))
    return out


@lru_cache(maxsize=4096)
def roots_of(word: str) -> tuple[str, ...]:
    """Every root `word` can be built from, likeliest first; () when nothing can place it."""
    word = word.strip()
    if not word:
        return ()
    found = list(dict.fromkeys(_filed_roots(word)))
    for _, root in readings(word):
        if root and root not in found:
            found.append(root)
    return tuple(found)


def root_of(word: str) -> str:
    """The likeliest root of `word`, or "" when nothing can place it."""
    return next(iter(roots_of(word)), "")
