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
SHADDA = "ّ"
SHADDA_SUKUN = SHADDA + SUKUN
DAGGER_ALEF = "ٰ"
# case shown by an ending, not by a vowel: the plural and the dual
HIDDEN_CASE = ("ين", "ون", "ان")

CASE_NAME = {"u": "raf'", "a": "nasb", "i": "jarr"}
# CAMeL's own case letters, as the vowel each one is
CAMEL_CASE = {"n": "u", "a": "a", "g": "i"}


def letters(word: str) -> list[tuple[str, set]]:
    """The typed word as (letter, its marks) pairs."""
    out: list[tuple[str, set]] = []
    for char in word or "":
        if char in VOWEL or char in SHADDA_SUKUN or char == DAGGER_ALEF:
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
        # أَخِي: the kasra before ya al-mutakallim is the ya's, and the case is unseen
        if marked and marked[-1][0] == "ي":
            return None
        marked = marked[:-stuck_on]
    if len(marked) < 2 or "".join(letter for letter, _ in marked[-2:]) in HIDDEN_CASE:
        return None
    last = marked[-1]
    if last[0] in "اى" and marked[-2][1] & TANWEEN:
        last = marked[-2]  # the alef of رَجُلًا carries nothing; the tanween is before it
    return next((VOWEL[mark] for mark in last[1] if mark in VOWEL), None)


def has_tanween(word: str) -> bool:
    return any(marks & TANWEEN for _, marks in letters(word))


# The vowel a mark writes, so a fatha and a fathatan on the same letter still
# disagree (one is definite, one is not) while a missing mark agrees with anything.
# The dagger alef is a fatha said long: لٰكِنْ is what a reader types as لَكِنْ.
_MARK = {"َ": "a", "ُ": "u", "ِ": "i", "ً": "an", "ٌ": "un", "ٍ": "in", SUKUN: "o", DAGGER_ALEF: "a"}


def vowel_agreement(typed: str, reading: str) -> tuple[int, int] | None:
    """(how many vowels typed on a word a reading also has, how many letters both voweled
    that it doubles differently), or None when a typed vowel contradicts it (فَتَحَ against
    فَتْح, فَهِمَ against فَهْمَ: a sukun is an answer too).

    A letter the reading leaves bare agrees with whatever was typed on it. Letters are
    lined up with their hamza seats folded (آفِلًا is still checked against أَفَلَا); two
    spellings that do not line up even so say nothing either way, so they score nothing.
    A shadda is a doubled letter, not a vowel, and readers drop it, so it never contradicts;
    the second count is kept apart for best_reading to weigh (أَبُوْهُ is not أَبُّوهُ).
    """
    mine, theirs = letters(typed), letters(reading)
    if [bare_letters(c) for c, _ in mine] != [bare_letters(c) for c, _ in theirs]:
        return 0, 0
    agreed = doubled = 0
    for (_, said), (_, read) in zip(mine, theirs):
        said_v, read_v = {_MARK[m] for m in said if m in _MARK}, {_MARK[m] for m in read if m in _MARK}
        if not said or not read:
            continue
        if said_v and read_v and said_v != read_v:
            return None
        agreed += len(said_v & read_v) + (SHADDA in said and SHADDA in read)
        doubled += (SHADDA in said) != (SHADDA in read)
    return agreed, doubled


def best_reading(typed: str, readings: list[dict]) -> dict | None:
    """The reading the typed vowels support best, None when every reading contradicts them.
    Vowels the reader wrote are evidence the statistics lack: ranked alone, فَتَحَ came back
    as the noun فَتْح. A reading spelled with the very letters typed comes first, then the
    one doubling no letter otherwise than typed, then the one sharing most typed vowels,
    then the given (best first) order: a bare انك agrees with anything but must not beat
    إِنَّكَ, nor the أَلْبَاب sharing more vowels beat الْبَاب, nor أَبُّوهُ beat أَبُوه for أَبُوْهُ."""
    letters_typed = [c for c, _ in letters(typed)]
    scored = [((letters_typed == [c for c, _ in letters(r.get("diac", ""))], -found[1], found[0]), i)
              for i, r in enumerate(readings) if (found := vowel_agreement(typed, r.get("diac", ""))) is not None]
    return readings[max(scored, key=lambda pair: (pair[0], -pair[1]))[1]] if scored else None


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


def moved_for_wasl(word: str, after: str = "") -> bool:
    """A last kasra that may be a sukun moved (التقاء الساكنين): the sakin end meets the
    sakin after hamzat al-wasl (أَقِمِ الصَّلَاةَ، لم يَكْتُبِ الطالبُ، قَدِ اسْتَقَامَ). A noun's
    kasra of jarr looks the same (بِسْمِ اللَّهِ), so that kasra alone settles nothing."""
    return after.lstrip()[:1] in ("ا", "ٱ") and word.endswith("ِ")


def paused(word: str, after: str = "") -> str:
    """The word as said alone: a moved kasra back to the sukun a verb's shape is read by."""
    return word[:-1] + SUKUN if moved_for_wasl(word, after) else word


def command_shape(word: str, after_jazm: bool = False, hollow: bool = False) -> bool:
    """فعل أمر by its vowels: a sukun last, and either the voweled hamzat al-wasl before a
    sakin letter (اُكْتُبْ، اِجْلِسْ), two letters only, the hollow verb's (قُمْ، بِعْ، نَمْ),
    or Form IV's hamzat al-qat' with a fatha before a sakin letter (أَكْرِمْ، أَرْسِلْ).
    A present verb's prefix is never a bare voweled alef, and no past verb ends in a
    sukun on its own. Only the last shape is also a present verb, the first person's
    after a jazm particle (لم أَجْلِسْ), so `after_jazm` rules it out. A hollow Form IV
    command lost its middle letter (أَقِمْ، أَجِبْ): three letters, a kasra on the second,
    and only the root can tell it from a name (أَحْمَدْ), so the caller passes `hollow`."""
    marked = letters(word)
    if _plural_command(marked):
        return True
    if len(marked) < 2 or SUKUN not in marked[-1][1]:
        return False
    first, second = marked[0], marked[1]
    if len(marked) == 2:
        return bool(first[1] & {"َ", "ُ", "ِ"})
    if len(marked) == 3 and hollow:
        return first[0] == "أ" and "َ" in first[1] and "ِ" in second[1] and not after_jazm
    if SUKUN not in second[1]:
        return False
    return (first[0] == "ا" and bool(first[1] & {"ُ", "ِ"})) or (
        first[0] == "أ" and "َ" in first[1] and len(marked) >= 4 and not after_jazm)


def _plural_command(marked: list[tuple[str, set]]) -> bool:
    """اُكْتُبُوا، اعْبُدُوا: a command to many drops its nun and keeps واو الجماعة (Tasheel
    2.2 p27), so it ends وا, not in a sukun; it opens with hamzat al-wasl (its vowel often
    left untyped) before a sakin letter. A past verb with that opening is a longer form
    (اِجْتَمَعُوا، اِنْكَسَرُوا) and has a fatha on its middle root letter, a command never."""
    if len(marked) < 6 or [letter for letter, _ in marked[-2:]] != ["و", "ا"]:
        return False
    first, second = marked[0], marked[1]
    if first[0] != "ا" or (first[1] and not first[1] & {"ُ", "ِ"}) or SUKUN not in second[1]:
        return False
    return len(marked) == 6 or "َ" not in marked[-4][1]


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
