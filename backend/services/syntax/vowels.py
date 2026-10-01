"""The vowels a reader typed, read as evidence (a leaf: pure string work).

The parser is fed letters only, so the harakat are the one place case and a
passive verb can be read from. `naming` and `teacher` judge with these; the
parser layer (`catib_onnx`) uses them to pick among readings.
"""
from __future__ import annotations

from backend.services.arabic_text import bare_letters

VOWEL = {"ً": "a", "ٌ": "u", "ٍ": "i", "َ": "a", "ُ": "u", "ِ": "i"}
TANWEEN = {"ً", "ٌ", "ٍ"}
SUKUN = "ْ"
SHADDA_SUKUN = "ّ" + SUKUN
# case shown by an ending, not by a vowel: the plural and the dual
HIDDEN_CASE = ("ين", "ون", "ان")

CASE_NAME = {"u": "raf'", "a": "nasb", "i": "jarr"}


def letters(word: str) -> list[tuple[str, set]]:
    """The typed word as (letter, its marks) pairs."""
    out: list[tuple[str, set]] = []
    for char in word or "":
        if char in VOWEL or char in SHADDA_SUKUN:
            if out:
                out[-1][1].add(char)
        elif char.isalpha():
            out.append((char, set()))
    return out


def typed_case(word: str, stuck_on: int = 0) -> str | None:
    """Case read off the last typed vowel, or None when the reader left it bare.

    `stuck_on` is how many letters at the end belong to an attached pronoun, whose
    own vowel says nothing about the word: the fatha of حَالُكَ is the kaf's, and
    the case is the damma before it.
    """
    marked = letters(word)
    if stuck_on:
        marked = marked[:-stuck_on]
    if len(marked) < 2 or "".join(letter for letter, _ in marked[-2:]) in HIDDEN_CASE:
        return None
    last = marked[-1]
    if last[0] in "اى" and marked[-2][1] & TANWEEN:
        last = marked[-2]  # the alef of رَجُلًا carries nothing; the tanween is before it
    return next((VOWEL[mark] for mark in last[1] if mark in VOWEL), None)


def has_tanween(word: str) -> bool:
    return any(marks & TANWEEN for _, marks in letters(word))


def agrees_with_typed(typed: str, reading: str) -> bool:
    """False when a vowelled reading puts a different vowel on a letter the reader
    vowelled: آفِلًا is not the أَفَلَا typed. A letter either side left bare says
    nothing, and two spellings that do not line up letter for letter are not
    evidence either way."""
    mine, theirs = letters(typed), letters(reading)
    if [bare_letters(c) for c, _ in mine] != [bare_letters(c) for c, _ in theirs]:
        return True
    for (_, typed_marks), (_, read_marks) in zip(mine, theirs):
        # a sukun is an answer too: فَهِمَ is not the noun فَهْمَ
        said = {mark for mark in typed_marks if mark in VOWEL or mark == SUKUN}
        read = {mark for mark in read_marks if mark in VOWEL or mark == SUKUN}
        if said and read and said != read:
            return False
    return True


def _without_ending(marked: list[tuple[str, set]]) -> list[tuple[str, set]]:
    """The letters of a present verb before its plural or dual ending: the stem of
    يُعَلَّمُونَ and يُكْتَبَانِ, or of يُكْتَبْنَ (a nun after a bare letter)."""
    if "".join(letter for letter, _ in marked[-2:]) in HIDDEN_CASE:
        return marked[:-2]
    if marked[-1][0] == "ن" and SUKUN in marked[-2][1]:
        return marked[:-1]
    return marked


def typed_passive(word: str, present: bool) -> bool:
    """فُعِلَ and يُفْعَلُ by their vowels.

    A past verb never opens with a damma unless it is passive, so that one mark
    is enough. A present verb does (يُكَافِئُ is active), so there the fatha
    before the last stem letter is what separates يُكَافَأُ from it. The kasra of
    كُتِبَتِ sits on a root letter, not the last one, which is why the end is not read.
    """
    marked = letters(word)
    if len(marked) < 3 or "ُ" not in marked[0][1]:
        return False
    if not present:
        return True
    stem = _without_ending(marked)
    return len(stem) >= 3 and "َ" in stem[-2][1]


def command_shape(word: str) -> bool:
    """فعل أمر by its vowels, for a word already known to be a verb: a sukun last, and
    either the voweled hamzat al-wasl before a sakin letter (اُكْتُبْ، اِجْلِسْ) or two
    letters only, the hollow verb's (قُمْ، بِعْ، نَمْ). A present verb's prefix is never a
    bare voweled alef, and no past verb ends in a sukun on its own."""
    marked = letters(word)
    if len(marked) < 2 or SUKUN not in marked[-1][1]:
        return False
    first, second = marked[0], marked[1]
    if len(marked) == 2:
        return bool(first[1] & {"َ", "ُ", "ِ"})
    return first[0] == "ا" and bool(first[1] & {"ُ", "ِ"}) and SUKUN in second[1]


def past_passive_shape(word: str) -> bool:
    """فُعِلَ by its vowels alone: damma first, a kasra inside, fatha or sukun last
    (قُرِئَ، سُئِلَ، بُنِيَ، قُرِئَتْ). For a word the morphology could only call a name.
    A final ت is the verb's only when it is bare or carries the kasra of meeting a
    sakin (قُرِئَتِ), and not the ات of a plural (مُسْلِمَاتُ)."""
    marked = letters(word)
    if len(marked) < 3 or "ُ" not in marked[0][1] or marked[0][0] == "ا":
        return False
    letter, last = marked[-1]
    closes = "َ" in last or SUKUN in last or (
        letter == "ت" and marked[-2][0] != "ا" and last <= {"ِ"})
    return any("ِ" in marks for _, marks in marked[1:-1]) and closes
