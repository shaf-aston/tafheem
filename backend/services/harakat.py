"""The vowels a reader typed, read as evidence (a leaf: pure string work).

The parser is fed letters only, so the harakat are the one place case and a
passive verb can be read from. `naming` and `teacher` judge with these; the
parser layer (`catib_onnx`) uses them to pick among readings.
"""
from __future__ import annotations


from backend.services.arabic_text import bare_letters, strip_diacritics

VOWEL = {"ً": "a", "ٌ": "u", "ٍ": "i", "َ": "a", "ُ": "u", "ِ": "i"}
TANWEEN = {"ً", "ٌ", "ٍ"}
SUKUN = "ْ"
SHADDA = "ّ"
SHADDA_SUKUN = SHADDA + SUKUN
DAGGER_ALEF = "ٰ"
# the letters a present verb opens with; a bare alef is hamzat al-wasl (اِتَّقِ is a command)
PRESENT_PREFIX = set("أنيت")
# the long letters a weak root's last radical shows as (يَهْدِي، يَدْعُو، يَسْعَى، العَصَا)
WEAK_ENDS = set("اىوي")
# case shown by an ending, not by a vowel: the plural and the dual
HIDDEN_CASE = ("ين", "ون", "ان")
# the vowels their nun carries (the plural's fatha, the dual's kasra); any other
# (الدِّينُ، بَيَانٌ) is the word's own case
ENDING_NUN = {"ين": {"َ", "ِ"}, "ون": {"َ"}, "ان": {"ِ"}}
# a sound feminine plural ends so; its kasra also shows nasb (رأيت المعلماتِ)
FEM_PLURAL_END = "ات"
# تَفَعَّلَ: the three radicals that follow a Form V or VI verb's opening ت
FORM_V_STEM = 3

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


def own_letters(word: str, before: int, after: int) -> str:
    """The typed word less `before` letters joined in front (فـ) and `after` of an attached
    pronoun (ـها), its own vowels kept: فَاقْبَلْهَا is اقْبَلْ."""
    marked = letters(word)
    return "".join(letter + "".join(sorted(marks)) for letter, marks in marked[before:len(marked) - after])


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
    if len(marked) < 2:
        return None
    ending = "".join(letter for letter, _ in marked[-2:])
    if ending in HIDDEN_CASE and marked[-1][1] & VOWEL.keys() <= ENDING_NUN[ending]:
        return None
    last = marked[-1]
    if last[0] == "ى" and marked[-2][1] & TANWEEN:
        return None  # مُعَافًى، هُدًى: a مقصور noun's tanween is written so in every case, which is unseen
    if (last[0] == "ا" or (last[0] == "و" and not last[1])) and marked[-2][1] & TANWEEN:
        last = marked[-2]  # the alef of رَجُلًا and the written و of عَمْرٌو carry nothing; the tanween is before
    return next((VOWEL[mark] for mark in last[1] if mark in VOWEL), None)


def merged_prefix(word: str, merging: frozenset[str]) -> bool:
    """A present verb whose second ta' merged into the stem's first letter (تَطَّوَّعَ for
    تَتَطَوَّعَ): a ت with a fatha, then a letter of `merging` doubled, and the whole stem of
    Form V or VI after the ت. A past verb of those forms has no shadda there (تَطَوَّعَ),
    and a short doubled past (تَمَّ) has not the stem."""
    marked = letters(word)
    return (len(marked) > FORM_V_STEM and marked[0][0] == "ت" and "َ" in marked[0][1]
            and marked[1][0] in merging and SHADDA in marked[1][1])


def has_tanween(word: str) -> bool:
    return any(marks & TANWEEN for _, marks in letters(word))


def weak_radical(raw_root: str | None, place: int) -> bool:
    """Whether CAMeL's root has a weak letter (و or ي) as its radical at `place` (-1 last,
    1 middle). `#` is how CAMeL writes one (and a hamza too: see weak_last); a root read
    from sarf's table (verb_reader) comes in Arabic letters."""
    radicals = (raw_root or "").split(".")
    return len(radicals) == 3 and radicals[place] in ("#", "w", "y", "Y", "و", "ي")


def weak_last(analysis: dict) -> bool:
    """A CAMeL reading whose root ends in و or ي: the root says weak and the dictionary
    form ends in a long letter (دَعَا، رَمَى، نَسِيَ، القَاضِي), not a hamza (قَرَأَ، جَاءَ)."""
    return weak_radical(analysis.get("root"), -1) and strip_diacritics(analysis.get("lex") or "")[-1:] in WEAK_ENDS


