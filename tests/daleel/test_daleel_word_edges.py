"""A term is found as a whole word: not inside a longer one, but with what Arabic joins on in front."""
from backend.services.daleel.match.words import pattern


def found(term, text):
    return [m.group(1) for m in pattern(term).finditer(text)]


def test_a_word_inside_a_longer_one_is_not_found():
    assert found("prayer", "the sprayer and the prayer") == ["prayer"]


def test_a_word_at_the_start_of_the_text_is_found():
    assert found("god", "god is one") == ["god"]


def test_a_short_arabic_word_is_found_with_what_is_joined_on_in_front():
    assert found("رب", "رب، وبالرب للرب ربما العرب ورب") == ["رب", "رب", "رب", "رب"]


def test_lamma_is_still_not_a_use_of_ma():
    from backend.services.daleel.match.words import uses

    assert [m.group(1) for m in uses("ما", "فلما جاء ما")] == ["ما"]
