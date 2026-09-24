"""The book's rules, applied to a word after its pattern has been filled.

A pattern alone is not the whole of sarf. Once the root letters are in place
some of them cannot be said where they stand, and the book states, rule by
rule, what happens instead. قَوَلَ is not a word; قَالَ is. So the engine fills
the pattern, runs the rules over the letters in order, and prints the result.

Each rule is one function here and one entry in `data/sarf/ilal.json`, which
holds the letters it covers and the page it is read off. A rule reports itself
when it fires, so a form the reader cannot trace back to a page is impossible,
which is the guessing this app refuses. The order in the JSON is the order they
run in, and it is a pipeline order, not the book's numbering: a rule that feeds
another comes first.

`Context` is what a rule needs to know beyond the letters themselves: which
cell of the table is being built, and what the باب does to the middle letter in
its past tense, which is what decides the first letter's vowel later on.
"""
from __future__ import annotations

from typing import Callable, NamedTuple

from backend.services.sarf import word as W

# The alphabet is `word.py`'s to name; these two are used on almost every line
# below, so they are bound locally rather than spelt W.WEAK each time.
WEAK, ALIF = W.WEAK, W.ALIF

# A weak letter follows the vowel in front of it: after a كسرة it is written ي,
# after a ضمة و. Two rules of the book say this of different letters (rule 3 of
# any silent one, rules 11 and 12 of the last root letter), so the swap itself
# is named once here rather than typed out in both.
FOLLOWS_THE_VOWEL = {("و", W.KASRAH): "ي", ("ي", W.DAMMAH): "و"}


class Context(NamedTuple):
    form: str        # the باب key, e.g. "I-nasara"
    slot: str        # which column: madi, mudari, amr, nahy, madi-passive, mudari-passive
    kind: str        # the root's category: sahih, ajwaf, naqis, mithal, ...
    radicals: str    # the root letters as typed
    past_middle: str # the vowel the باب puts on the middle letter in the past


class Shaped(NamedTuple):
    letters: list[W.Letter]
    fired: list[str]      # rule ids, in the order they fired
    notes: list[str]      # what the book also allows, for the reader


def _weak_at(letters: list[W.Letter], index: int) -> bool:
    """Is this a و or ي standing as the middle or last root letter?

    The first root letter is excluded throughout: the book's first condition on
    rule 7 is that the letter must not be the فاء الكلمة (p.174), which is why
    تَوَفَّى keeps its و.
    """
    letter = letters[index]
    return letter.letter in WEAK and letter.radical in (2, 3)


# ── باب افتعال ───────────────────────────────────────────────────────────────

def iftial_taa(letters: list[W.Letter], rule: dict, context: Context):
    """The ت of افتعال changes after certain first letters, then may merge."""
    first = W.find(letters, 1)
    if first is None or first + 1 >= len(letters):
        return letters, None
    opener = letters[first].letter
    note = rule["variants"].get(opener)
    becomes = rule["becomes"].get(opener)
    if becomes is None:
        return letters, note

    letters = list(letters)
    letters[first + 1] = letters[first + 1].with_letter(becomes)
    if becomes == opener:
        # إدغام: the two are now one letter said twice, written once with a
        # shaddah carrying the ت's own vowel (p.105: اِطْتَلَبَ becomes اِطَّلَبَ).
        # The root letter is the one kept, so the word still knows where its
        # first radical is when a later rule looks for it.
        letters[first] = letters[first].with_marks(letters[first + 1].vowel + W.SHADDAH)
        del letters[first + 1]
    return letters, note


def iftial_weak_first(letters: list[W.Letter], rule: dict, context: Context):
    """A weak first root letter in افتعال becomes a ت and merges (p.169)."""
    first = W.find(letters, 1)
    if first is None or first + 1 >= len(letters):
        return letters, None
    if letters[first].letter not in WEAK or letters[first + 1].letter != "ت":
        return letters, None
    letters = list(letters)
    letters[first] = W.Letter("ت", letters[first + 1].vowel + W.SHADDAH, letters[first].role)
    del letters[first + 1]
    return letters, None


# ── مثال ─────────────────────────────────────────────────────────────────────

