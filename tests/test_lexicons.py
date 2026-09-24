"""The classical dictionaries: how a book is read, and how a root reaches it.

Two halves, tested apart because they fail apart. The reading rules are pure
string work over the shapes these files really use, so they are checked against
real lines lifted out of the books. The lookup is checked against a small
database built here, four entries, so a spelling rule can be proved without
46MB or a network.

Run: python -m pytest tests/test_lexicons.py
"""
from __future__ import annotations

import sqlite3
import zlib

import pytest

from backend.scripts import build_lexicons as builder
from backend.services import lexicons


# ── how a book is read ───────────────────────────────────────────────────────

def test_a_heading_naming_two_roots_files_the_entry_under_both():
    """Taj al-Arus heads one entry "عكث وعنكث". Both roots must reach it."""
    assert builder._heads_of("عكث وعنكث") == ["عكث", "عنكث"]


def test_a_root_written_with_its_letters_apart_stays_one_root():
    """The nearest case to the one above, and the opposite answer.

    "خ و ف" is one root spelled out letter by letter. Split on the same "و" it
    would become two roots of one letter each, neither of which exists. What
    tells them apart is that the pieces here are too short to be roots.
    """
    assert builder._heads_of("خ و ف") == ["خ و ف"]
    assert builder.normalize_root("خ و ف") == "خوف"


def test_a_chapter_heading_is_not_a_root():
    assert builder._heads_of("فصل") == []
    assert builder._heads_of("باب الهمزة والميم") == []


def test_the_books_own_punctuation_becomes_punctuation():
    """"|" ends a sense and "%" fences a half-line of verse. Neither is printed."""
    said = builder._clean("أصل صحيح | من ذلك الكتاب | قال % لا تأمنن % % على قلوصك %")
    assert "|" not in said and "%" not in said
    assert said.splitlines() == [
        "أصل صحيح", "من ذلك الكتاب", "قال", "لا تأمنن", "على قلوصك",
    ]


def test_page_numbers_and_milestones_are_not_words():
    said = builder._clean("والكتبة الخرزة PageV01P006 وإنما ms00043 سميت")
    assert said == "والكتبة الخرزة وإنما سميت"


def test_lanes_arabic_is_turned_back_into_arabic():
    assert builder._arabic("ktb") == "كتب"
    assert builder._arabic("katabahu") == "كَتَبَهُ"


def test_a_hamza_sitting_on_a_letter_is_that_letter():
    """Perseus writes A^ w^ y^ where Buckwalter writes one letter each.

    Left as they are, the caret prints in the middle of the word and every mark
    after it hangs off the wrong letter.
    """
    assert builder._arabic("$uw^obuwbN") == "شُؤْبُوبٌ"
    assert builder._arabic("$aA^afapN") == "شَأَفَةٌ"
    assert builder._arabic("$ay^iytN") == "شَئِيتٌ"


def test_a_caret_with_no_letter_under_it_is_a_hamza_on_the_line():
    """The nearest case the rule above does not name: 113 of the book's carets.

    They follow a vowel mark rather than a carrier, so there is nothing for the
    hamza to sit on and it stands by itself.
    """
    assert builder._arabic("^") == "ء"
    assert "^" not in builder._arabic("$aAa^a")


def test_arabic_inside_an_english_sentence_is_fenced_off():
    """Without this a browser lays "كتب 1, aor." out as "1 كتب , aor."."""
    fenced = builder._fenced("كتب 1, aor.")
    assert fenced == "⁨كتب⁩ 1, aor."


# ── which book is which ──────────────────────────────────────────────────────
# The shelf and the books above the reading rules. None of these touches a file:
# what they decide is who is on the shelf and in what order, which is exactly
# what a name looked up in a table somewhere else used to decide badly.

def test_every_book_on_the_shelf_says_who_it_is():
    """An unfilled book would be stored with a blank name and no credit."""
    for book in builder.SHELF.books:
        assert book.id and book.title and book.author and book.source
        assert book.language in {"ar", "en"}


def test_a_book_carries_its_own_rule_for_where_an_entry_starts():
    """Lisan's colon heading and Taj's bar heading, each on its own class."""
    assert builder.Lisan.START.match("### $ بكأ: بكأت الناقة").group(1) == "بكأ"
    assert builder.Taj.START.match("# |عكث وعنكث").group(1).strip() == "عكث وعنكث"
    # And the one that is not a line at all: Ibn Faris is cut on his marker.
    assert builder.Maqayis.MARKER.search("وهو كذلك ( أخ ) الهمزة").group(1) == "أخ"


def test_rebuilding_one_book_leaves_it_where_it_stands_on_the_shelf():
    """The nearest case nobody asks for: --only must not reorder the shelf.

    Lane is shown last. Rebuilding Lane alone hands back a list of one, and an
    order counted from that list would make Lane the first book shown.
    """
    lane = builder.SHELF.wanted("lane")
    assert [book.id for book in lane] == ["lane"]
    order = lane[0].credit(builder.SHELF.books.index(lane[0]))[-1]
    assert order == len(builder.SHELF.books) - 1


