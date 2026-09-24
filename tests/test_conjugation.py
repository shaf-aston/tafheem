"""Pin the conjugation engine to the book it claims to follow.

The reference is *From the Treasures of Arabic Morphology* (Madrassah Inaamiyyah).
Page 98 prints باب إفعال for the root ك-ر-م as a grid, fourteen persons down,
ماضي · مضارع · أمر · نهي across, and every cell below was read off that page.
Page 97 prints the same باب's صرف صغير, its one-line summary.

These are not tests of what the code currently does. They are the book, written
down, so that a template edited in patterns.json cannot quietly stop matching it.
"""
from __future__ import annotations

import pytest

from backend.services import conjugation

# Treasures p.98, column الماضي المعروف, top to bottom.
MADI = [
    "أَكْرَمَ", "أَكْرَمَا", "أَكْرَمُوا", "أَكْرَمَتْ", "أَكْرَمَتَا", "أَكْرَمْنَ", "أَكْرَمْتَ",
    "أَكْرَمْتُمَا", "أَكْرَمْتُمْ", "أَكْرَمْتِ", "أَكْرَمْتُمَا", "أَكْرَمْتُنَّ", "أَكْرَمْتُ", "أَكْرَمْنَا",
]
# Column المضارع المعروف.
MUDARI = [
    "يُكْرِمُ", "يُكْرِمَانِ", "يُكْرِمُونَ", "تُكْرِمُ", "تُكْرِمَانِ", "يُكْرِمْنَ", "تُكْرِمُ",
    "تُكْرِمَانِ", "تُكْرِمُونَ", "تُكْرِمِينَ", "تُكْرِمَانِ", "تُكْرِمْنَ", "أُكْرِمُ", "نُكْرِمُ",
]
# Column الأمر المعروف. The persons who are not being spoken to take a لِ.
AMR = [
    "لِيُكْرِمْ", "لِيُكْرِمَا", "لِيُكْرِمُوا", "لِتُكْرِمْ", "لِتُكْرِمَا", "لِيُكْرِمْنَ", "أَكْرِمْ",
    "أَكْرِمَا", "أَكْرِمُوا", "أَكْرِمِي", "أَكْرِمَا", "أَكْرِمْنَ", "لِأُكْرِمْ", "لِنُكْرِمْ",
]
# Column النهي المعروف.
NAHY = [
    "لَا يُكْرِمْ", "لَا يُكْرِمَا", "لَا يُكْرِمُوا", "لَا تُكْرِمْ", "لَا تُكْرِمَا", "لَا يُكْرِمْنَ",
    "لَا تُكْرِمْ", "لَا تُكْرِمَا", "لَا تُكْرِمُوا", "لَا تُكْرِمِي", "لَا تُكْرِمَا", "لَا تُكْرِمْنَ",
    "لَا أُكْرِمْ", "لَا نُكْرِمْ",
]


@pytest.mark.parametrize(
    "column,expected",
    [("madi", MADI), ("mudari", MUDARI), ("amr", AMR), ("nahy", NAHY)],
)
def test_form_iv_matches_treasures_page_98(column: str, expected: list[str]) -> None:
    rows = conjugation.conjugate("كرم", "IV")["rows"]
    assert [row["cells"][column] for row in rows] == expected


def test_the_grid_is_fourteen_persons_and_six_columns() -> None:
    table = conjugation.conjugate("كرم", "IV")
    assert len(table["rows"]) == 14
    assert [c["id"] for c in table["columns"]] == [
        "madi", "mudari", "amr", "nahy", "madi-passive", "mudari-passive",
    ]


@pytest.mark.parametrize(
    "radicals,form,expected",
    [
        # p.97  أَكْرَمَ يُكْرِمُ إِكْرَامًا فَهُوَ مُكْرِمٌ وَأُكْرِمَ يُكْرَمُ ... أَكْرِمْ ... لاَ تُكْرِمْ
        ("كرم", "IV", ["أَكْرَمَ", "يُكْرِمُ", "إِكْرَام", "مُكْرِم", "أُكْرِمَ", "يُكْرَمُ", "مُكْرَم",
                       "أَكْرِمْ", "لَا تُكْرِمْ"]),
        # p.117 إِسْتَنْصَرَ يَسْتَنْصِرُ إِسْتِنْصَارًا ... وَأُسْتُنْصِرَ يُسْتَنْصَرُ ... لاَ تَسْتَنْصِرْ
        ("نصر", "X", ["اِسْتَنْصَرَ", "يَسْتَنْصِرُ", "اِسْتِنْصَار", "مُسْتَنْصِر", "اُسْتُنْصِرَ",
                      "يُسْتَنْصَرُ", "مُسْتَنْصَر", "اِسْتَنْصِرْ", "لَا تَسْتَنْصِرْ"]),
        # p.126 بَعْثَرَ يُبَعْثِرُ بَعْثَرَةً ... وَبُعْثِرَ يُبَعْثَرُ ... بَعْثِرْ ... لاَ تُبَعْثِرْ
        ("بعثر", "IQ", ["بَعْثَرَ", "يُبَعْثِرُ", "بَعْثَرَة", "مُبَعْثِر", "بُعْثِرَ", "يُبَعْثَرُ",
                        "مُبَعْثَر", "بَعْثِرْ", "لَا تُبَعْثِرْ"]),
    ],
)
def test_sarf_sagheer_matches_the_book(radicals: str, form: str, expected: list[str]) -> None:
    assert [slot["arabic"] for slot in conjugation.summary(radicals, form)] == expected


