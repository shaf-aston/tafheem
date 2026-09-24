"""Bringing a quiet recitation up, and the three things that must not happen."""
from __future__ import annotations

import numpy as np
import pytest

from backend.services.recitation import loudness

TARGET, CEILING, FLOOR, MOST = 0.06, 0.95, 0.002, 20.0


def tone(level: float, seconds: float = 1.0, rate: int = 16000) -> np.ndarray:
    """A steady sound at a known loudness. A sine's average is its peak over root two."""
    t = np.arange(int(seconds * rate), dtype=np.float32) / rate
    return (level * np.sqrt(2) * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def levelled(sound):
    return loudness.levelled(sound, target=TARGET, ceiling=CEILING, floor=FLOOR, most=MOST)


def test_a_quiet_recitation_is_brought_up_to_the_target():
    assert loudness.loudness(levelled(tone(0.01))) == pytest.approx(TARGET, rel=0.02)


def test_a_recitation_already_loud_enough_is_left_exactly_as_it_was():
    loud = tone(0.2)
    assert levelled(loud) is loud


def test_a_silent_room_is_never_lifted_into_something_to_read():
    room = tone(0.0005)
    assert levelled(room) is room


def test_nothing_is_pushed_past_what_a_recording_can_hold():
    # Quiet on average and loud at one moment: a thump in an otherwise soft
    # recitation. Lifting it to the target would clip that moment.
    sound = tone(0.005)
    sound[100] = 0.9
    assert float(np.max(np.abs(levelled(sound)))) <= CEILING + 1e-6


def test_faint_hiss_is_not_raised_to_the_level_of_a_voice():
    hiss = tone(0.0025)
    assert loudness.loudness(levelled(hiss)) == pytest.approx(0.0025 * MOST, rel=0.02)


def test_empty_sound_says_nothing_rather_than_dividing_by_it():
    empty = np.zeros(0, dtype=np.float32)
    assert loudness.loudness(empty) == 0.0
    assert levelled(empty) is empty


def test_it_keeps_the_kind_of_numbers_the_ear_expects():
    assert levelled(tone(0.01)).dtype == np.float32
