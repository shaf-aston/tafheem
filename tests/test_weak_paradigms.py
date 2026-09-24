"""The book's own weak-root paradigms, cell by cell, as the engine's yardstick.

`tests/fixtures/treasures/*.json` is *From the Treasures of Arabic Morphology*
pp.158 to 303 read off the page images: every paradigm the book prints for a
root that is not صحيح سالم. Two readers read each page independently and a third
settled every disagreement at the image, so a cell here is what the book prints,
not what anyone expected it to print.

A root type the engine cannot yet shape is listed in `conjugates` in
patterns.json, and its paradigms skip with a reason rather than fail: this file
is the scoreboard for that work, so it must say plainly what is not done yet.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.services import conjugation
from backend.services.sarf import word as W

FIXTURES = Path(__file__).parent / "fixtures" / "treasures"

# The book names a باب by its verb; patterns.json names it by a key.
BABS = {
    "نصر": "I-nasara", "ضرب": "I-daraba", "فتح": "I-fataha",
    "سمع": "I-samia", "كرم": "I-karuma", "حسب": "I-hasiba",
    "إفعال": "IV", "إفتعال": "VIII", "إستفعال": "X", "تفعيل": "II",
}


def bab_of(printed: str) -> str | None:
    """The form key for a باب the book names, or None if we cannot place it."""
    bare = conjugation.bare(printed).replace("باب", "").strip()
    return BABS.get(bare)


# The book writes a long vowel's letter with a sukun on it (يَقُوْلُ) and the app
# does not (يَقُولُ); it also writes لاَ where the app writes لَا. Neither is a
# different word, so both are levelled before comparing: what is being checked
# here is the morphology, not the typesetting.
LONG = {"و": W.DAMMAH, "ي": W.KASRAH, "ا": W.FATHAH}


def level(text: str) -> str:
    letters = W.build([(text, W.PATTERN)], "")
    # The seat a hamzah is written on (أ ؤ ئ) is spelling, not a different
    # letter, and the book varies its own: يُؤْخَذُ on p158, أُسْتُأْذِنَ on p162.
    letters = [W.Letter("أ", l.marks, l.role) if l.letter in "إؤئ" else l for l in letters]
    if letters and letters[0].letter in "أإ":
        # This publisher prints the joining alif with a hamzah glyph on it
        # (إِتَّقَدَ, أُتُّقِدَ) all through the book. همزة الوصل carries no hamzah,
        # so the app writes the bare alif; it is the same letter.
        letters[0] = W.Letter("ا", letters[0].marks, letters[0].role)
    out = []
    for index, letter in enumerate(letters):
        marks = letter.marks
        if letter.letter in LONG:
            marks = marks.replace(W.SUKUN, "")
        if letter.letter == "ا" and W.FATHAH in marks and out:
            # لاَ: the fathah is printed after the alif, the app puts it on the
            # lam before it. Same word, one glyph earlier.
            marks = marks.replace(W.FATHAH, "")
            out[-1] = out[-1] if W.FATHAH in out[-1] else out[-1] + W.FATHAH
        out.append(letter.letter + marks)
    return "".join(out)


# Cells where the book's own printing is wrong, kept here in the open rather
# than quietly skipped. Each one was read again at the image, and each is
# contradicted by the same form printed correctly elsewhere in the book.
MISPRINTS = {
    (222, "you (f)", "mudari"): "prints تَقُوْلِيْنِ with a كسرة on the ن; p229 prints تَبِيْعِيْنَ",
    (222, "you (f)", "mudari-passive"): "same كسرة on the ن; p229 prints تُبَاعِيْنَ",
    (218, "he", "madi"): "prints وَمَقَ, but this is باب حَسِبَ, whose past carries a كسرة",
    (265, "you (f)", "nahy"): "prints لاَ تَقِ with no ي; p255 prints لاَ تَرْمِيْ for the same shape",
}

# Through the weak-root chapters the book leaves the alif off a plural و in the
# أمر and the نهي: لِيَدْعُوْ, مُدُّوْ, إِرْمُوْ. It is not a rule, it is that
# chapter's typesetting, and the book itself prints بِيْعُوْا with the alif on
# p229. The app writes the alif everywhere, so a cell that differs by exactly
# that one letter is the book's omission, not a wrong form.
PLURAL_ALIF = ("amr", "nahy")


def book_left_the_plural_alif_off(column: str, book: str, engine: str) -> bool:
    return column in PLURAL_ALIF and level(engine) == level(book) + "ا"


# Rule 1 of the hamzah chapter (p.147) is permissible, not compulsory: a silent
# hamzah may be written as the long vowel matching the vowel before it, so
# يُؤْخَذُ may also be يُوْخَذُ. The book takes the option in some paradigms and not
# in others, printing يُؤْخَذُ on p158 and يُوْتَمَرُ on p162. The app prints the
# hamzah and names the other reading under the table, so both are right.
LONG_FOR = {W.FATHAH: "ا", W.DAMMAH: "و", W.KASRAH: "ي"}


def book_took_the_optional_hamzah_change(book: str, engine: str) -> bool:
    letters = W.build([(engine, W.PATTERN)], "")
    softened = []
    for index, letter in enumerate(letters):
        long = LONG_FOR.get(letters[index - 1].vowel) if index else None
        if letter.letter in "أؤئ" and not letter.vowel and long:
            letter = W.Letter(long, letter.marks, letter.role)
        softened.append(letter)
    return level(W.render(softened)) == level(book)


def paradigms() -> list[tuple[str, dict]]:
    found = []
    for path in sorted(FIXTURES.glob("*.json")):
        for entry in json.loads(path.read_text(encoding="utf-8")):
            if entry.get("rows"):
                found.append((f"p{entry['page']}-{entry.get('root', '?').replace(' ', '')}", entry))
    return found


CASES = paradigms()


def test_the_fixtures_are_there_and_were_read_from_the_book() -> None:
    assert len(CASES) > 20, "the book's paradigms are the only yardstick; do not let them go missing"


@pytest.mark.parametrize("name,entry", CASES, ids=[name for name, _ in CASES])
def test_the_engine_prints_what_the_book_prints(name: str, entry: dict) -> None:
    radicals = "".join(entry["root"].split())
    form = bab_of(entry.get("bab", ""))
    if form is None:
        pytest.skip(f"{entry.get('bab')} is not one of the أبواب the engine builds")

    if conjugation.kind(radicals) not in conjugation.conjugates():
        name = conjugation.root_type(radicals).split(":")[0]
        pytest.skip(f"{name} is not shaped yet (p{entry['page']}, {entry['root']})")

    table = conjugation.conjugate(radicals, form)
    ours = {row["person"]: row["cells"] for row in table["rows"]}
    if list(entry["rows"]) == ["he"]:
        # A صرف صغير line, not a grid: its أمر and نهي are the ones addressed to
        # you, which the book prints as خُذْ and لاَ تَأْخُذْ beside the third-person
        # past. Compare those two against the row they actually belong to.
        ours = dict(ours)
        ours["he"] = {**ours["he"], "amr": ours["you (m)"]["amr"], "nahy": ours["you (m)"]["nahy"]}
    wrong = [
        f"{person} {column}: book {want!r}, engine {ours[person][column]!r}"
        for person, cells in entry["rows"].items()
        for column, want in cells.items()
        if want not in ("(blank)", "⟨?⟩") and person in ours
        and (entry["page"], person, column) not in MISPRINTS
        and not book_left_the_plural_alif_off(column, want, ours[person][column])
        and not book_took_the_optional_hamzah_change(want, ours[person][column])
        and level(ours[person][column]) != level(want)
    ]
    assert not wrong, f"p{entry['page']} {entry['root']} ({entry.get('bab')}):\n  " + "\n  ".join(wrong)
