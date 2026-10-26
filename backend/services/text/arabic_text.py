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



def marks_in_order(text: str) -> str:
    """Each letter's marks in one fixed order, length kept: shadda+damma and damma+shadda look alike but differ as text."""
    return re.sub(f"(?:{DIACRITICS_RE.pattern}){{2,}}", lambda run: "".join(sorted(run.group(), key=unicodedata.combining)), text)

_strip_fn = None
try:
    from pyarabic.araby import strip_tashkeel as _strip_fn  # type: ignore[no-redef]
except ImportError:
    pass

# Whether PyArabic answered strip_diacritics, reported by morphology.py.
HAS_PYARABIC = _strip_fn is not None


def strip_diacritics(text: str) -> str:
    """Strip Arabic tashkeel/diacritics from `text`. The regex runs after PyArabic too:
    PyArabic leaves the maddah and the superscript alef (تُتْلَىٰ), which are marks, not letters."""
    return DIACRITICS_RE.sub("", text if _strip_fn is None else _strip_fn(text))


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
    return [_MADDA_RE.sub(lambda found: found.group(1) + "آ", w) for w in _tokens(text) if _has_arabic_letter(w)]


def not_arabic(text: str) -> list[str]:
    """What words() drops that a reader typed as a word: letters, none Arabic (hello, x).
    A mark or a number is not a word, so it is not reported."""
    return [w for w in _tokens(text) if any(c.isalpha() for c in w) and not _has_arabic_letter(w)]


def unpunctuated(text: str) -> str:
    """The text with every punctuation mark a break between words, spaced or not,
    and the Qur'an's own marks gone: القيامة. is القيامة, مالك،يوم is two words.
    The one rule every search box reads its query by (utils.search_query).

    An apostrophe between two letters is part of the word (don't, Mu'adh), not
    a break, or one word typed in English would be searched as two.
    """
    spaced = "".join(" " if _breaks(text, i) else c for i, c in enumerate(text))
    return " ".join(_QURANIC_MARKS_RE.sub("", spaced).split())


def _breaks(text: str, i: int) -> bool:
    if not unicodedata.category(text[i]).startswith("P"):
        return False
    inside = 0 < i < len(text) - 1 and text[i - 1].isalpha() and text[i + 1].isalpha()
    return not (inside and text[i] in _APOSTROPHES)


_APOSTROPHES = "'’"


# The Qur'an's spelling of آ: ءَامَنُوا is آمَنُوا. Only where the hamza opens the word (or follows
# a one-letter prefix) and more follows the alef: جُزْءَا and شَيْءَانِ keep their hamza.
_MADDA_RE = re.compile("^((?:[وفبلكس][ً-ْ]?)?)ءَا(?=.)")


def _tokens(text: str) -> list[str]:
    return unpunctuated(text).split()


def _has_arabic_letter(token: str) -> bool:
    return any(unicodedata.category(c) == "Lo" and ARABIC_RE.match(c) for c in token)


def bare_letters(text: str) -> str:
    """The letters of a word, with every mark and spelling variant folded away.

    For deciding whether two sources are talking about the same word, never for
    display, because what it returns is not how anyone writes Arabic.
    """
    # NFKC first: a ligature is the letters it is drawn from, so ﷲ is الله and
    # ﻻ is لا. Without it a typed ﷲ matched nothing, not even itself in a book.
    text = unicodedata.normalize("NFKC", text)
    return _QURANIC_MARKS_RE.sub("", strip_diacritics(text)).translate(_LETTER_FOLD)


def doubled_letters(text: str) -> tuple:
    """One per letter of bare_letters(text): True under a shadda, False under another mark, None unmarked."""
    out: list = []
    for char in _QURANIC_MARKS_RE.sub("", unicodedata.normalize("NFKC", text)):
        if not DIACRITICS_RE.match(char):
            out.append(None)
        elif out and out[-1] is not True:
            out[-1] = char == "\u0651"  # the shadda
    return tuple(out)



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


