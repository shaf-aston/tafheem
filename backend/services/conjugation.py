"""Conjugate a sound root from the templates in data/sarf/patterns.json.

Deterministic and offline: the same root and form always give the same table,
and nothing here asks an AI. A root that does not follow the sound pattern is
named as irregular and left alone rather than conjugated wrongly.

The shape of the table
----------------------
Not a list. A gardaan is a grid, the same fourteen persons read down the side,
and each tense or mood as its own column across the top, which is how every
madrasah book prints it, and the only layout where you can see that يُكْرِمُ and
لاَ يُكْرِمْ are the same word two ways. The reference is Treasures of Arabic
Morphology p.98, whose four columns are ماضي · مضارع · أمر · نهي; the two مجهول
columns beside them come from pp.29-39.

Above the grid sits the صرف صغير, the one-line summary of a باب that the book
gives at the head of each chapter (p.97): past, present, verbal noun, doer,
their passives, the command and the prohibition, in that order.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from backend.services.arabic_text import normalize_root
from backend.services.sarf import ilal
from backend.services.sarf import word as W

_SARF = Path(__file__).parent.parent / "data" / "sarf"
_PATTERNS = _SARF / "patterns.json"
_BABS = _SARF / "babs.json"
_ILAL = _SARF / "ilal.json"

# The two letters that can only ever be standing in for a real weak letter. A
# root never holds a bare ا: in قَالَ the middle letter is a و underneath, so an
# alif in what we were handed means the root is weak and we do not know which
# letter it truly is. Without this, قال was conjugated letter by letter into
# قَاَلَ, which is not a word.
HIDDEN = W.ALIF + W.MAQSURA
# Classifying a typed root is the one place the alif counts as weak, so the set
# is wider here than the two letters the rules act on. Built from word.py's
# alphabet rather than retyped, so the two can never drift apart.
WEAK = W.WEAK + HIDDEN
HAMZAH = W.HAMZAH + "آ"


@lru_cache(maxsize=1)
def _rules() -> dict:
    with open(_PATTERNS, encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def babs() -> dict:
    """babs.json: the six Form I babs and the source order to try them in. The
    one loader; verb_forms reads it from here rather than opening the file."""
    with open(_BABS, encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def _ilal_rules() -> dict:
    """ilal.json: the rules that reshape a filled pattern, and the letters each
    one covers. The one loader; `services/sarf/ilal.py` opens no file itself."""
    with open(_ILAL, encoding="utf-8") as handle:
        return json.load(handle)["rules"]


class Shaper:
    """Builds a word from pieces, runs the book's rules over it, and prints it.

    One per table, because the notes a rule leaves ("the book also allows…")
    belong to the whole table, not to each of its eighty-four cells. Which cell
    is being built is passed in with the pieces: a rule needs it, since the
    first letter of a past tense takes a vowel that no other cell takes.
    """

    def __init__(self, radicals: str, form: str) -> None:
        self.radicals, self.form, self.notes = radicals, form, []
        self.kind = kind(radicals)
        # The vowel this باب puts on the middle letter of its past tense. Read
        # off the template rather than stored twice, and it is what decides
        # قُلْنَ against قِلْنَ long after the middle letter itself has gone.
        built = W.build([(_rules()["forms"][form]["madi"], W.PATTERN)], radicals)
        middle = W.find(built, 2)
        self.past_middle = built[middle].vowel if middle is not None else ""

    def __call__(self, slot: str, *segments: tuple[str, str]) -> str:
        context = ilal.Context(self.form, slot, self.kind, self.radicals, self.past_middle)
        shaped = ilal.apply(W.build(list(segments), self.radicals), _ilal_rules(), context)
        for note in shaped.notes:
            if note not in self.notes:
                self.notes.append(note)
        return W.render(shaped.letters)


def forms(radicals: int | None = None) -> dict[str, str]:
    """Every باب the engine can conjugate: id -> human label.

    Given a root's letter count, only the أبواب that count can take; offering a
    three-letter root a quadriliteral باب leads to a table that cannot be built.
    """
    return {
        key: value["label"]
        for key, value in _rules()["forms"].items()
        if radicals is None or value.get("radicals", 3) == radicals
    }


def radicals_needed(form: str) -> int:
    """How many root letters this form is built from, three, or four."""
    return _rules()["forms"][form].get("radicals", 3)


def kind(radicals: str) -> str:
    """Which of the book's categories this root falls in. Treasures p.143-145.

    One name, decided in the book's own order: a hamzah or a doubled letter is
    named before any weak letter is looked for, and two weak letters make the
    root لفيف, which has to be read before the one-weak-letter names because
    those stop at the first weak letter they meet (وَقَي was being called مثال).
    """
    if any(letter in HAMZAH for letter in radicals):
        # A root with both a hamzah and a weak letter is its own chapter in the
        # book (pp.272-283), where the two sets of rules meet and the weak ones
        # take precedence. Named apart so it is not conjugated by halves.
        return "mahmuz-weak" if any(letter in WEAK for letter in radicals) else "mahmuz"
    if radicals[-2] == radicals[-1]:
        return "mudaaf"
    weak = [position for position, letter in enumerate(radicals) if letter in WEAK]
    if len(weak) > 1:
        return "lafif-maqrun" if weak[-1] - weak[-2] == 1 else "lafif-mafruq"
    return next(
        (name for position, name in ((0, "mithal"), (1, "ajwaf"), (2, "naqis"))
         if radicals[position] in WEAK),
        "sahih",
    )


def conjugates() -> list[str]:
    """The root kinds the rules can shape today. Everything else is refused."""
    return _rules()["conjugates"]


def root_type(radicals: str) -> str:
    """What kind of root this is, in the words the books use. Never empty."""
    return _rules()["irregular"][kind(radicals)]


def _fill(template: str, radicals: str) -> str:
    for index, letter in enumerate(radicals, start=1):
        template = template.replace(f"{{{index}}}", letter)
    return template


def _check(radicals: str, form: str) -> dict:
    """The shape for this form, or a ValueError the caller turns into a message."""
    rules = _rules()
    shape = rules["forms"].get(form)
    if shape is None:
        raise ValueError(f"Unknown verb form: {form}")

    wanted = shape.get("radicals", 3)
    if len(radicals) != wanted:
        raise ValueError(f"{shape['label']} is built from {wanted} root letters, not {len(radicals)}.")
    if hidden := set(radicals) & set(HIDDEN):
        # قال is not a root: its alif stands for a و or a ي and nothing in the
        # letters says which. Filling the templates with the alif itself made
        # قَاَلَ, which is not a word, so the reader is asked for the root.
        raise ValueError(
            f"{''.join(hidden)} is not a root letter: it stands for a و or a ي and the "
            "letters do not say which. Enter the root itself, like قول or رمي."
        )
    if kind(radicals) not in conjugates():
        raise ValueError(f"This root is {root_type(radicals)}, and its rules are not built yet.")
    return shape


def scale_name(form: str) -> str:
    """The باب's own name in ف ع ل, its مصدر, the way the books name the chapter.

    باب اِسْتِفْعَال, not اِسْتَفْعَلَ. Form I has no single مصدر, so it keeps the
    past-tense scale it is named by instead. Deliberately skips the soundness
    check: ف-ع-ل-ل repeats its last letter, and the scale is a name, not a root
    being conjugated.
    """
    shape = _rules()["forms"][form]
    letters = "فعل" if shape.get("radicals", 3) == 3 else "فعلل"
    if shape.get("masdar"):
        return _fill(shape["masdar"], letters)
    return _fill(shape["madi"], letters) + _rules()["persons"][0][1]


def madi_of(radicals: str, form: str) -> str | None:
    """This form's past tense for this root, or None if the form cannot take it."""
    try:
        shape = _check(radicals, form)
    except ValueError:
        return None
    return _fill(shape["madi"], radicals) + _rules()["persons"][0][1]


