"""The reader's ayah text: the corpus's words, in the mushaf's spelling where stored.

Run: python -m pytest tests/test_quran_printed.py
"""
from __future__ import annotations

from backend.services.quran_service import as_printed


def test_a_stop_sign_on_a_word_is_shown():
    assert as_printed("لَا رَيْبَ فِيهِ", {2: "رَيْبَۛ", 3: "فِيهِۛ"}) == "لَا رَيْبَۛ فِيهِۛ"


def test_a_sign_set_apart_stays_one_word_with_it():
    shown = as_printed("لَا رَيْبَ فِيهِ", {2: "رَيْبَ ۛ"})
    assert shown.split(" ") == ["لَا", "رَيْبَ ۛ", "فِيهِ"]


def test_nothing_stored_leaves_the_corpus_text():
    assert as_printed("قُلْ هُوَ", {}) == "قُلْ هُوَ"
