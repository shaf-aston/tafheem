"""An English term is found as a whole word and not inside a longer one."""
from backend.services.daleel.match.words import pattern


def found(term, text):
    return [m.group(1) for m in pattern(term).finditer(text)]


def test_a_word_inside_a_longer_one_is_not_found():
    assert found("prayer", "the sprayer and the prayer") == ["prayer"]


def test_a_word_at_the_start_of_the_text_is_found():
    assert found("god", "god is one") == ["god"]
