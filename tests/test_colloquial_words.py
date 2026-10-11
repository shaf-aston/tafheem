import urllib.error

import pytest

from backend.services.colloquial.wordcheck import forms_of, known_forms, missing, skeleton


def test_chat_and_scholarly_spellings_meet():
    assert skeleton("marḥaba") == skeleton("mar7aba") == "mr7b"
    assert skeleton("ʔakīd") == skeleton("akeed")
    assert skeleton("xamīr") == skeleton("khameer")


def test_prefix_and_ending_are_tried():
    assert skeleton("kīf") in forms_of("keefak")
    assert skeleton("bāb") in forms_of("wil-baab")


def test_a_blank_word_matches_nothing():
    assert forms_of("") == set()


def test_a_word_in_the_reference_is_not_missing():
    # The reference downloads from its publisher on first use; their server being down is not our failure.
    try:
        assert known_forms("ddda")
    except (urllib.error.URLError, TimeoutError) as down:
        pytest.skip(f"reference server unreachable: {down}")
    assert missing(["keefak", "zzzqxq"]) == ["zzzqxq"]