@pytest.mark.parametrize(
    "radicals,family",
    [("وعد", "مثال"), ("قول", "أجوف"), ("رمي", "ناقص"),
     ("مدد", "مضاعف"), ("سأل", "مهموز")],
)
def test_a_root_that_shifts_is_named_as_the_book_names_it(radicals: str, family: str) -> None:
    assert conjugation.root_type(radicals).startswith(family)


@pytest.mark.parametrize("radicals", ["رأي", "أوي"])
def test_a_root_whose_rules_are_not_built_is_refused_not_guessed(radicals: str) -> None:
    """Printing a table the rules cannot really make would be the guessing this
    app refuses, so the tab says which kind it is and stops."""
    assert conjugation.kind(radicals) not in conjugation.conjugates()
    with pytest.raises(ValueError):
        conjugation.conjugate(radicals, "I-nasara")


@pytest.mark.parametrize(
    "radicals,form,expected",
    [
        # Every one of these is the book's own printed form, and each needs a
        # different rule to reach: p222, p229, p241, p252, p262, p291, p214, p158.
        ("قول", "I-nasara", "قَالَ"), ("بيع", "I-daraba", "بَاعَ"),
        ("دعو", "I-nasara", "دَعَا"), ("رمي", "I-daraba", "رَمَى"),
        ("وقي", "I-daraba", "وَقَى"), ("مدد", "I-nasara", "مَدَّ"),
        ("وعد", "I-daraba", "وَعَدَ"), ("أخذ", "I-nasara", "أَخَذَ"),
    ],
)
def test_a_weak_root_is_conjugated_the_way_the_book_prints_it(
    radicals: str, form: str, expected: str
) -> None:
    assert conjugation.conjugate(radicals, form)["rows"][0]["cells"]["madi"] == expected


@pytest.mark.parametrize("radicals", ["قال", "رمى"])
def test_an_alif_hides_which_letter_it_is_so_the_root_is_asked_for(radicals: str) -> None:
    """قال is not a root: the alif stands for a و or a ي and the letters do not
    say which. Filled into the templates it made قَاَلَ, which is not a word."""
    with pytest.raises(ValueError, match="not a root letter"):
        conjugation.conjugate(radicals, "I-nasara")


def test_a_sound_root_is_not_refused() -> None:
    assert conjugation.root_type("كتب").startswith("صحيح سالم")


def test_a_quadriliteral_form_refuses_three_letters() -> None:
    """فَعْلَلَ needs four letters; handing it three must fail loudly, not silently
    produce a table with an empty slot in it."""
    with pytest.raises(ValueError, match="4 root letters"):
        conjugation.conjugate("كتب", "IQ")


def test_every_form_can_be_built() -> None:
    """No template may be half-written: each form must produce a full grid."""
    for form in conjugation.forms():
        radicals = "كتب" if conjugation.radicals_needed(form) == 3 else "بعثر"
        table = conjugation.conjugate(radicals, form)
        assert len(table["rows"]) == 14
        for row in table["rows"]:
            assert all(row["cells"][c["id"]] for c in table["columns"]), (form, row["person"])


def test_a_baab_is_named_by_its_masdar() -> None:
    """The books head the chapter باب اِسْتِفْعَال, not باب اِسْتَفْعَلَ. Form I has no
    single مصدر, so it keeps the past-tense scale it is named by."""
    assert conjugation.scale_name("X") == "اِسْتِفْعَال"
    assert conjugation.scale_name("II") == "تَفْعِيل"
    assert conjugation.scale_name("I-nasara") == "فَعَلَ"


def test_only_the_baabs_a_root_can_take_are_offered() -> None:
    """A three-letter root offered a quadriliteral باب leads to a table that
    cannot be built, so the count filters the list before the reader sees it."""
    three, four = conjugation.forms(3), conjugation.forms(4)
    assert "X" in three and "IQ" not in three
    assert "IQ" in four and "X" not in four
    assert set(three) | set(four) == set(conjugation.forms())