def summary(radicals: str, form: str, shaped: "Shaper | None" = None) -> list[dict[str, str]]:
    """The صرف صغير, a باب in one line, as the book heads its chapter with it."""
    shape = _check(radicals, form)
    rules = _rules()
    shaped = shaped or Shaper(radicals, form)
    he_madi, he_letter, he_mudari = rules["persons"][0][1], rules["persons"][0][2], rules["persons"][0][3]
    you_jussive = rules["jussive"][6]
    prefix, passive_prefix = shape["prefix"], rules["passive-prefix"]

    label, no = rules["slots"], rules["nahy-la"]
    slots = [
        ("madi", shaped("madi", (shape["madi"], W.PATTERN), (he_madi, W.SUFFIX))),
        ("mudari", shaped("mudari", (he_letter, W.PREFIX), (prefix, W.PREFIX),
                          (shape["mudari"], W.PATTERN), (he_mudari, W.SUFFIX))),
        ("masdar", shaped("masdar", (shape["masdar"], W.PATTERN)) if shape["masdar"] else None),
        ("fail", shaped("fail", (shape["fail"], W.PATTERN))),
        ("madi-passive", shaped("madi-passive", (shape["madi-passive"], W.PATTERN), (he_madi, W.SUFFIX))),
        ("mudari-passive", shaped("mudari-passive", (he_letter, W.PREFIX), (passive_prefix, W.PREFIX),
                                  (shape["mudari-passive"], W.PATTERN), (he_mudari, W.SUFFIX))),
        ("maful", shaped("maful", (shape["maful"], W.PATTERN))),
        ("amr", shaped("amr", (shape["amr"], W.PATTERN), (you_jussive, W.SUFFIX))),
        ("nahy", no + shaped("nahy", (rules["persons"][6][2], W.PREFIX), (prefix, W.PREFIX),
                             (shape["mudari"], W.PATTERN), (you_jussive, W.SUFFIX))),
    ]
    # باب كَرُمَ is intransitive, so the book gives it a صفة مشبهة where every
    # other باب gives an اسم الفاعل (Treasures p.88). A باب may rename any line
    # of its own صرف صغير that way; only the name changes, the line is the same.
    return [{"label": shape.get(f"{slot}-label", label[slot]), "arabic": arabic}
            for slot, arabic in slots if arabic]