def both_spellings(text: str) -> str:
    """The text folded both ways a reader might type it, in one string.

    The Qur'an writes a long "aa" as a small mark above the letter, so ٱلْكِتَٰب is
    the word an ordinary book spells الكتاب. Drop the mark and someone typing
    الكتاب finds nothing; write it out as a full alef and someone typing الرحمن
    finds nothing, because that word is never spelled الرحمان. Neither fold is
    right on its own, so both go in and a query matches whichever fits. Text
    without the mark, which is every book but the Qur'an, comes back once.
    """
    dropped = bare_letters(text)
    written = alef_written_out(text)
    return dropped if written == dropped else f"{dropped} {written}"


def normalize_root(text: str) -> str:
    """One spelling of a root, so the same three letters always match.

    Without this the tabs cannot pass a root to each other: the conjugator hands
    over "ك-ت-ب" and the corpus has never heard of it. It is also what files
    the classical root book, so a root the book writes with an unusual separator
    has to normalise to the same key as the one the reader types.
    """
    return _NOT_ROOT_LETTER_RE.sub("", strip_diacritics(text))


# A letter as a root writes it: every seated hamza is the root's ء, and آتى keeps the ي of أتي as ى.
_AS_ROOT = str.maketrans({"ى": "ي", "أ": "ء", "إ": "ء", "آ": "ء", "ؤ": "ء", "ئ": "ء", "ٱ": "ا"})


_THREE_LETTERS = 3
# A shadda is its letter twice, whichever side of the letter's vowel it is written.
_SHADDA_RE = re.compile("([ء-ي])([\u064b-\u0650\u0652]?)\u0651")


def as_root_letters(text: str) -> str:
    """A word's letters spelled the way its root writes them: قَرَأ is قرء, مُعْتَلّ is معتلل.

    Not bare_letters, which folds أ to ا for searching and so loses the hamza a root keeps;
    and a shadda's letter counted once leaves ع ل ل a letter short in مُعْتَلّ.
    """
    letters = normalize_root(_SHADDA_RE.sub(r"\1\1", text))
    # A final ى is a ي only in a word of three letters (رمى, but دعا): past three it is written ى
    # whatever the root, أدنى of د ن و as أبقى of ب ق ي, so it says nothing either way.
    if len(letters) > _THREE_LETTERS and letters.endswith("ى"):
        letters = letters[:-1]
    return letters.translate(_AS_ROOT)


def root_letters_in_order(root: str, word: str) -> int:
    """How many of the root's letters `word` carries in the root's order (both as as_root_letters).

    A root's letters stand in each of its words in order, so this is what tells two roots one
    spelling could be apart: يَقُول holds ق و ل whole and ق ي ل only in part. A letter out of order
    is no radical: the أ of أراد, before its ر, is not the third letter of ر#د.
    """
    held = [[0] * (len(word) + 1) for _ in range(len(root) + 1)]
    for i, r in enumerate(root, 1):
        for j, w in enumerate(word, 1):
            held[i][j] = held[i - 1][j - 1] + 1 if r == w else max(held[i - 1][j], held[i][j - 1])
    return held[-1][-1]


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


# A small meem (U+06E2 above, U+06ED below) written straight after a tanween.
_TANWEEN_MEEM_RE = re.compile("([ً-ٍ])[ۭۢ]")


def mushaf_words(words: list[str], then: str = "") -> list[str]:
    """An ayah's words as the Madinah mushaf prints them.

    The corpus and Quran.com's word list put a small meem after nearly every
    tanween (4,807 of them) to tag how it is said, and a font draws each one as
    a stray letter: إِثْمًۭا. The mushaf prints that meem only for iqlab, where
    the next word starts with ب (سَمِيعًۢا بَصِيرًا), so that is the one kept.
    A stop sign held to its word (غُلْفٌۢ ۚ) does not hide the ب after it.
    `then` is what is read next, so the ayah's last word sees it too: the next
    ayah, or the next surah's بِسْمِ (أَحَدٌۢ at the end of al-Ikhlas).
    Checked against Quran.com's whole-ayah text: the same meems on every ayah.
    """
    return [
        word if following.startswith("ب") else _TANWEEN_MEEM_RE.sub(r"\1", word)
        for word, following in zip(words, [*words[1:], then])
    ]
