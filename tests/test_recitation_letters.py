"""The letters model: reading its answer, and where it sits among the ears.

No model runs here. What is tested is turning the model's best piece per moment
into words, a missing model failing loud, and the letters ear being asked for
recitations only.

Run: python -m pytest tests/test_recitation_letters.py
"""
from __future__ import annotations

import numpy as np
import pytest

from backend.config import get_settings
from backend.services.recitation import ears, letters, listen

BLANK = 4
PIECES = ["▁قل", "▁هو", "▁ال", "له", "<blank>"]


def spell(*best):
    return letters.spelled(np.array(best), PIECES, BLANK)


def test_a_piece_held_over_several_moments_is_written_once():
    assert spell(0, 0, 0, 1, 1) == "قل هو"


def test_a_blank_between_two_of_the_same_piece_writes_it_twice():
    assert spell(0, BLANK, 0) == "قل قل"


def test_pieces_join_into_a_word_until_the_next_word_mark():
    assert spell(BLANK, 2, 3, BLANK, BLANK, 1) == "الله هو"


def test_nothing_but_blanks_is_nothing_heard():
    assert spell(BLANK, BLANK) == ""


def test_a_missing_model_fails_loud(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "recitation_letters_path", "data/no-such-model-here")
    monkeypatch.setattr(letters, "_loaded", None)
    assert not letters.installed()
    with pytest.raises(listen.NotInstalled):
        letters.read(np.zeros(1600, dtype=np.float32))


@pytest.fixture
def asked(monkeypatch):
    """Every ear answering with its own name, and a note of who was asked."""
    who: list[str] = []
    for key in ("hosted", "letters", "here"):
        ear = ears.named(key)
        monkeypatch.setattr(ear, "transcribe", lambda audio, language, hint, key=key: who.append(key) or key)
        monkeypatch.setattr(ear, "is_available", lambda: True)
        monkeypatch.setattr(ear, "retired_reason", "")
        monkeypatch.setattr(ear, "_resting_until", 0.0)
    monkeypatch.setattr(get_settings(), "recitation_ears", "letters,here")
    return who


def test_a_recitation_is_written_by_the_letters_ear(asked):
    assert ears.hear(b"sound", "ar", "") == "letters"
    assert ears.would_answer_locally()


def test_a_search_never_goes_to_the_letters_ear(asked):
    """It knows only the Qur'an: "knowledge" would come back as an ayah."""
    assert ears.hear(b"sound", None, "") == "here"
    assert asked == ["here"]


def test_without_the_model_a_recitation_falls_to_the_ear_here(asked, monkeypatch):
    monkeypatch.setattr(ears.named("letters"), "is_available", lambda: False)
    assert ears.hear(b"sound", "ar", "") == "here"