def mithal_drops_waw(letters: list[W.Letter], rule: dict, context: Context):
    """The و of a مثال falls out of the مضارع: يَوْعِدُ becomes يَعِدُ (p.166)."""
    if context.slot not in rule["slots"]:
        return letters, None
    first = W.find(letters, 1)
    if first is None or first + 1 >= len(letters):
        return letters, None
    if letters[first].letter != "و":
        return letters, None
    after = letters[first + 1].vowel
    throat = any(context.radicals[position] in rule["throat"] for position in (1, 2))
    if after != rule["after"] and not (after == W.FATHAH and throat):
        return letters, None
    letters = list(letters)
    del letters[first]
    return letters, None


# ── the rules that carry every أجوف and ناقص ────────────────────────────────

def transfer_vowel(letters: list[W.Letter], rule: dict, context: Context):
    """A vowel on a weak letter moves back onto the silent letter before it."""
    for index in range(1, len(letters)):
        before = letters[index - 1]
        if not _weak_at(letters, index) or not letters[index].vowel:
            continue
        if W.SUKUN not in before.marks or before.doubled:
            continue
        letters = list(letters)
        moved = letters[index].vowel
        letters[index - 1] = before.with_vowel(moved)
        # Rule 8.2 sits on the back of this one: when the vowel that moved was a
        # فتحة the weak letter becomes an alif (يُقْوَلُ, يُقَوْلُ, يُقَالُ). It is
        # done here because only a transfer can trigger it, never a فتحة that was
        # always there: دَعَوْتَ keeps its و.
        letters[index] = (W.Letter(ALIF, "", letters[index].role) if moved == W.FATHAH
                          else letters[index].with_vowel(W.SUKUN))
        return letters, None
    return letters, None


def past_passive_hollow(letters: list[W.Letter], rule: dict, context: Context):
    """The ماضي مجهول of an أجوف: the letter before the middle one is silenced
    and takes its vowel, whatever vowel it had of its own (p.184, rule 9).

    This is why قُوِلَ becomes قِوْلَ and then قِيْلَ. It differs from rule 8 only
    in that rule 8 waits for a letter that is already silent; here the book
    silences it.
    """
    if context.slot not in rule["slots"] or context.kind != "ajwaf":
        return letters, None
    index = W.find(letters, 2)
    if index is None or index == 0 or not letters[index].vowel:
        return letters, None
    letters = list(letters)
    letters[index - 1] = letters[index - 1].with_vowel(letters[index].vowel)
    letters[index] = letters[index].with_vowel(W.SUKUN)
    return letters, None


def silent_waw_after_kasrah(letters: list[W.Letter], rule: dict, context: Context):
    """A silent و after a كسرة becomes ي, a silent ي after a ضمة becomes و."""
    for index in range(1, len(letters)):
        letter = letters[index]
        # Rule 3 is not one of rule 7's, so it is not held to rule 7's
        # conditions: it reaches the first root letter too (يُيْسَرُ is يُوْسَرُ).
        if letter.letter not in WEAK or letter.radical is None or letter.doubled:
            continue
        if W.SUKUN not in letter.marks:
            continue
        becomes = FOLLOWS_THE_VOWEL.get((letter.letter, letters[index - 1].vowel))
        if becomes is None:
            continue
        letters = list(letters)
        letters[index] = letter.with_letter(becomes)
        return letters, None
    return letters, None


def weak_after_fathah_is_alif(letters: list[W.Letter], rule: dict, context: Context):
    """A و or ي with a فتحة before it becomes an alif (p.171)."""
    for index in range(1, len(letters)):
        # The book's rule is about a و or ي that is متحرك (p.171). A silent one
        # only becomes an alif through the transfer of rule 8, which does it
        # there, so دَعَوْتَ is left alone.
        if not _weak_at(letters, index) or not letters[index].vowel:
            continue
        # Two weak letters in one root: the book's second condition on rule 7
        # blocks the change for the MIDDLE letter only (طَوَى keeps its و, p.175);
        # its last letter still becomes an alif, which is why the book prints
        # وَقَى and طَوَى rather than وَقَيَ and طَوَيَ.
        if letters[index].radical == 2 and context.kind.startswith("lafif"):
            continue
        if letters[index - 1].vowel != W.FATHAH:
            continue
        # The alif of the dual stands right after the weak letter and blocks
        # the change: دَعَوَا stays as it is (p.175, condition 3).
        if index + 1 < len(letters) and letters[index + 1].letter == rule["blocked-before"]:
            continue
        letters = list(letters)
        letters[index] = W.Letter(ALIF, "", letters[index].role)
        return letters, None
    return letters, None


