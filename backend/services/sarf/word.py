"""A word as a list of letters, each one knowing which job it holds.

Why this exists
---------------
Every rule in the book is phrased about a letter's job, not its position in a
string: "when the و is the middle radical and carries a فتحة before it". A
plain string cannot answer "which letter is the middle radical" once letters
have been deleted or swapped, which is exactly what the rules do. So the
engine builds the word once, keeping each letter's job beside it, applies the
rules, and only then joins it back into text.

A letter is its consonant plus the marks written on it, in the order the
template wrote them.

Where the Arabic lives
----------------------
Two places, and the split is the point. The alphabet itself, the marks, the
two weak letters, the alif, the ways a hamzah is written, is fixed for every
verb in the language and is named once here. What a *rule* covers, its
letters, its page in the book and the cells it reaches, changes rule by rule
and lives in `data/sarf/ilal.json`; the templates live in
`data/sarf/patterns.json`. Nothing about a rule is written in code, and
nothing about the alphabet is written in the data.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

# Everything that is written on a letter rather than beside it: the three
# vowels, the tanwin, sukun, shaddah and the small standing alif. Kept as one
# set so a mark is never mistaken for a letter of the root.
MARKS = frozenset("ًٌٍَُِّْٰ")

FATHAH, DAMMAH, KASRAH, SUKUN, SHADDAH = "َ", "ُ", "ِ", "ْ", "ّ"

# The alphabet facts every rule leans on, named once so no two files can hold
# different ideas of what a weak letter is.
WEAK = "وي"          # the two weak letters, و and ي
ALIF = "ا"           # what a weak letter turns into
MAQSURA = "ى"        # the alif written short, at the end of a word
LONG = ALIF + WEAK   # the three that can carry a long vowel
HAMZAH = "أإؤئء"     # every seat a hamzah is written on, and the bare one

# The jobs a letter can hold. Radicals are numbered: r1 is the first root
# letter. Everything the pattern itself adds is `pattern`; what the person
# endings add is `prefix` or `suffix`.
RADICAL = "r"
PATTERN = "pattern"
PREFIX = "prefix"
SUFFIX = "suffix"


@dataclass(frozen=True)
class Letter:
    """One consonant and the marks written on it."""

    letter: str
    marks: str = ""
    role: str = PATTERN

    @property
    def radical(self) -> int | None:
        """Which root letter this is (1-based), or None if the pattern added it."""
        return int(self.role[1:]) if self.role.startswith(RADICAL) else None

    @property
    def vowel(self) -> str:
        """The one vowel written on this letter, or "" for a bare letter."""
        return next((m for m in self.marks if m in (FATHAH, DAMMAH, KASRAH)), "")

    @property
    def doubled(self) -> bool:
        return SHADDAH in self.marks

    @property
    def silent(self) -> bool:
        """Carries a sukun, or carries nothing at all (a long vowel's alif)."""
        return SUKUN in self.marks or not self.marks

    def with_marks(self, marks: str) -> "Letter":
        return replace(self, marks=marks)

    def with_letter(self, letter: str) -> "Letter":
        """A different consonant in the same place, keeping its marks and job."""
        return replace(self, letter=letter)

    def with_vowel(self, vowel: str) -> "Letter":
        """The same letter with its vowel (or sukun) replaced, shaddah kept.

        Vowel first, shaddah after: that is the order Unicode itself sorts
        these two into, and the order every template in patterns.json is
        already written in, so a doubled letter compares equal wherever it was
        built.
        """
        return replace(self, marks=vowel + (SHADDAH if self.doubled else ""))


def build(segments: list[tuple[str, str]], radicals: str) -> list[Letter]:
    """Letters from templates, in order, with each letter's job attached.

    `segments` is the word in pieces, each piece a template and the job its own
    letters hold: [("ي", "prefix"), ("َ", "prefix"), ("{1}ْ{2}ُ{3}", "pattern"),
    ("ُ", "suffix")]. `{n}` is the nth root letter, and a mark always lands on
    the letter before it, whichever piece that letter came from, so a piece may
    be marks alone (the vowel on the مضارع prefix is written that way).
    """
    word: list[Letter] = []
    for template, role in segments:
        index = 0
        while index < len(template):
            char = template[index]
            if char == "{":
                close = template.index("}", index)
                number = int(template[index + 1:close])
                if number > len(radicals):
                    raise ValueError(f"template wants root letter {number}, root has {len(radicals)}")
                word.append(Letter(radicals[number - 1], role=f"{RADICAL}{number}"))
                index = close + 1
                continue
            if char in MARKS:
                if not word:
                    raise ValueError(f"a mark with no letter to sit on: {template!r}")
                word[-1] = word[-1].with_marks(word[-1].marks + char)
            else:
                word.append(Letter(char, role=role))
            index += 1
    return word


def render(word: list[Letter]) -> str:
    """The letters joined back into text, exactly as they will be printed."""
    return "".join(letter.letter + letter.marks for letter in word)


def find(word: list[Letter], radical: int) -> int | None:
    """Where the nth root letter sits now, or None if a rule deleted it."""
    return next((i for i, letter in enumerate(word) if letter.radical == radical), None)