def conjugate(radicals: str, form: str) -> dict:
    """The full gardaan as a grid: fourteen persons down, six columns across."""
    radicals = "".join(radicals.split())
    shape = _check(radicals, form)
    rules = _rules()

    shaped = Shaper(radicals, form)
    prefix, passive_prefix = shape["prefix"], rules["passive-prefix"]
    addressed = set(rules["addressed"])

    rows = []
    for index, (label, madi_end, letter, mudari_end) in enumerate(rules["persons"]):
        jussive = rules["jussive"][index]
        # The command of someone who is not being spoken to is لِ + the jussive;
        # only the six second-person rows use the أمر stem itself. Treasures p.98.
        jussed = shaped("nahy", (letter, W.PREFIX), (prefix, W.PREFIX),
                        (shape["mudari"], W.PATTERN), (jussive, W.SUFFIX))
        command = (shaped("amr", (shape["amr"], W.PATTERN), (jussive, W.SUFFIX))
                   if index in addressed else rules["amr-lam"] + jussed)
        rows.append({
            "person": label,
            "cells": {
                "madi": shaped("madi", (shape["madi"], W.PATTERN), (madi_end, W.SUFFIX)),
                "mudari": shaped("mudari", (letter, W.PREFIX), (prefix, W.PREFIX),
                                 (shape["mudari"], W.PATTERN), (mudari_end, W.SUFFIX)),
                "amr": command,
                "nahy": rules["nahy-la"] + jussed,
                "madi-passive": shaped("madi-passive", (shape["madi-passive"], W.PATTERN), (madi_end, W.SUFFIX)),
                "mudari-passive": shaped("mudari-passive", (letter, W.PREFIX), (passive_prefix, W.PREFIX),
                                         (shape["mudari-passive"], W.PATTERN), (mudari_end, W.SUFFIX)),
            },
        })

    # The notes are the book's own "this spelling is also allowed": they belong
    # under the table, not in a cell, and an empty list means no rule reshaped
    # anything, which is the ordinary sound-root case.
    return {"columns": rules["columns"], "rows": rows,
            "summary": summary(radicals, form, shaped), "notes": shaped.notes}


