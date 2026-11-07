"""What a listening request may ask for, called directly (the HTTP side of each rule is
in test_recitation_check.py).

Run: python -m pytest tests/recitation/test_recitation_rules.py
"""
from __future__ import annotations

import pytest

from backend.config import get_settings
from backend.services.recitation import Refused, rules


@pytest.fixture(autouse=True)
def small_caps(monkeypatch):
    monkeypatch.setattr(get_settings(), "recitation_check_ayahs_max", 3)
    monkeypatch.setattr(get_settings(), "recitation_check_heard_max_chars", 10)


def test_a_check_list_is_read_in_order_and_empty_pieces_are_skipped():
    assert rules.checked_ayahs("112:1,112:2,") == ["112:1", "112:2"]
    assert rules.checked_ayahs("") == []


@pytest.mark.parametrize("check", ["1:1,1:2,1:3,1:4", "1:1,1:1", "1:1,x", "1:1;1:2", "1234:1", "1:"])
def test_a_check_list_too_long_repeating_or_misshapen_is_refused_in_the_readers_words(check):
    with pytest.raises(Refused, match="check must be up to 3 different ayahs, as 1:1,1:2."):
        rules.checked_ayahs(check)


def test_one_reading_s_words_have_one_cap_named_for_whichever_asked():
    rules.words_within_cap("heard", "x" * 10)
    with pytest.raises(Refused, match="before must be at most 10 characters."):
        rules.words_within_cap("before", "x" * 11)
    with pytest.raises(Refused, match="heard must be at most 10 characters."):
        rules.words_within_cap("heard", "x" * 11)


def test_the_open_page_is_its_first_and_last_ayah():
    assert rules.page_ends("2:1-2:5") == ((2, 1), (2, 5))
    assert rules.page_ends("2:286-3:20") == ((2, 286), (3, 20))