def final_weak_endings(letters: list[W.Letter], rule: dict, context: Context):
    """A weak last root letter meeting a person's ending (p.189-192, rule 10).

    Three shapes. The ending is that same letter again and the vowel before it
    already agrees, so the pair reduces to one (يَدْعُوْنَ). The two do not agree,
    so the weak letter's vowel moves back and the letter itself goes
    (تَدْعِيْنَ, يَرْمُوْنَ, دُعُوْا). Or nothing follows it at all, and it simply goes
    silent (يَدْعُوْ, يَرْمِيْ), which the book states of the مضارع only.
    """
    index = W.find(letters, 3)
    if index is None or index == 0 or letters[index].letter not in WEAK:
        return letters, None
    letter, before = letters[index], letters[index - 1]
    if not letter.vowel:
        return letters, None
    agrees = before.vowel == rule["agrees"][letter.letter]
    after = letters[index + 1] if index + 1 < len(letters) else None

    if after is None:
        # Nothing follows but the case vowel, so the weak letter goes silent.
        # Where a letter does follow, even the alif of the dual, the rule does
        # not reach it and the vowel stays: يَدْعُوَانِ.
        if context.slot in rule["slots"] and before.vowel in (W.DAMMAH, W.KASRAH):
            letters = list(letters)
            letters[index] = letter.with_vowel(W.SUKUN)
        return letters, None

    if after.letter not in WEAK:
        return letters, None

    if after.letter == letter.letter and agrees:
        letters = list(letters)
        letters[index] = letter.with_vowel(W.SUKUN)
        del letters[index + 1]
        return letters, None

    letters = list(letters)
    letters[index - 1] = before.with_vowel(letter.vowel)
    del letters[index]
    return letters, None


def last_weak_follows_the_vowel(letters: list[W.Letter], rule: dict, context: Context):
    """A last root letter و after a كسرة becomes ي, and ي after a ضمة becomes و
    (p.192-193, rules 11 and 12): دُعِوَ is دُعِيَ."""
    index = W.find(letters, 3)
    if index is None or index == 0:
        return letters, None
    becomes = FOLLOWS_THE_VOWEL.get((letters[index].letter, letters[index - 1].vowel))
    if becomes is None:
        return letters, None
    letters = list(letters)
    letters[index] = letters[index].with_letter(becomes)
    return letters, None


def jussive_drops_last_weak(letters: list[W.Letter], rule: dict, context: Context):
    """A مجزوم loses its last weak letter altogether: لِيَدْعُ, لاَ يَدْعُ (p.243).

    The مجزوم ending is a sukun, and a weak letter carrying it at the end of the
    word is simply dropped, the way the sound verb drops its final vowel.
    """
    if context.slot not in rule["slots"]:
        return letters, None
    index = W.find(letters, 3)
    if index is None or index != len(letters) - 1:
        return letters, None
    if letters[index].letter not in WEAK + ALIF or letters[index].vowel:
        return letters, None
    return letters[:-1], None


def final_alif_is_written_maqsura(letters: list[W.Letter], rule: dict, context: Context):
    """An alif standing at the end of a word is written ى, not ا.

    The one exception the book's paradigms show is the past tense of a root
    whose last letter is و, which keeps the full alif: دَعَا against يُدْعَى.
    """
    if not letters or letters[-1].letter != ALIF or letters[-1].radical != 3:
        return letters, None
    if context.slot in rule["keeps-alif"] and context.radicals[-1] == "و":
        return letters, None
    letters = list(letters)
    letters[-1] = letters[-1].with_letter(W.MAQSURA)
    return letters, None


def late_waw_is_ya(letters: list[W.Letter], rule: dict, context: Context):
    """A و standing fourth in the word or later becomes ي, unless a ضمة or a
    silent و comes before it (p.205, rule 20): يُدْعَوَانِ is يُدْعَيَانِ."""
    index = W.find(letters, 3)
    if index is None or index < rule["from-position"] - 1 or letters[index].letter != "و":
        return letters, None
    before = letters[index - 1]
    if before.vowel == W.DAMMAH or (before.letter == "و" and before.silent):
        return letters, None
    letters = list(letters)
    letters[index] = letters[index].with_letter("ي")
    return letters, None


