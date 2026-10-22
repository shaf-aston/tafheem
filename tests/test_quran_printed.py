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


def test_a_tanween_meem_is_dropped_unless_a_ba_follows():
    from backend.services.arabic_text import mushaf_words
    # 4:112: إِثْمًۭا before ثُمَّ is printed plain.
    assert mushaf_words(["إِثْمًۭا", "ثُمَّ"]) == ["إِثْمًا", "ثُمَّ"]
    # 4:58: iqlab, the meem stays.
    assert mushaf_words(["سَمِيعًۢا", "بَصِيرًا"]) == ["سَمِيعًۢا", "بَصِيرًا"]
    # 2:88: a stop sign between the word and the ب does not hide it.
    assert mushaf_words(["غُلْفٌۢ ۚ", "بَل"])[0] == "غُلْفٌۢ ۚ"
    # 112:4: the last word sees what is read next, the next surah's بِسْمِ.
    assert mushaf_words(["أَحَدٌۢ"], "بِسْمِ") == ["أَحَدٌۢ"]
    assert mushaf_words(["أَحَدٌۢ"]) == ["أَحَدٌ"]


def test_the_reader_and_the_word_rows_get_the_printed_meems(monkeypatch):
    from backend.services import quran_service as qs

    texts = [(112, "أَوْ إِثْمًۭا ثُمَّ"), (113, "سَمِيعًۢا بَصِيرًا أَحَدٌۢ")]
    monkeypatch.setattr(qs.quran_corpus, "ayah_texts", lambda surah: texts)
    monkeypatch.setattr(qs.quran_meanings, "for_surah", lambda surah: {})
    monkeypatch.setattr(qs.quran_meanings, "uthmani_for_surah", lambda surah: {})
    monkeypatch.setattr(qs.quran_meanings, "surah_name", lambda surah: {})
    monkeypatch.setattr(qs.quran_layout, "for_surah", lambda surah: {})
    lines = [a["arabic"] for a in qs.get_surah(4)["ayahs"]]
    # The last ayah's last word reads on into the next surah's بِسْمِ.
    assert lines == ["أَوْ إِثْمًا ثُمَّ", "سَمِيعًۢا بَصِيرًا أَحَدٌۢ"]

    def word(arabic):
        return {"arabic": arabic, "segments": [{"arabic": arabic}]}

    rows = {112: [word("إِثْمًۭا"), word("ثُمَّ")], 113: [word("بَرِيٓـًۭٔا")]}
    monkeypatch.setattr(qs.quran_corpus, "words_for_ayah", lambda surah, ayah: rows.get(ayah, []))
    monkeypatch.setattr(qs, "_translations", lambda surah, ayah: {})
    monkeypatch.setattr(qs.quran_meanings, "uthmani_for_ayah", lambda surah, ayah: {1: "إِثْمًۭا"})
    monkeypatch.setattr(qs.quran_meanings, "ayah_end_mark", lambda surah, ayah: None)
    first = qs.get_ayah(4, 112)["words"][0]
    assert first["arabic"] == first["uthmani"] == first["segments"][0]["arabic"] == "إِثْمًا"
