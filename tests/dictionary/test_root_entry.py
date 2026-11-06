"""The rules of retelling a Maqayees entry in English, below the route: when the model is asked at
all, what English is kept, and what is refused rather than shown wrong."""
import pytest

from backend.services import ai
from backend.services.dictionary import root_english, root_entry, root_meaning
from backend.services.dictionary.root_entry import Refused

ROOT = "كتب"
BODY = "جمع الشيء. وكتب الكتاب. وكتب الأمر."


@pytest.fixture
def book(monkeypatch):
    """A loaded book with one entry, no kept English, a model that must be asked for anything."""
    asked, kept = [], []
    monkeypatch.setattr(root_meaning, "status", lambda: root_meaning.READY)
    monkeypatch.setattr(root_meaning, "book_root_of", lambda root: root)
    monkeypatch.setattr(root_meaning, "lookup", lambda root: {"body": BODY})
    monkeypatch.setattr(root_english, "get", lambda root: None)
    monkeypatch.setattr(root_english, "get_lines", lambda root, count: None)
    monkeypatch.setattr(root_english, "put_lines", lambda root, lines: kept.append(lines))
    monkeypatch.setattr(ai, "is_ai_available", lambda: True)
    monkeypatch.setattr(ai, "explain_root_entry", lambda root, arabic: asked.append(arabic) or {"english": "To gather. To write."})
    monkeypatch.setattr(ai, "explain_root_entry_lines", lambda root, lines, prose: asked.append(lines) or {"lines": ["a", "b", "c"]})
    return asked, kept


def test_shipped_english_never_wakes_the_model(book, monkeypatch):
    asked, _ = book
    monkeypatch.setattr(root_english, "get", lambda root: "To gather. To write.")
    monkeypatch.setattr(ai, "is_ai_available", lambda: False)
    assert root_entry.english(ROOT) == ("To write.", False, "maqayees_translation") and asked == []


def test_english_made_on_the_spot_is_badged_ai_and_there_is_no_model_to_ask_otherwise(book, monkeypatch):
    assert root_entry.english(ROOT).source == "ai"
    monkeypatch.setattr(ai, "is_ai_available", lambda: False)
    assert root_entry.english(ROOT) is Refused.NO_AI


def test_an_empty_answer_or_an_empty_entry_is_refused_not_shown(book, monkeypatch):
    monkeypatch.setattr(ai, "explain_root_entry", lambda root, arabic: {"english": " "})
    assert root_entry.english(ROOT) is Refused.EMPTY
    monkeypatch.setattr(root_meaning, "lookup", lambda root: None)
    assert root_entry.english(ROOT) is Refused.NO_ENTRY


def test_lines_paired_by_the_model_are_returned_and_kept_once(book):
    asked, kept = book
    done = root_entry.lines(ROOT)
    assert done.lines == [("جمع الشيء.", "a"), ("وكتب الكتاب.", "b"), ("وكتب الأمر.", "c")] and done.source == "ai"
    assert kept == [["a", "b", "c"]]


def test_lines_that_do_not_match_the_arabic_are_refused_and_not_kept(book, monkeypatch):
    _, kept = book
    monkeypatch.setattr(ai, "explain_root_entry_lines", lambda root, lines, prose: {"lines": ["a", "b"]})
    assert root_entry.lines(ROOT) is Refused.MISPAIRED and kept == []
    monkeypatch.setattr(ai, "explain_root_entry_lines", lambda root, lines, prose: {"lines": ["a", "", "c"]})
    assert root_entry.lines(ROOT) is Refused.MISPAIRED and kept == []


def test_shipped_lines_wear_the_books_badge_and_skip_the_model(book, monkeypatch):
    asked, _ = book
    monkeypatch.setattr(root_english, "get_lines", lambda root, count: ["a", "b", "c"])
    monkeypatch.setattr(root_english, "shipped_lines", lambda root, count: True)
    assert root_entry.lines(ROOT).source == "maqayees_lines" and asked == []