def alif_drops_before_silence(letters: list[W.Letter], rule: dict, context: Context):
    """An alif that came from a weak letter falls away (p.177, p.181)."""
    for index, letter in enumerate(letters):
        if letter.letter != ALIF or letter.radical not in (2, 3):
            continue
        after = letters[index + 1] if index + 1 < len(letters) else None
        if after is None:
            continue
        # Silent letter after it, or the ت of the feminine past, which deletes
        # the alif even though it carries a vowel of its own (7.3).
        feminine = after.role == W.SUFFIX and after.letter == rule["taa"]
        if after.silent or feminine:
            letters = list(letters)
            del letters[index]
            return letters, None
    return letters, None


def weak_drops_before_silence(letters: list[W.Letter], rule: dict, context: Context):
    """A silent و or ي falls away before another silent letter (p.180)."""
    for index in range(len(letters) - 1):
        letter, after = letters[index], letters[index + 1]
        if not _weak_at(letters, index) or letter.doubled:
            continue
        # An explicit sukun on the next letter, not merely a letter with no
        # marks: the app prints no case endings, so a bare last letter is not a
        # silent one, and مَبِيْع would lose its ي.
        if W.SUKUN not in letter.marks or W.SUKUN not in after.marks:
            continue
        # The alif written after a plural و is not a letter being said; the
        # weak letter before it stays (لِيَدْعُوْا).
        if after.letter == ALIF and after.role == W.SUFFIX:
            continue
        letters = list(letters)
        del letters[index]
        return letters, None
    return letters, None


def past_first_vowel(letters: list[W.Letter], rule: dict, context: Context):
    """Once the middle letter has gone from a past tense, the first root letter
    takes a ضمة or a كسرة of its own (p.177-178, p.186-187).

    Which one is decided by the معروف, never by the cell in hand, which is why
    the مجهول of قَالَ is قُلْنَ and not قِلْنَ.
    """
    if context.slot not in rule["slots"] or W.find(letters, 2) is not None:
        return letters, None
    first = W.find(letters, 1)
    if first is None or context.kind != "ajwaf":
        return letters, None
    middle = context.radicals[1]
    vowel = W.DAMMAH if middle == "و" and context.past_middle != W.KASRAH else W.KASRAH
    if letters[first].vowel == vowel:
        return letters, None
    letters = list(letters)
    letters[first] = letters[first].with_vowel(vowel)
    return letters, None


def doubled_letters_merge(letters: list[W.Letter], rule: dict, context: Context):
    """A root whose last two letters are the same: they become one letter with
    a shaddah (p.284-290, rules 2 to 5).

    Which of the book's three ways it happens depends only on what stands
    before the pair: a vowelled letter, and the first of the pair simply goes
    silent (مَدَدَ, مَدَّ); a silent letter, and the first one's vowel moves back
    onto it (يَمْدُدُ, يَمُدُّ); a long vowel, and nothing moves (حَاجَجَ, حَاجَّ).

    Rule 5 is the other half: when the second of the pair would be silent the
    two are written apart instead (مَدَدْنَ, يَمْدُدْنَ), unless the word ends
    there, where the book merges them and gives the letter a فتحة (لَمْ يَمُدَّ)
    and names the other readings it allows.
    """
    second = W.find(letters, 3)
    if second is None or second == 0:
        return letters, None
    first = second - 1
    if letters[first].letter != letters[second].letter or letters[first].radical != 2:
        return letters, None

    note = None
    pausing = W.SUKUN in letters[second].marks
    if pausing and (second != len(letters) - 1 or context.slot not in rule["pause-slots"]):
        # A real sukun on the second letter and the word carries on: the two
        # are written apart (مَدَدْنَ). Returned untouched, not as a copy, so
        # `apply` does not record this rule as having fired.
        return letters, None

    letters = list(letters)
    if pausing:
        # The word ends here, so the book merges the pair after all and gives
        # the letter a فتحة, naming the other readings it allows.
        letters[second] = letters[second].with_vowel(W.FATHAH)
        note = rule["pause-note"]

    before = letters[first - 1] if first else None
    if before is not None and before.silent and before.letter not in W.LONG:
        letters[first - 1] = before.with_vowel(letters[first].vowel)
    letters[first] = W.Letter(letters[second].letter,
                              letters[second].vowel + W.SHADDAH, letters[first].role)
    del letters[second]
    return letters, note


