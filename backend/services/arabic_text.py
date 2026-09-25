"""Shared Arabic text helpers, single owner of diacritics stripping.

PyArabic's strip_tashkeel is the most reliable implementation; the regex
(U+0610-U+061A extended signs, U+064B-U+065F harakat, U+0670 superscript alef)
is the dependency-free fallback. Both morphology.py and rule_engine.py import
from here, never redefine this locally.

The one deliberate exception is conjugation.bare(), which keeps the shaddah:
stripping it makes عَلَّمَ and عَلَمَ identical, and the sarf tab picks the باب by
comparing those spellings. Do not merge the two, they answer different questions.
"""
from __future__ import annotations

import re
import unicodedata

# \u escapes, three disjoint ranges: literal Arabic boundary chars get bidi-reordered
# and silently swallow letters like فكلمن into the "diacritics" span.
DIACRITICS_RE = re.compile("[\u0610-\u061a\u064b-\u065f\u0670]")

# What counts as Arabic - one definition, used everywhere (was three, inconsistently).
ARABIC_RE = re.compile("[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")

# Keeps root letters, drops separators (hyphen, dash, any space, zero-width
# space) - an open-ended list, so "keep" is safer than "drop these". Tatweel
# (U+0640) is excluded too: it's typesetting stretch, not a letter.
_NOT_ROOT_LETTER_RE = re.compile("[^\u0600-\u063F\u0641-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFE]")


def has_arabic(text: str) -> bool:
    """True when `text` holds at least one Arabic character."""
    return bool(ARABIC_RE.search(text))


_strip_fn = None
try:
    from pyarabic.araby import strip_tashkeel as _strip_fn  # type: ignore[no-redef]
except ImportError:
    pass

# Whether PyArabic answered strip_diacritics, reported by morphology.py.
HAS_PYARABIC = _strip_fn is not None


def strip_diacritics(text: str) -> str:
    """Strip Arabic tashkeel/diacritics from `text`."""
    return DIACRITICS_RE.sub("", text) if _strip_fn is None else _strip_fn(text)


# Folds spelling variants that mean the same word (Qur'anic alef wasla vs plain alef) to shared letters.
_QURANIC_MARKS_RE = re.compile("[ـۖ-ۭ࣓-ࣿ]")
_LETTER_FOLD = str.maketrans({"ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا",
                              "ى": "ي"})


def words(text: str) -> list[str]:
    """The words of a sentence: each token stripped of the Qur'an's reading marks,
    and only those with an Arabic letter left in them.

    One rule instead of a list of things to skip: a pause sign, an ayah number,
    a verse-end mark and a stray comma all fail it the same way, because none
    of them holds a letter. Listing them would go out of date at the next mark.

    Punctuation is a break between words, spaced or not: مَرْحَبًا، reached CAMeL
    with its comma and came back as an unknown name.
    """
    spaced = "".join(" " if unicodedata.category(c).startswith("P") else c for c in text)
    cleaned = (_QURANIC_MARKS_RE.sub("", token) for token in spaced.split())
    return [w for w in cleaned if any(unicodedata.category(c) == "Lo" and ARABIC_RE.match(c) for c in w)]


def bare_letters(text: str) -> str:
    """The letters of a word, with every mark and spelling variant folded away.

    For deciding whether two sources are talking about the same word, never for
    display, because what it returns is not how anyone writes Arabic.
    """
    # DIACRITICS_RE runs after strip_diacritics on purpose: PyArabic leaves the
    # maddah and the superscript alef in place, and Qur'anic spelling is full of both.
    folded = DIACRITICS_RE.sub("", strip_diacritics(text))
    return _QURANIC_MARKS_RE.sub("", folded).translate(_LETTER_FOLD)



# Qur'anic small alef (long "aa") vs. plain alef: كِتَٰب and الكتاب are the
# same word, so this spells the mark out as a full alef so both match.
_SMALL_ALEF = "ٰ"
# Strip marks other than the small alef first (it can follow a fatha).
_OTHER_MARKS_RE = re.compile("[ؐ-ًؚ-ٟ]")
# waw/ya + small alef -> one alef; the mark alone -> alef too.
_WRITTEN_OUT = ((f"و{_SMALL_ALEF}", "ا"), (f"ي{_SMALL_ALEF}", "ا"), (_SMALL_ALEF, "ا"))


def alef_written_out(text: str) -> str:
    """The same letters, with the Qur'an's small alef spelled as a full one."""
    text = _OTHER_MARKS_RE.sub("", text)
    for mark, letter in _WRITTEN_OUT:
        text = text.replace(mark, letter)
    return bare_letters(text)


def normalize_root(text: str) -> str:
    """One spelling of a root, so the same three letters always match.

    Without this the tabs cannot pass a root to each other: the conjugator hands
    over "ك-ت-ب" and the corpus has never heard of it. It is also what files
    the classical root book, so a root the book writes with an unusual separator
    has to normalise to the same key as the one the reader types.
    """
    return _NOT_ROOT_LETTER_RE.sub("", strip_diacritics(text))


# What a person puts between letters when they spell a word out: spaces of any
# kind, hyphens and dashes, the zero-width space.
_SPELLING_GAP_RE = re.compile(r"[\s\-‐-―​]+")
# Fewer than three and it is more likely two real one-letter words than a spelling.
_MIN_SPELLED_LETTERS = 3


def spelled_out(text: str) -> str:
    """A word typed one letter at a time, joined: ك ت ب and ك-ت-ب both give كتب.

    The search box is where a reader types a root the way the books print it,
    and a search that does not see one word in it finds nothing. Deliberately
    not normalize_root, which drops every non-letter and would glue a phrase
    into one word: this joins only when every piece is a single letter, so a
    real phrase, or anything with a longer piece in it, comes back untouched.
    """
    pieces = [p for p in _SPELLING_GAP_RE.split(text) if p]
    one_letter_each = all(len(strip_diacritics(p)) == 1 and ARABIC_RE.match(p) for p in pieces)
    return "".join(pieces) if len(pieces) >= _MIN_SPELLED_LETTERS and one_letter_each else text


# A Latin letter or "#" in a root means a code or placeholder, not a root:
# CAMeL writes NTWS for particles and # for a radical it cannot pin down.
_NOT_A_ROOT_RE = re.compile(r"[A-Za-z#]")


def shown_root(text: str | None) -> str:
    """The root as a reader may see it, or "" when there is no real root.

    Every root that reaches the client passes through here: the analyzer's,
    the AI's freehand "ل-م-", and the particle placeholder that once printed
    as "NطWص". A part of a code is still a code, so anything holding a Latin
    letter or # is dropped whole rather than trimmed to its Arabic letters.
    """
    return "" if not text or _NOT_A_ROOT_RE.search(text) else normalize_root(text)