# Every Arabic mark except the shaddah. A shaddah is not a vowel, it doubles a
# letter, and once the vowels come off it is the only thing telling عَلَّمَ apart
# from عَلَمَ. Stripping it made the two look identical, so neither Form could
# be chosen and the tab silently fell back to Form I.
SHADDAH = chr(0x0651)
MARKS = "".join(chr(c) for c in [
    *range(0x0610, 0x061B),   # Qur’anic annotation signs
    *range(0x064B, 0x0651),   # fathah, dammah, kasrah, the tanwin
    *range(0x0652, 0x0660),   # sukun and the rest; the shaddah at 0x0651 is skipped
    0x0670,                   # the small standing alif
    *range(0x06D6, 0x06EE),   # the Qur’anic recitation marks
])
DIACRITICS = re.compile(f"[{MARKS}]")


def bare(text: str) -> str:
    """Vowels and the joining alif off, so two spellings of a word compare as one."""
    return DIACRITICS.sub("", text).replace("ٱ", "ا").strip()


def letters(text: str) -> str:
    """Just the letters, the shaddah too, since a root never carries one."""
    return bare(text).replace(SHADDAH, "")


def identify(word: str, radicals: str) -> str | None:
    """Which باب the reader typed, by rebuilding each one's past tense.

    Returns None when no form matches, or when several do and the word cannot
    choose between them, the six Form I baabs all spell their past tense the
    same way once the vowels come off.
    """
    typed = bare(word)
    matches = [
        form
        for form in forms()
        if (madi := madi_of(radicals, form)) and bare(madi) == typed
    ]
    return matches[0] if len(matches) == 1 else None


# ── Which باب, and whether there is a table at all ───────────────────────────

def radicals_of(text: str) -> str:
    """The bare root letters, however the root was written; كتب, ك-ت-ب, ك ت ب."""
    return letters(normalize_root(text))


def resolve_form(
    word: str,
    radicals: str,
    is_noun: bool,
    requested: str | None = None,
    known: str | None = None,
) -> tuple[str | None, str | None]:
    """Which باب to conjugate this word in, or the reason it has no table.

    Exactly one of the pair comes back: a form and no note, or a note and no
    form. The three refusals are ordered by how true they are, not by how easy
    they are to check, because the first one that applies is the one the reader
    is told.

    `is_noun` is the tagger's opinion, passed in rather than looked up, so
    nothing here has to know how words are tagged.

    The form precedence is: `requested` (the reader's own choice) beats
    `known` (a bab a dictionary source could name, see verb_forms.babs_of)
    beats `identify()` (worked out from the shape of the word). When none of
    the three names one, there is no table and no guess: the note says no
    dictionary records the bab and leaves the picker for the reader. This is
    the only place that chain is written; nothing else should reimplement it.
    """
    if len(radicals) not in (3, 4):
        return None, "Only three- and four-letter roots are conjugated, try the bare root, like كتب."

    if hidden := set(radicals) & set(HIDDEN):
        # Checked before anything else, because it is the truest thing we can
        # say: قال is not a root, and guessing whether its alif stands for a و
        # or a ي would be inventing the table.
        return None, (
            f"{''.join(hidden)} is not a root letter here: it stands for a و or a ي and "
            "the letters do not say which. Enter the root itself, like قول or رمي."
        )

    if kind(radicals) not in conjugates():
        return None, (
            f"This root is {root_type(radicals)}, and the book gives it its own chapter of "
            "rules, which are not built here yet. Rather than print a table that would be "
            "wrong, the tab says so."
        )

    if is_noun and bare(word) != radicals and not identify(word, radicals):
        # Typing كِتَاب used to produce a full table of كَتَبَ. It is a noun; its
        # root can be conjugated, but this word is not the verb.
        return None, (
            f"{word} is a noun (اسم), and conjugation tables are for verbs. "
            f"Its root {radicals} does conjugate, enter the root itself to see it."
        )

    if form := (requested or known or identify(word, radicals)):
        return form, None
    return None, f"No dictionary here records which باب {word} takes. Choose one below to see its table."