def base_of(word: str, atbtok: str | None) -> str:
    """The typed word's bare letters less the ones CAMeL's split (atbtok, "وَ+_سَ+_يَكْتُب_+هُ")
    files as joined before ("+" after) or as an attached pronoun ("+" before). The letters
    stay the reader's: CAMeL's reading may spell them otherwise (اتَّقِ read as أَتَّقِي)."""
    bare = strip_diacritics(word)  # not bare_letters: it folds the أ of أَجْلِسُ into an alef
    pieces = [strip_diacritics(p) for p in (atbtok or "").split("_")]
    joined = "".join(p[:-1] for p in pieces if p.endswith("+"))
    pronoun = "".join(p[1:] for p in pieces if p.startswith("+"))
    stem = next((p for p in pieces if "+" not in p), "")
    middle = bare[len(joined):len(bare) - len(pronoun)]
    # the split is used only where its joined letters are the reader's own and the rest
    # opens with CAMeL's stem (أَخ for أخي); a letter written once (لِ+ال as لل, عَلَى+يَ
    # as عليّ) fails and the word stays whole
    fits = bare.startswith(joined) and bare.endswith(pronoun)
    return middle if stem and fits and bare_letters(middle).startswith(bare_letters(stem)) else bare


def drops_weak(base: str, weak_last: bool) -> bool:
    """The root ends in a weak letter the word no longer ends in (اِسْقِ، لم يَدْعُ): the
    book's sign of jazm for a present verb. `base` is the word without its joined letters.
    Not when the five verbs' nun stands (يُؤْتُونَ): the weak letter went before the plural
    waw, and the nun kept is the sign of raf'."""
    bare = strip_diacritics(base)
    return bool(weak_last) and bare[-1:] not in WEAK_ENDS and not bare.endswith(HIDDEN_CASE)


def five_verb_nun(word: str) -> str | None:
    """"kept" or "dropped": the nun of one of the five verbs, which shows the case in place
    of a vowel (يكتبون، تكتبين، يكتبان raf'; يكتبوا، يكتبا، تكتبي nasb or jazm), else None.
    A damma typed on the nun makes it the verb's own letter (يَبِينُ), and a fatha on a
    last ي makes it a weak root letter (لن يَمْشِيَ), not the ya of تكتبي."""
    bare, shown = strip_diacritics(word), typed_case(word)  # not bare_letters: it folds يقرأ's أ into an alef
    if shown == "u" or len(bare) < 4:
        return None
    if bare.endswith(HIDDEN_CASE):
        return "kept"
    if bare.endswith(("وا", "ا")) or (bare.startswith("ت") and bare.endswith("ي") and shown != "a"):
        return "dropped"
    return None


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

    A past verb's opening damma is passive only with the kasra of فُعِلَ inside it:
    a hollow verb takes the damma alone before its doer's تاء (كُنْتَ، قُلْتُ), and
    the last letter's kasra may be that تاء's (كُنْتِ). A present verb opens with a
    damma too (يُكَافِئُ is active), so there the fatha
    before the last stem letter is what separates يُكَافَأُ from it. The kasra of
    كُتِبَتِ sits on a root letter, not the last one, which is why the end is not read.
    """
    marked = letters(word)
    if len(marked) < 3 or "ُ" not in marked[0][1]:
        return False
    if not present:
        # or a doubled verb's shadda (حُفَّتْ، رُدَّ), not a ن's: كُنَّا is كان meeting نا
        return any("ِ" in marks or (SHADDA in marks and letter != "ن") for letter, marks in marked[1:-1])
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


ROOT_PLACES = "فعل"  # in a shape (أَفْعَلَ), the letters that stand for the root's


def fits_shape(word: str, shape: str, root: str = "") -> bool:
    """The word has this shape (أَفْعَلَ), by its letters, whatever vowels it was typed with: the
    letters outside the root are the shape's own (أ may be written ا), a vowel typed on a letter
    must be one the shape has, one left off is not held against it. A shadda in the shape is the root's
    doubled letter: typed, or (plain text) the analyser's root has its last two letters alike."""
    marked, wanted = letters(word), letters(shape)
    if len(marked) != len(wanted):
        return False
    for (letter, marks), (want, want_marks) in zip(marked, wanted):
        if want not in ROOT_PLACES and bare_letters(letter) != bare_letters(want):
            return False
        if not marks <= want_marks:
            return False
        if SHADDA in want_marks and SHADDA not in marks and not (len(root) == 3 and root[1] == root[2]):
            return False
    return True
