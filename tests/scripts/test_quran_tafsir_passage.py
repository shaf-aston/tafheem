"""Reading one tafsir answer, without the network.

A commentary is often written about several ayahs at once, and getting that
wrong files a passage under the wrong ayah, so it is checked here rather than
only during a four-hour harvest.
"""
from __future__ import annotations

from backend.scripts.build_quran_tafsir import read_passage


def test_a_passage_about_one_ayah_covers_only_that_ayah():
    text, covered = read_passage(2, 5, {"tafsir": {"text": "<p>Said of them.</p>"}})
    assert text == "Said of them."
    assert covered == [5]


def test_a_passage_written_about_a_run_covers_all_of_it():
    text, covered = read_passage(2, 1, {
        "tafsir": {"text": "About the opening.", "verses": {"2:1": {}, "2:2": {}, "2:3": {}}},
    })
    assert covered == [1, 2, 3]
    assert text == "About the opening."


def test_a_key_naming_another_surah_is_dropped():
    """Trusting one would file this surah's passage under a different one."""
    _, covered = read_passage(2, 1, {"tafsir": {"text": "x", "verses": {"2:1": {}, "3:7": {}}}})
    assert covered == [1]


def test_a_key_that_is_not_two_numbers_is_dropped():
    _, covered = read_passage(2, 1, {"tafsir": {"text": "x", "verses": {"2:1": {}, "intro": {}}}})
    assert covered == [1]


def test_an_ayah_with_no_commentary_comes_back_empty():
    """Stored as nothing at all, never as an empty passage."""
    assert read_passage(2, 5, {"tafsir": {"text": ""}}) == ("", [5])
    assert read_passage(2, 5, {}) == ("", [5])


def test_the_ayah_asked_for_answers_when_the_reply_names_none():
    _, covered = read_passage(114, 3, {"tafsir": {"text": "x", "verses": {}}})
    assert covered == [3]
