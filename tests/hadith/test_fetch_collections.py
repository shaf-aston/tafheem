"""Reading a book fawazahmed0 lacks (Mishkat) from hadith-json into the shape the index builds from."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.scripts.hadith.fetch_hadith_collections import collections, from_hadith_json  # noqa: E402

_BOOK = {
    "chapters": [{"id": 1, "arabic": "كتاب الإيمان", "english": "Faith"},
                 {"id": 0, "arabic": "", "english": "Author's Introduction"}],
    "hadiths": [
        {"idInBook": 1, "chapterId": 1, "arabic": "عَنْ عُمَرَ قَالَ", "english": {"narrator": "‘Umar said:", "text": "One day."}},
        {"idInBook": 2, "chapterId": 1, "arabic": "  ", "english": {"narrator": "", "text": "No Arabic, so dropped."}},
        {"idInBook": 3, "chapterId": 1, "arabic": "وَعَنْ أَنَسٍ", "english": {"narrator": "", "text": "Anas said."}},
        {"idInBook": 4, "chapterId": 1, "arabic": "قَالَ: \n\" ثَلَاثَةٌ  حَقٌّ", "english": {"narrator": "", "text": "Three."}},
    ],
}


def test_chapters_become_books_with_their_arabic_names_and_the_introduction_dropped():
    books, _ = from_hadith_json(_BOOK)
    assert books == [{"number": 1, "name": "Faith", "arabic": "كتاب الإيمان"}]


def test_each_hadith_keeps_its_number_and_counts_its_place_in_its_book():
    _, hadiths = from_hadith_json(_BOOK)
    assert [(h["number"], h["in_book"], h["book"]) for h in hadiths] == [(1, 1, 1), (3, 2, 1), (4, 3, 1)]
    assert hadiths[0]["english"] == "‘Umar said: One day."
    assert hadiths[1]["english"] == "Anas said." and hadiths[0]["grades"] == []


def test_every_shelved_book_names_its_shelf_and_cover():
    shelved = {key: meta for key, meta in collections().items() if meta.get("shelf")}
    assert "mishkat" in shelved
    assert all(meta.get("about") and "{number}" in meta["cite"] for meta in shelved.values())


def test_a_line_break_inside_a_hadith_is_one_space():
    _, hadiths = from_hadith_json(_BOOK)
    assert hadiths[2]["arabic"] == 'قَالَ: " ثَلَاثَةٌ حَقٌّ'