def doer_of_hollow_takes_hamzah(letters: list[W.Letter], rule: dict, context: Context):
    """The اسم الفاعل of an أجوف carries a hamzah where the root has its weak
    letter, because the verb itself changed: قَاوِل is قَائِل, بَايِع is بَائِع
    (p.202, rule 17)."""
    if context.slot not in rule["slots"] or context.kind != "ajwaf":
        return letters, None
    index = W.find(letters, 2)
    if index is None or letters[index].letter not in WEAK:
        return letters, None
    letters = list(letters)
    letters[index] = letters[index].with_letter(rule["becomes"])
    return letters, None


def done_to_of_hollow(letters: list[W.Letter], rule: dict, context: Context):
    """The اسم المفعول of an أجوف: the two silent letters cannot both be said,
    so one goes, and after a ي the letter before it takes a كسرة (p.182).

    مَقْوُوْل becomes مَقُوْل, مَبْيُوْع becomes مَبِيْع.
    """
    if context.slot not in rule["slots"] or context.kind != "ajwaf":
        return letters, None
    index = W.find(letters, 2)
    if index is None or index + 1 >= len(letters) or letters[index].letter not in WEAK:
        return letters, None
    if not letters[index].silent or not letters[index + 1].silent:
        return letters, None
    letters = list(letters)
    if letters[index].letter == "ي":
        letters[index - 1] = letters[index - 1].with_vowel(W.KASRAH)
        del letters[index + 1]
    else:
        del letters[index]
    return letters, None


def same_letters_at_the_end_merge(letters: list[W.Letter], rule: dict, context: Context):
    """Two of the same letter ending a word are written once with a shaddah:
    مَدْعُووٌ is مَدْعُوٌّ (p.284, rule 1 of the doubled root)."""
    if len(letters) < 2 or letters[-1].letter != letters[-2].letter:
        return letters, None
    if not letters[-2].silent:
        return letters, None
    letters = list(letters)
    letters[-2] = letters[-1].with_marks(letters[-1].vowel + W.SHADDAH)
    return letters[:-1], None


def hamzah_becomes_long_vowel(letters: list[W.Letter], rule: dict, context: Context):
    """A silent hamzah right after the alif that opens a word becomes the long
    vowel matching that alif's own vowel (p.147, rules 1 and 2).

    أَأْمَنَ is آمَنَ, أُأْمِنَ is أُومِنَ, إِئْمَانًا is إِيمَانًا, and in the same way
    اِأْتَمَرَ is إِيْتَمَرَ and اُأْتُمِرَ is أُوْتُمِرَ.
    """
    index = W.find(letters, 1)
    if index != 1 or letters[index].letter not in W.HAMZAH:
        return letters, None
    if letters[index].vowel or letters[0].letter not in rule["openers"]:
        return letters, None
    becomes = rule["after"].get(letters[0].vowel)
    if becomes is None:
        return letters, None
    letters = list(letters)
    # An alif standing for a long vowel is written bare, which is what lets the
    # فتحة before it pull the pair together into the one letter آ (أَأْمَنَ is
    # آمَنَ, not أَاْمَنَ). A و or ي keeps the sukun the book prints on it: أُوْمِنَ.
    marks = "" if becomes == ALIF else letters[index].marks
    letters[index] = W.Letter(becomes, marks, letters[index].role)
    return letters, None


def hamzah_amr(letters: list[W.Letter], rule: dict, context: Context):
    """The أمر of a hamzated verb (p.152, rule 7; p.159).

    Where the hamzah is the middle root letter the book moves its vowel onto
    the letter before it and drops it: اِسْأَلْ is سَلْ, اِزْأِرْ is زِرْ. Three verbs
    do the same with a first-letter hamzah, and the book names them.
    """
    if context.slot != "amr":
        return letters, None
    named = context.radicals in rule["drop-first"] and context.form in rule["drop-first-forms"]
    index = W.find(letters, 1 if named else 2)
    if index is None or index == 0 or letters[index].letter not in W.HAMZAH:
        return letters, None
    letters = list(letters)
    if letters[index].vowel:
        letters[index - 1] = letters[index - 1].with_vowel(letters[index].vowel)
    del letters[index]
    return letters, rule["note"]


