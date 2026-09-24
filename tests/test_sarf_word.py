"""The letter model must not change a single printed character.

Every rule of إعلال is about a letter's job, so the engine stops treating a
word as text and starts treating it as letters that know their job. That swap
is only safe if building a word and printing it again gives back exactly what
the old string-filling gave. These tests pin that, template by template, for
every باب in patterns.json.
"""
from __future__ import annotations

import pytest

from backend.services import conjugation
from backend.services.sarf import word as W

ROOTS = {3: "كرم", 4: "دحرج"}


def _fill(template: str, radicals: str) -> str:
    """The old way: replace {1}{2}{3} with the letters and keep the marks."""
    for index, letter in enumerate(radicals, start=1):
        template = template.replace(f"{{{index}}}", letter)
    return template


@pytest.mark.parametrize("form", list(conjugation.forms()))
@pytest.mark.parametrize(
    "slot", ["madi", "mudari", "amr", "fail", "maful", "madi-passive", "mudari-passive", "masdar"]
)
def test_building_then_printing_is_the_old_string_fill(form: str, slot: str) -> None:
    shape = conjugation._rules()["forms"][form]
    template = shape.get(slot)
    if not template:
        pytest.skip(f"{form} has no {slot}")
    radicals = ROOTS[conjugation.radicals_needed(form)]
    assert W.render(W.build([(template, W.PATTERN)], radicals)) == _fill(template, radicals)


def test_a_letter_knows_which_radical_it_is() -> None:
    built = W.build([("ي", W.PREFIX), ("ُ", W.PREFIX), ("{1}ْ{2}ِ{3}", W.PATTERN), ("ُ", W.SUFFIX)], "كرم")
    assert W.render(built) == "يُكْرِمُ"
    assert [letter.radical for letter in built] == [None, 1, 2, 3]
    assert built[0].role == W.PREFIX and built[0].vowel == W.DAMMAH
    assert W.find(built, 2) == 2
    assert built[W.find(built, 1)].silent


def test_a_shaddah_is_kept_when_the_vowel_is_replaced() -> None:
    built = W.build([("{1}َ{2}َّ{3}", W.PATTERN)], "علم")
    middle = built[W.find(built, 2)]
    assert middle.doubled
    assert middle.with_vowel(W.KASRAH).marks == W.KASRAH + W.SHADDAH


def test_a_mark_lands_on_the_letter_before_it_across_pieces() -> None:
    built = W.build([("ت", W.PREFIX), ("َ", W.PREFIX)], "كرم")
    assert len(built) == 1 and built[0].marks == W.FATHAH


def test_a_template_asking_for_a_letter_the_root_does_not_have_is_loud() -> None:
    with pytest.raises(ValueError, match="root letter 4"):
        W.build([("{1}{2}{3}{4}", W.PATTERN)], "كرم")


def test_a_mark_with_nothing_to_sit_on_is_loud() -> None:
    with pytest.raises(ValueError, match="no letter"):
        W.build([("َ", W.PATTERN)], "كرم")