def test_a_book_nothing_answers_to_is_refused_not_quietly_skipped():
    """--only sihah must stop, not rebuild nothing and report success."""
    with pytest.raises(SystemExit):
        builder.SHELF.wanted("sihah")
    assert len(builder.SHELF.wanted(None)) == len(builder.SHELF.books)


# ── how a root reaches an entry ──────────────────────────────────────────────

@pytest.fixture
def shelf(tmp_path, monkeypatch):
    """A four-entry database, enough to prove every spelling rule."""
    path = tmp_path / "lexicons.db"
    db = sqlite3.connect(path)
    db.executescript(builder.Shelf.SCHEMA)
    db.executemany(
        "INSERT INTO book VALUES (?,?,?,?,?,?,?,?)",
        [
            ("lisan", "لسان العرب", "The Tongue", "ابن منظور", 711, "ar", "openiti-lexicons", 0),
            ("lane", "Lane", "In English", "Lane", 1876, "en", "lane", 1),
        ],
    )
    rows = [
        # (book, root, folded, head, text)
        ("lisan", "أمر", "امر", "أمر", "what Ibn Manzur says about أمر"),
        ("lane", "امر", "امر", "امر", "what Lane says about امر"),
        # One book, one root, twice: a later volume returning to it.
        ("lane", "كتب", "كتب", "كتب", "the main entry, which is much the longer of the two"),
        ("lane", "كتب", "كتب", "كتب", "a supplement"),
        # Two real roots that fold to the same letters. Neither may answer.
        ("lisan", "هنأ", "هنا", "هنأ", "about هنأ"),
        ("lisan", "هنا", "هنا", "هنا", "about هنا"),
    ]
    db.executemany(
        "INSERT INTO entry VALUES (?,?,?,?,?)",
        [(b, r, f, h, zlib.compress(t.encode())) for b, r, f, h, t in rows],
    )
    db.commit()
    db.close()

    monkeypatch.setattr(lexicons, "DATABASE", path)
    return path


def test_the_letters_typed_answer_for_themselves_first(shelf):
    """Lisan spells it أمر and Lane امر, and both are the same root.

    Typing either spelling reaches both books. What the exactness decides is not
    who answers but what is said about it: the book that spells it the way it
    was typed has nothing to explain, and the other one says where it filed it.
    """
    found = {e["book"]: e for e in lexicons.entries_for("أمر")}
    assert set(found) == {"lisan", "lane"}
    assert found["lisan"]["filed_under"] is None
    assert found["lane"]["filed_under"] == "امر"


def test_a_book_spelling_it_differently_is_still_found_and_says_so(shelf):
    """Typing امر must reach Lisan's أمر, and the reader must be told it did."""
    found = {e["book"]: e for e in lexicons.entries_for("امر")}
    assert set(found) == {"lisan", "lane"}
    assert found["lisan"]["filed_under"] == "أمر"
    # Lane files it under exactly what was typed, so there is nothing to explain.
    assert found["lane"]["filed_under"] is None


def test_two_real_roots_that_look_alike_are_refused_rather_than_guessed(shelf):
    """هنأ and هنا fold together and are different words. Neither may stand in."""
    assert lexicons.entries_for("هنا")[0]["filed_under"] is None
    assert len(lexicons.entries_for("هنا")) == 1
    # A spelling neither root uses gets nothing at all, rather than one of them.
    assert lexicons.entries_for("هنء") == []


def test_one_book_returning_to_a_root_is_one_entry_not_two(shelf):
    """Two cards with the same book's name on them read as a page repeating."""
    found = lexicons.entries_for("كتب")
    assert len(found) == 1
    # Joined with the main entry first. Which one is the main one is decided by
    # length: a book's later supplement is the short one, and a reader opening a
    # book wants what it mostly says before what it added afterwards.
    assert found[0]["text"] == (
        "the main entry, which is much the longer of the two\n\na supplement"
    )


def test_the_books_keep_their_own_order(shelf):
    assert [e["book"] for e in lexicons.entries_for("امر")] == ["lisan", "lane"]


def test_a_root_no_book_holds_is_empty_and_still_ready(shelf):
    """Empty is a fact about the root. It must not read as a broken machine."""
    assert lexicons.status() == lexicons.READY
    assert lexicons.entries_for("زقزق") == []


def test_no_database_says_so_rather_than_saying_the_root_is_unknown(tmp_path, monkeypatch):
    """The nearest case nobody asks for: the books were never built here."""
    monkeypatch.setattr(lexicons, "DATABASE", tmp_path / "not-built.db")
    assert lexicons.status() == lexicons.MISSING
    assert lexicons.entries_for("كتب") == []
