"""The book's rules for reshaping a filled pattern, written down as tests.

The reference is *From the Treasures of Arabic Morphology*, باب افتعال, Rules 1
to 3 on pp.105 to 108. The ت of the pattern cannot be said after certain first
root letters, so it changes, and where it then matches that letter the two
merge. Before this, the app printed اِصْتَبَرَ and اِطْتَلَبَ, which are not words.
"""
from __future__ import annotations

import pytest

from backend.services import conjugation


def madi(radicals: str) -> str:
    return conjugation.conjugate(radicals, "VIII")["rows"][0]["cells"]["madi"]


@pytest.mark.parametrize(
    "radicals,expected,why",
    [
        # p.105 Rule 1: after د, ذ or ز the ت becomes a د.
        ("درس", "اِدَّرَسَ", "د: the two دs merge, the book calls إدغام compulsory"),
        ("ذكر", "اِذْدَكَرَ", "ذ: the book's third permissible spelling, left unmerged"),
        ("زجر", "اِزْدَجَرَ", "ز: the book's own example, left unmerged"),
        # pp.106-107 Rule 2: after ص, ض, ط or ظ the ت becomes a ط.
        ("صبر", "اِصْطَبَرَ", "ص: the book's own example"),
        ("ضرب", "اِضْطَرَبَ", "ض: the book's own example"),
        ("طلب", "اِطَّلَبَ", "ط: the two طs merge, compulsory on p.106"),
        ("ظلم", "اِظْطَلَمَ", "ظ: the book's second permissible spelling"),
        # p.107 Rule 3 is permissible, not compulsory, so the plain form stays.
        ("ثبت", "اِثْتَبَتَ", "ث: only permissible, so the pattern is left alone"),
        # A first letter no rule names is untouched: p.105's own paradigm verb.
        ("جنب", "اِجْتَنَبَ", "ج: no rule applies"),
    ],
)
def test_the_taa_of_iftial_follows_the_book(radicals: str, expected: str, why: str) -> None:
    assert madi(radicals) == expected, why


def test_the_change_runs_through_every_cell_not_just_the_past() -> None:
    table = conjugation.conjugate("طلب", "VIII")
    cells = table["rows"][0]["cells"]
    assert cells["mudari"] == "يَطَّلِبُ"
    assert cells["amr"] == "لِيَطَّلِبْ"
    assert cells["madi-passive"] == "اُطُّلِبَ"
    assert [slot["arabic"] for slot in table["summary"][:3]] == ["اِطَّلَبَ", "يَطَّلِبُ", "اِطِّلَاب"]


def test_the_book_s_other_allowed_spellings_are_named_not_hidden() -> None:
    assert conjugation.conjugate("ذكر", "VIII")["notes"] == [
        "اِدَّكَرَ and اِذَّكَرَ, both with إدغام, are also allowed (p.105)."
    ]


def test_a_root_no_rule_touches_carries_no_note() -> None:
    assert conjugation.conjugate("جنب", "VIII")["notes"] == []


def test_the_other_babs_are_left_alone() -> None:
    # The rule is written for باب افتعال only: صبر in باب نصر keeps its ص and
    # gains no ط, so no rule may fire on a form it was not written for.
    assert conjugation.conjugate("صبر", "I-nasara")["rows"][0]["cells"]["madi"] == "صَبَرَ"
    assert conjugation.conjugate("صبر", "I-nasara")["notes"] == []


def test_a_rule_named_in_the_data_with_no_function_is_loud() -> None:
    from backend.services.sarf import ilal, word

    context = ilal.Context("VIII", "madi", "sahih", "كتب", word.FATHAH)
    with pytest.raises(ValueError, match="no function"):
        ilal.apply(word.build([("{1}{2}{3}", word.PATTERN)], "كتب"),
                   {"not-written-yet": {"forms": ["VIII"]}}, context)


# ── the two halves stay in step ──────────────────────────────────────────────

def test_every_rule_has_both_a_function_and_an_entry() -> None:
    """A rule is a function plus a data entry, and neither half works alone.

    The data->code direction is already loud (the test above). This is the
    other one: a function left in RULES with no entry in ilal.json would never
    be reached by `apply`, and nothing printed would look wrong, so the rule
    would quietly stop being applied.
    """
    import json

    from backend.services import conjugation
    from backend.services.sarf import ilal

    with open(conjugation._ILAL, encoding="utf-8") as handle:
        entries = json.load(handle)["rules"]
    assert set(ilal.RULES) == set(entries)


def test_a_rule_that_changed_nothing_is_not_recorded_as_having_fired() -> None:
    """`fired` is the record of which rules shaped a cell, so a rule that
    looked and walked away must not appear in it.

    مَدَدْنَ is the case: the two دs meet, the merging rule reads them, and the
    book leaves them written apart. مَدَّ, the row above it, is the nearest cell
    where the same rule does fire, and it must be recorded there.
    """
    from backend.services import conjugation
    from backend.services.sarf import ilal, word

    def fired(slot: str, ending: str) -> list[str]:
        shape = conjugation._rules()["forms"]["I-nasara"]
        context = ilal.Context("I-nasara", slot, "mudaaf", "مدد", word.FATHAH)
        letters = word.build([(shape[slot], word.PATTERN), (ending, word.SUFFIX)], "مدد")
        return ilal.apply(letters, conjugation._ilal_rules(), context).fired

    assert "doubled-letters-merge" not in fired("madi", "ْنَا")  # مَدَدْنَا
    assert "doubled-letters-merge" in fired("madi", "َ")         # مَدَّ


# ── the nouns of a hollow root, and a hamzah standing first ──────────────────

def summary_of(radicals: str, form: str) -> dict[str, str]:
    return {line["label"]: line["arabic"] for line in conjugation.summary(radicals, form)}


def test_the_doer_and_the_done_to_of_a_hollow_root() -> None:
    """Treasures p.202 (rule 17) and p.182: قَاوِل is قَائِل and مَقْوُوْل is مَقُوْل,
    بَايِع is بَائِع and مَبْيُوْع is مَبِيْع. The ي root is the nearer case, because
    only it puts a كسرة on the letter before.

    The book prints a sukun on the long vowel of مَقُوْل; the templates here
    write every long vowel bare (مَكْتُوب too), so the word is the same
    word and this test holds the app to its own notation."""
    qawl = summary_of("قول", "I-nasara")
    assert qawl["Doer (اسم الفاعل)"] == "قَائِل"
    assert qawl["Done to (اسم المفعول)"] == "مَقُول"

    bay = summary_of("بيع", "I-daraba")
    assert bay["Doer (اسم الفاعل)"] == "بَائِع"
    assert bay["Done to (اسم المفعول)"] == "مَبِيْع"


def test_a_hamzah_standing_first_becomes_a_long_vowel() -> None:
    """Treasures p.147, rules 1 and 2. أَأْمَنَ is آمَنَ, and أُأْمِنَ is أُوْمِنَ:
    the alif is written bare so the فتحة before it pulls the two into the one
    letter آ, while the و keeps the sukun the book prints on it."""
    amana = summary_of("أمن", "IV")
    assert amana["Past (ماضي)"] == "آمَنَ"
    assert amana["Command (أمر)"] == "آمِنْ"
    assert amana["Past passive (ماضي مجهول)"] == "أُوْمِنَ"
    assert amana["Verbal noun (مصدر)"] == "إِيْمَان"