# ── Which باب, and whether there is a table at all ───────────────────────────
#
# The Sarf tab refuses three kinds of word rather than print a table that would
# be wrong, and the wording of each refusal is what the reader actually sees. It
# lived inside the endpoint until now, where no test could reach it.

def test_a_bare_root_with_no_known_baab_gets_the_no_dictionary_note() -> None:
    """A bare root cannot say which Form I باب on its own; with no dictionary
    source and no reader choice, the tab says so rather than guessing one."""
    form, note = conjugation.resolve_form("كتب", "كتب", is_noun=False)
    assert form is None
    assert note and "No dictionary here records" in note


def test_a_known_baab_from_a_dictionary_source_resolves_the_form() -> None:
    """`known` is what verb_forms.verdict() names when a source states the
    bab; it beats identify()'s inability to tell the six babs apart."""
    form, note = conjugation.resolve_form("كتب", "كتب", is_noun=False, known="I-daraba")
    assert (form, note) == ("I-daraba", None)


def test_the_reader_choice_of_baab_wins() -> None:
    """Switching باب is the one place a form is not worked out but chosen."""
    form, note = conjugation.resolve_form("كتب", "كتب", is_noun=False, requested="IV")
    assert (form, note) == ("IV", None)


def test_a_word_that_is_not_three_or_four_letters_is_refused() -> None:
    form, note = conjugation.resolve_form("ال", "ال", is_noun=False)
    assert form is None
    assert note and "three- and four-letter" in note


def test_a_doubled_root_is_conjugated_now_that_its_rules_are_built() -> None:
    """مدّ used to be refused. Its إدغام rules are built, so it has a table."""
    form, note = conjugation.resolve_form("مد", "مدد", is_noun=False, requested="I-nasara")
    assert note is None and form == "I-nasara"
    assert conjugation.conjugate("مدد", form)["rows"][0]["cells"]["madi"] == "مَدَّ"


def test_a_root_whose_chapter_is_not_built_is_named_not_conjugated() -> None:
    """رأى is both hamzated and weak, which the book gives its own chapter."""
    form, note = conjugation.resolve_form("رأى", "رأي", is_noun=False)
    assert form is None
    assert note and "not built here yet" in note


def test_a_noun_is_refused_but_its_root_is_offered() -> None:
    """كِتَاب used to come back as a full table of its root. It is a noun."""
    form, note = conjugation.resolve_form("كِتَاب", "كتب", is_noun=True)
    assert form is None
    assert note and "conjugation tables are for verbs" in note
    # The root as a word, not as three spelled-out letters: it is what the
    # reader is being told to type, so it has to be typeable.
    assert "كتب" in note


def test_a_verb_the_tagger_called_a_noun_is_not_refused_as_one() -> None:
    """The tagger is a guess. A word whose own letters are the root's past
    tense is never refused as a noun, whether or not a source can then say
    which باب it is."""
    madi = conjugation.madi_of("كتب", "I-nasara")
    form, note = conjugation.resolve_form(madi, "كتب", is_noun=True)
    assert form is None
    assert note and "No dictionary here records" in note  # not "is a noun"


def test_a_verb_the_tagger_called_a_noun_is_conjugated_once_a_source_names_the_baab() -> None:
    madi = conjugation.madi_of("كتب", "I-nasara")
    form, note = conjugation.resolve_form(madi, "كتب", is_noun=True, known="I-nasara")
    assert (form, note) == ("I-nasara", None)


def test_the_root_letters_are_found_however_the_root_was_written() -> None:
    """Including the separators the old two-character strip left behind."""
    for written in ["كتب", "ك-ت-ب", "ك ت ب", "ك–ت–ب", "ك​ت​ب"]:
        assert conjugation.radicals_of(written) == "كتب", written


# ── Which category a root falls in (Treasures p.143-145) ─────────────────────

@pytest.mark.parametrize(
    "radicals,expected",
    [
        # p.145 rules 15 and 16: the book's own two examples.
        ("وقي", "لفيف مفروق"),
        ("طوي", "لفيف مقرون"),
        # One weak letter only, so the ordinary names still stand (rules 8-10).
        ("وعد", "مثال"),
        ("قول", "أجوف"),
        ("رمي", "ناقص"),
        # p.145 rules 11-13 and 17: these are named before any weak letter is
        # looked for, so a hamzah or a doubled letter wins.
        ("سأل", "مهموز"),
        ("مدد", "مضاعف"),
        ("نصر", "صحيح سالم"),
    ],
)
def test_the_root_is_named_the_way_the_book_names_it(radicals: str, expected: str) -> None:
    assert conjugation.root_type(radicals).startswith(expected)
