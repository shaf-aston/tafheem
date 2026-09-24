"""Searching the Qur'an: two ways of answering, one thing the caller sees.

Everything here goes through the module's own front door, `quran_search.search`
and the two adapters' `search`. Nothing reaches inside them, because the point
of the module is that a caller does not have to know how it answered.

The things worth testing are the ones that were actually wrong before:

  A search used to need the internet, and waited 15.7 seconds to say so. So the
  test that matters most is that with the network refusing, an answer still
  comes back.

  A two-letter query finds nothing through a trigram index, silently. Arabic is
  full of them, so that is a test and not a footnote.

  Typing an ayah with all its marks on must find the ayah written with them.

Run: python -m pytest tests/test_quran_search.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.config import get_settings
from backend.services import quran_search
from backend.services.quran_search import local, remote

# Three fabricated ayahs, not the real ones: the point is the search, and a test
# that needs the built index would be skipped exactly when it is most useful.
_ROWS = [
    (1, 1, "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"),
    (2, 2, "ذَٰلِكَ ٱلْكِتَٰبُ لَا رَيْبَ فِيهِ"),
    (3, 3, "أَبٌ وَأُمٌّ"),
    # Quotes the first ayah inside a longer one: a real shape (40:65 quotes
    # 1:2), and the one that must not outrank the ayah it quotes.
    (4, 4, "قَالُوا بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ وَهُوَ رَبُّ ٱلْجَنَّةِ"),
    (5, 5, "مَالِكِ يَوْمِ ٱلدِّينِ"),
]

# The rows a search returns, as (surah, ayah).
def _keys(hits):
    return [(h.surah, h.ayah) for h in hits]


# The index has to be written inside backend/, not in pytest's tmp_path.
# config.data_path refuses a path outside the app's own directory on purpose,
# because these same settings are what the build scripts overwrite. So the
# temporary index is a temporary *name* in the real folder, removed afterwards.
_TEMP_INDEX = "data/quran/search-under-test.db"


@pytest.fixture
def index(monkeypatch):
    """A tiny index of three fabricated ayahs, pointed at through the real
    setting, so what the test exercises is the path the app itself takes."""
    from backend.scripts.build_quran_search_index import _fold

    target = Path(__file__).resolve().parents[1] / "backend" / _TEMP_INDEX
    target.unlink(missing_ok=True)
    conn = sqlite3.connect(target)
    conn.executescript(
        "CREATE VIRTUAL TABLE verse USING fts5("
        "surah UNINDEXED, ayah UNINDEXED, arabic UNINDEXED, fold, tokenize='trigram');"
    )
    conn.executemany(
        "INSERT INTO verse (surah, ayah, arabic, fold) VALUES (?, ?, ?, ?)",
        [(s, a, text, _fold(text)) for s, a, text in _ROWS],
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(get_settings(), "quran_search_index_path", _TEMP_INDEX)
    yield target
    target.unlink(missing_ok=True)


def test_a_word_is_found(index) -> None:
    hits = local.search("ريب", 10)
    assert [(h.surah, h.ayah) for h in hits] == [(2, 2)]


def test_the_quran_own_spelling_is_found_by_the_ordinary_one(index) -> None:
    """The corpus writes ٱلْكِتَٰبُ with a small alef; a reader types الكتاب. Both
    spellings are indexed, or offline search would find nothing for one of the
    commonest words in the book."""
    assert local.search("الكتاب", 10)
    assert local.search("الكتب", 10)


def test_diacritics_typed_in_still_find_the_ayah(index) -> None:
    """A beginner copies the word out with every mark on it. The index holds the
    folded text, so the query has to be folded the same way or this finds none."""
    assert local.search("ٱلرَّحِيمِ", 10)
    assert local.search("الرحيم", 10)


def test_a_two_letter_word_is_found(index) -> None:
    """The one a trigram index cannot see. It goes down the LIKE path instead,
    and finding nothing here would look exactly like an honest "not present"."""
    hits = local.search("أب", 10)
    assert [(h.surah, h.ayah) for h in hits] == [(3, 3)]


def test_a_wildcard_is_not_a_wildcard(index) -> None:
    """A bare % must be a character to search for, not "match everything"."""
    assert local.search("%", 10) == []


def test_a_recitation_across_two_ayahs_finds_both(index) -> None:
    """Dictation does not stop at the ayah mark. Both ayahs recited come first,
    and the long ayah that merely quotes one of them comes after them."""
    hits = local.search("بسم الله الرحمن الرحيم مالك يوم الدين", 10)
    assert _keys(hits) == [(1, 1), (5, 5), (4, 4)]


def test_one_misheard_word_costs_a_point_not_the_search(index) -> None:
    assert _keys(local.search("بسم الله الرحمن الكريم", 10))[0] == (1, 1)


def test_words_out_of_order_still_find_the_ayah(index) -> None:
    assert _keys(local.search("الرحيم الرحمن الله بسم", 10))[0] == (1, 1)


def test_punctuation_is_not_part_of_the_word(index) -> None:
    assert _keys(local.search("بسم الله، الرحمن الرحيم.", 10))[0] == (1, 1)


def test_ta_marbuta_typed_as_ha(index) -> None:
    assert _keys(local.search("الجنه", 10)) == [(4, 4)]


def test_a_repeated_query_word_is_counted_once(index) -> None:
    assert _keys(local.search("الله الله الله", 10)) == [(1, 1), (4, 4)]


def test_arabic_asks_the_index_first_and_english_asks_quran_com_first(index, monkeypatch) -> None:
    """Quran.com answered a recited Fatiha with 39:74. For Arabic the ranked
    index answers; for English, which the index cannot read, Quran.com does."""
    asked = []

    def remote_answers(query, limit):
        asked.append(query)
        return [quran_search.Hit(surah=9, ayah=9, arabic_text="x", source=remote._SOURCE)]

    monkeypatch.setattr(remote, "search", remote_answers)
    monkeypatch.setattr(get_settings(), "quran_search_source", "auto")
    assert _keys(quran_search.search("ريب", 10)) == [(2, 2)] and asked == []
    assert _keys(quran_search.search("doubt", 10)) == [(9, 9)] and asked == ["doubt"]


def test_a_local_hit_is_badged_as_the_corpus(index) -> None:
    assert {h.source for h in local.search("ريب", 10)} == {"corpus"}


def test_a_missing_index_is_empty_not_an_error(monkeypatch) -> None:
    """Not built yet is a thing to say, never a crash."""
    monkeypatch.setattr(get_settings(), "quran_search_index_path", "data/quran/never-built.db")
    assert local.search("ريب", 10) == []


def test_the_local_index_answers_when_the_network_does_not(index, monkeypatch) -> None:
    """The whole reason the local index exists."""
    def refuse(*args, **kwargs):
        raise OSError("no network")

    monkeypatch.setattr(remote, "search", refuse)
    monkeypatch.setattr(get_settings(), "quran_search_source", "auto")

    hits = quran_search.search("ريب", 10)
    assert [(h.surah, h.ayah, h.source) for h in hits] == [(2, 2, "corpus")]


def test_nothing_answers_and_that_is_still_not_an_error(monkeypatch) -> None:
    """No network and no index: empty, and the app carries on."""
    def refuse(*args, **kwargs):
        raise OSError("no network")

    monkeypatch.setattr(remote, "search", refuse)
    monkeypatch.setattr(get_settings(), "quran_search_index_path", "data/quran/never-built.db")
    monkeypatch.setattr(get_settings(), "quran_search_source", "auto")

    assert quran_search.search("ريب", 10) == []


def test_pinning_to_local_never_touches_the_network(index, monkeypatch) -> None:
    """"local" has to mean local. A reader who sets it is asking the app to stop
    reaching for the internet, so a fallback the other way would break a promise."""
    def explode(*args, **kwargs):
        raise AssertionError("the network was used with quran_search_source=local")

    monkeypatch.setattr(remote, "search", explode)
    monkeypatch.setattr(get_settings(), "quran_search_source", "local")
    assert quran_search.search("ريب", 10)


def test_the_online_source_is_a_known_badge() -> None:
    """Both adapters name a source that data/sources.json really has, or the
    badge would fail at the moment a reader searched rather than here."""
    from backend.services import provenance

    assert provenance.of(local._SOURCE)["label"]
    assert provenance.of(remote._SOURCE)["label"]