def hamzah_madd(letters: list[W.Letter], rule: dict, context: Context):
    """A hamzah with a فتحة on it, followed by a bare alif, is written as the
    one letter آ: أَاخِذ is آخِذ (p.147)."""
    for index in range(len(letters) - 1):
        letter, after = letters[index], letters[index + 1]
        if letter.letter not in W.HAMZAH or letter.vowel != W.FATHAH:
            continue
        if after.letter != ALIF or after.marks:
            continue
        letters = list(letters)
        letters[index] = W.Letter(rule["madd"], "", letter.role)
        del letters[index + 1]
        return letters, None
    return letters, None


def hamzah_seat(letters: list[W.Letter], rule: dict, context: Context):
    """Which letter a hamzah is written on (p.156-157).

    The seat follows whichever is the stronger of the hamzah's own vowel and
    the vowel before it: a كسرة gives ئ, a ضمة ؤ, a فتحة ا. At the head of a
    word the hamzah stands on its own alif, so it is left as it is.
    """
    strength = rule["strength"]
    for index in range(1, len(letters)):
        letter = letters[index]
        if letter.letter not in rule["hamzah"]:
            continue
        own, before = letter.vowel, letters[index - 1].vowel
        pick = own if strength.get(own, 0) >= strength.get(before, 0) else before
        seat = rule["seats"].get(pick)
        if seat is None or seat == letter.letter:
            continue
        letters = list(letters)
        letters[index] = letter.with_letter(seat)
        return letters, None
    return letters, None


def joining_alif_drops(letters: list[W.Letter], rule: dict, context: Context):
    """The alif that only exists to start a silent letter goes once that letter
    has a vowel: اُقْوُلْ becomes قُلْ (p.224). A doubled letter keeps it."""
    if not letters or letters[0].letter != ALIF or letters[0].role != W.PATTERN:
        return letters, None
    if len(letters) < 2 or letters[1].silent or letters[1].doubled:
        return letters, None
    return letters[1:], None


RULES: dict[str, Callable[[list[W.Letter], dict, Context], tuple[list[W.Letter], str | None]]] = {
    "iftial-taa": iftial_taa,
    "iftial-weak-first": iftial_weak_first,
    "mithal-drops-waw": mithal_drops_waw,
    "transfer-vowel": transfer_vowel,
    "past-passive-hollow": past_passive_hollow,
    "silent-waw-after-kasrah": silent_waw_after_kasrah,
    "weak-after-fathah-is-alif": weak_after_fathah_is_alif,
    "final-weak-endings": final_weak_endings,
    "last-weak-follows-the-vowel": last_weak_follows_the_vowel,
    "late-waw-is-ya": late_waw_is_ya,
    "jussive-drops-last-weak": jussive_drops_last_weak,
    "final-alif-is-written-maqsura": final_alif_is_written_maqsura,
    "alif-drops-before-silence": alif_drops_before_silence,
    "weak-drops-before-silence": weak_drops_before_silence,
    "past-first-vowel": past_first_vowel,
    "doubled-letters-merge": doubled_letters_merge,
    "doer-of-hollow-takes-hamzah": doer_of_hollow_takes_hamzah,
    "done-to-of-hollow": done_to_of_hollow,
    "same-letters-at-the-end-merge": same_letters_at_the_end_merge,
    "hamzah-becomes-long-vowel": hamzah_becomes_long_vowel,
    "hamzah-amr": hamzah_amr,
    "hamzah-madd": hamzah_madd,
    "hamzah-seat": hamzah_seat,
    "joining-alif-drops": joining_alif_drops,
}


def apply(letters: list[W.Letter], config: dict, context: Context) -> Shaped:
    """Run every rule this word can trigger, in the order the JSON lists them.

    `config` is the `rules` object of `data/sarf/ilal.json`, passed in rather
    than read here: this module has no file of its own to open.

    A rule that did not change the word must hand back the very list it was
    given; that is how `fired` stays a true record of which rules shaped this
    cell, and `tests/test_ilal.py` holds each rule to it.
    """
    fired, notes = [], []
    for rule_id, rule in config.items():
        if "forms" in rule and context.form not in rule["forms"]:
            continue
        run = RULES.get(rule_id)
        if run is None:
            raise ValueError(f"ilal.json names a rule with no function: {rule_id}")
        shaped, note = run(letters, rule, context)
        if shaped is not letters:
            fired.append(rule_id)
        if note and note not in notes:
            notes.append(note)
        letters = shaped
    return Shaped(letters, fired, notes)
