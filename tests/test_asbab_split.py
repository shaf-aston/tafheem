"""Cutting the Lubab into reports, and placing each on its ayah.

Hand-built miniatures rather than the real book: each one is a rule in
services/asbab_split, and a rule that stops working fails here by name. The
shipped file is checked separately, by the counts build_asbab.py prints and by
data/quran/asbab-unmatched.json, which lists every report it refused to place.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
from backend.services import asbab_split

NAMES = {2: "البقرة", 8: "الأنفال", 9: "التوبة"}
ALIASES = {"براءة": 9}
BAQARAH = {
    255: "الله لا إله إلا هو الحي القيوم",
    256: "لا إكراه في الدين قد تبين الرشد من الغي",
    285: "آمن الرسول بما أنزل إليه من ربه والمؤمنون",
}
ANFAL = {9: "إذ تستغيثون ربكم فاستجاب لكم"}


def book(*pieces: str) -> str:
    return "\n".join(pieces)


def test_a_report_is_cut_at_the_word_that_ends_the_quotation():
    found = asbab_split.reports(book("### | سورة البقرة", "قوله تعالى لا إكراه في الدين الآية أخرج ابن جرير عن ابن عباس قال نزلت"))
    assert len(found) == 1
    assert found[0].quote == "لا إكراه في الدين"
    assert found[0].text.startswith("أخرج ابن جرير")


def test_the_editions_own_ayah_number_ends_the_quotation_and_is_kept():
    found = asbab_split.reports(book("### | سورة البقرة", "قوله تعالى آمن الرسول [285] روى مسلم عن ابن عباس"))
    assert found[0].numbered == 285
    assert found[0].quote == "آمن الرسول"
    assert found[0].text == "روى مسلم عن ابن عباس"


def test_a_report_that_runs_straight_into_its_chain_is_still_cut():
    found = asbab_split.reports(book("### | سورة البقرة", "قوله تعالى لا إكراه في الدين أخرج ابن جرير عن ابن عباس"))
    assert found[0].quote == "لا إكراه في الدين"
    assert found[0].text.startswith("أخرج")


def test_openiti_page_marks_and_wrapping_are_taken_out():
    found = asbab_split.reports(book(
        "### | سورة البقرة",
        "قوله تعالى لا إكراه في",
        "~~الدين الآية PageV01P019 أخرج ms015 ابن جرير عن ابن عباس",
    ))
    assert found[0].quote == "لا إكراه في الدين"
    assert "PageV01P019" not in found[0].text and "ms015" not in found[0].text


def test_the_books_own_preface_is_not_read_as_a_surah():
    rows, missed = asbab_split.passages(
        book("### | مقدمة", "قوله تعالى شيء ما الآية كلام المؤلف"), NAMES, ALIASES, lambda s: BAQARAH,
    )
    assert (rows, missed) == ([], [])


def test_a_heading_the_book_spells_its_own_way_is_read_from_the_alias_file():
    assert asbab_split.match_surah("سورة براءة", NAMES, ALIASES) == 9
    assert asbab_split.match_surah("سورة البقرة", NAMES, ALIASES) == 2
    assert asbab_split.match_surah("سورة الغاشية", NAMES, ALIASES) is None


def test_the_longer_wording_wins_over_a_shorter_one_that_opens_another_ayah():
    ayahs = {220: "ويسألونك عن اليتامى قل إصلاح لهم خير", 222: "ويسألونك عن المحيض قل هو أذى"}
    assert asbab_split.match_ayah("ويسألونك عن اليتامى", ayahs)[0] == 220
    assert asbab_split.match_ayah("ويسألونك عن المحيض", ayahs)[0] == 222


def test_words_in_two_ayahs_and_nowhere_else_are_refused():
    ayahs = {1: "يا أيها الذين آمنوا اتقوا الله", 2: "يا أيها الذين آمنوا أوفوا بالعقود"}
    ayah, why = asbab_split.match_ayah("يا أيها الذين آمنوا", ayahs)
    assert ayah is None and "no single ayah" in why


def test_a_printed_number_that_does_not_hold_the_words_is_not_trusted():
    ayah, why = asbab_split.match_ayah("إذ تستغيثون ربكم", ANFAL, numbered=99)
    assert (ayah, why) == (9, "opens")


def test_a_one_word_quotation_is_listed_rather_than_placed():
    ayah, why = asbab_split.match_ayah("وأقسموا", BAQARAH)
    assert ayah is None and "too short" in why


def test_reports_on_one_ayah_are_numbered_and_kept_in_the_books_order():
    rows, missed = asbab_split.passages(book(
        "### | سورة الأنفال",
        "قوله تعالى إذ تستغيثون ربكم الآية روى الترمذي عن عمر",
        "قوله تعالى إذ تستغيثون ربكم الآية وأخرج ابن جرير عن ابن عباس نحوه",
    ), NAMES, ALIASES, lambda s: ANFAL)
    assert missed == []
    assert len(rows) == 1 and rows[0]["surah"] == 8 and rows[0]["ayah"] == 9
    assert "[1 / 2]" in rows[0]["text"] and "[2 / 2]" in rows[0]["text"]
    assert rows[0]["text"].index("الترمذي") < rows[0]["text"].index("ابن جرير")


def test_an_exact_duplicate_report_is_kept_as_two_rather_than_folded_into_one():
    same = "قوله تعالى إذ تستغيثون ربكم الآية روى الترمذي عن عمر"
    rows, _ = asbab_split.passages(book("### | سورة الأنفال", same, same), NAMES, ALIASES, lambda s: ANFAL)
    assert rows[0]["text"].count("الترمذي") == 2


def test_a_report_about_a_run_of_ayahs_still_says_so():
    """The book closed this quotation with الآيات, so the passage must too: it is
    filed on the ayah it opens with, and printing الآية would say it is about one."""
    rows, _ = asbab_split.passages(
        book("### | سورة الأنفال", "قوله تعالى إذ تستغيثون ربكم الآيات روى الترمذي عن عمر"),
        NAMES, ALIASES, lambda s: ANFAL,
    )
    assert "الآيات" in rows[0]["text"] and rows[0]["ayah"] == 9


def test_an_opening_with_no_quotation_and_no_report_is_dropped_quietly():
    """Not a miss to list: there is nothing to place and nothing to show. The
    count build_asbab.py prints is of reports actually cut, so a dropped scrap
    never reaches a reader and never inflates the tally either."""
    rows, missed = asbab_split.passages(
        book("### | سورة البقرة", "قوله تعالى الآية"), NAMES, ALIASES, lambda s: BAQARAH,
    )
    assert (rows, missed) == ([], [])


def test_a_report_whose_words_are_in_no_ayah_is_listed_not_placed():
    rows, missed = asbab_split.passages(
        book("### | سورة البقرة", "قوله تعالى كلمات ليست في القرآن الآية أخرج ابن جرير"),
        NAMES, ALIASES, lambda s: BAQARAH,
    )
    assert rows == []
    assert missed and missed[0]["surah"] == 2 and "no single ayah" in missed[0]["why"]
