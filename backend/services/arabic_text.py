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

# Explicit \u escapes so this NEVER matches Arabic letters
DIACRITICS_RE = re.compile("[ؐ-ًؚ-ٰٟ]")

# What counts as Arabic. One definition, in one place: this used to be asked
# three different ways - broadly in utils.py, narrowly in morphology.py, and
# narrowly again inline in the dictionary router - so the same word could be
# Arabic to one of them and not to another.
ARABIC_RE = re.compile("[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")

# The letters a root is made of. Written as "keep the letters" rather than "drop
# these separators", because the list of things that separate root letters is
# open - hyphen, en-dash, space, non-breaking space, zero-width space - and the
# invisible ones cannot be seen in a diff, so a list of them is a list that
# quietly goes out of date. That list had four entries; a root written with an
# en-dash was filed under letters no search could produce.
#
# U+0640 (tatweel) is left out on purpose: it stretches a word for typesetting,
# it is not a letter, so كــتــب is كتب.
_NOT_ROOT_LETTER_RE = re.compile("[^\u0600-\u063F\u0641-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFE]")


def has_arabic(text: str) -> bool:
    """True when `text` holds at least one Arabic character."""
    return bool(ARABIC_RE.search(text))


_strip_fn = None
try:
    from pyarabic.araby import strip_tashkeel as _strip_fn  # type: ignore[no-redef]
except ImportError:
    pass

# Whether PyArabic is installed. Asked here because this is already the module
# that looks for it, morphology.py reports it as the engine that answered.
HAS_PYARABIC = _strip_fn is not None


def strip_diacritics(text: str) -> str:
    """Strip Arabic tashkeel/diacritics from `text`."""
    return DIACRITICS_RE.sub("", text) if _strip_fn is None else _strip_fn(text)


# Two sources can spell the same word differently and still mean the same word:
# the Qur'anic corpus writes ٱللَّهِ with alef wasla and the Qur'anic pause marks,
# a treebank writes الله plainly. Comparing those letter for letter says they
# differ, which is false. This folds both to the letters they share.
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



# The Qur'an writes a long "aa" as a small alef above the letter rather than as
# the letter ا: ٱلْكِتَٰب is the word an ordinary book spells الكتاب, and ٱلصَّلَوٰة is
# الصلاة. bare_letters drops that little mark, which is right for كِتَٰب matching
# كتب but leaves someone who types الكتاب finding nothing at all.
#
# So this writes the mark out as a full alef instead. Neither answer is the
# right one on its own, رَحْمَٰن is written الرحمن and never الرحمان, which is why
# the search index holds both spellings and a query is compared against the pair.
_SMALL_ALEF = "ٰ"
# Every mark except the small alef itself. Taken off first, because the mark sits
# after a fatha (صَلَوٰة is و, fatha, small alef) and a rule written for the two
# characters side by side would never fire on the real text.
_OTHER_MARKS_RE = re.compile("[ؐ-ًؚ-ٟ]")
# ـوٰ and ـيٰ are the same long "aa" carried on a waw or a ya, so the whole pair
# becomes one alef; anywhere else the mark simply becomes an alef.
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
