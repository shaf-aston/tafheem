"""A جازم opener puts both its verbs in jazm (يجزم فعلين): typed bare, a present verb showing no
ending of its own is in jazm, never the raf' of a verb nothing governs (إن تدرس تنجح)."""
import pytest

from tests.nahw_helpers import cards, needs_parser


def cases(sentence: str) -> list[str]:
    return [c["case"] for c in cards(sentence)]


@needs_parser
@pytest.mark.parametrize("sentence", ["إن تدرس تنجح", "إن تدرسوا تنجحوا", "إِنْ تَدْرُسْ تَنْجَحْ"])
def test_both_verbs_of_in_are_in_jazm(sentence):
    assert cases(sentence)[1:] == ["jazm", "jazm"]


@needs_parser
def test_a_verb_joined_to_the_condition_verb_is_in_jazm_too():
    assert cases("إن تدرس وتجتهد تنجح")[1:] == ["jazm", "jazm", "jazm"]


@needs_parser
def test_the_verb_after_man_tied_by_its_fa_is_in_jazm():
    words = cards("ومن يشرك بالله فقد ضل")
    assert (words[1]["case"], words[1]["sign"]) == ("jazm", "سكون")


@needs_parser
def test_a_noun_shared_with_a_relative_needs_its_answer_to_show_jazm():
    assert cases("من يدرس ينجح")[1:] == ["raf'", "raf'"]


@needs_parser
def test_an_opener_that_governs_nothing_leaves_its_verb_unmoved():
    assert cases("إذا جاء زيد فأكرمه")[1] == "mabni"


@needs_parser
def test_a_past_verb_after_in_stays_built():
    assert cases("إن جاء زيد أكرمته") == ["mabni", "mabni", "raf'", "mabni"]


@needs_parser
def test_law_puts_no_verb_in_jazm():
    assert cases("لو يدرس زيد لنجح")[1] == "raf'"


@needs_parser
def test_only_a_verb_is_put_in_jazm():
    assert "jazm" not in cases("إن تدرس فلك أجر")[2:]
