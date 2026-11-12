"""The classical dictionaries: how a book is read, and how a root reaches it.

Two halves, tested apart because they fail apart. The reading rules are pure
string work over the shapes these files really use, so they are checked against
real lines lifted out of the books. The lookup is checked against a small
database built here, four entries, so a spelling rule can be proved without
46MB or a network.

Run: python -m pytest tests/dictionary/test_lexicons.py
"""
from __future__ import annotations

import sqlite3
import zlib

import pytest

from backend.scripts.dictionary import build_lexicons as builder
from backend.services.dictionary import lexicons


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


def test_a_lane_headword_keeps_its_first_spelling_only():
    """Perseus lists the unvowelled spellings after the headword as more <orth>
    tags; Lane printed only the first, and a heading of five spellings was lost."""
    said = builder.Lane()._said(
        '<orth extent="full" lang="ar">xaArijiy~N</orth> <orth lang="ar">xArj</orth> '
        '<orth lang="ar">xArjY</orth> One who goes out, <foreign lang="ar">xaraja</foreign>.')
    assert said == f"⁨{builder._arabic('xaArijiy~N')}⁩ One who goes out, ⁨خَرَجَ⁩."


@pytest.mark.parametrize(("heading", "roots"), [
    # Lane's own words for "and the rest": the root is the first word only.
    ("mtr, &amp;c", ["mtr"]),
    ("fAlw* &amp;c.", ["fAlw*"]),
    # One entry for two roots, joined by "and" or "or", which are not letters.
    ("$Sw and $SY", ["$Sw", "$SY"]),
    ("(dmw or dmY)", ["dmw", "dmY"]),
    # A quasi-root is filed under its letters; "Quasi" is not the letter س.
    ("Quasi tqY: or, accord. to some, tqw", ["tqY", "tqw"]),
    ("txm and quasi txm", ["txm"]),
    ("HY: or HY and Hyw", ["HY", "Hyw"]),
    # What follows "see" is where to look, not what this entry is about.
    ("gwY: see gw", ["gwY"]),
    # A single root, as nearly every heading is.
    ("ktb", ["ktb"]),
    (" tr ", ["tr"]),
    # No plain root word at all: kept whole, and its vowels go when it is filed.
    ("safaro jalN", ["safaro jalN"]),
])
def test_a_lane_heading_names_its_roots_and_no_english(heading, roots):
    """Read whole, "$Sw and $SY" was filed as شصوندشصى and nobody could reach it:
    121 of Lane's entries, تقي سعي نسي غشي among them, were lost that way."""
    assert builder._lane_heads(heading) == roots


def test_a_heading_lane_never_reached_is_not_shelved():
    """Perseus holds the place with "See Supplement", a book the app has not got."""
    lane = builder.Lane()
    stub = '<head><foreign lang="ar">yEr</foreign> &amp;c.</head><entryFree>See Supplement </entryFree>'
    assert lane._unwritten(stub)
    # A pointer with no entry block of its own is still a real line of Lane's.
    pointer = '<head><foreign lang="ar">Ely</foreign></head> For words mentioned under this head, see art. Elw.'
    assert not lane._unwritten(pointer)
    written = stub.replace("See Supplement", '<orth lang="ar">yaEara</orth> He bleated')
    assert not lane._unwritten(written)


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
    assert found["lisan"]["book_root"] is None
    assert found["lane"]["book_root"] == "امر"


def test_a_book_spelling_it_differently_is_still_found_and_says_so(shelf):
    """Typing امر must reach Lisan's أمر, and the reader must be told it did."""
    found = {e["book"]: e for e in lexicons.entries_for("امر")}
    assert set(found) == {"lisan", "lane"}
    assert found["lisan"]["book_root"] == "أمر"
    # Lane files it under exactly what was typed, so there is nothing to explain.
    assert found["lane"]["book_root"] is None


def test_two_real_roots_that_look_alike_are_refused_rather_than_guessed(shelf):
    """هنأ and هنا fold together and are different words. Neither may stand in."""
    assert lexicons.entries_for("هنا")[0]["book_root"] is None
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


def test_longest_means_the_text_not_the_stored_bytes(shelf):
    """Bodies are stored compressed, and a long repetitive entry packs smaller
    than a short varied one; ordering by stored size put the supplement first."""
    db = sqlite3.connect(shelf)
    db.execute("DELETE FROM entry WHERE root = 'كتب'")
    db.executemany("INSERT INTO entry VALUES ('lane', 'كتب', 'كتب', 'كتب', ?)", [
        (zlib.compress(("main " * 400).encode()),),
        (zlib.compress(bytes(range(32, 127)).decode().encode()),),
    ])
    db.commit()
    db.close()
    assert lexicons.entries_for("كتب")[0]["text"].startswith("main main")


def test_a_doubled_root_reaches_every_book_however_each_heads_it(shelf):
    """Lane heads مدد as مد, Lisan as مدد. A reader holding either spelling
    must reach both, and be told where the other book filed it."""
    db = sqlite3.connect(shelf)
    db.executemany("INSERT INTO entry VALUES (?,?,?,?,?)", [
        ("lisan", "مدد", "مدد", "مدد", zlib.compress("Lisan on مدد".encode())),
        ("lane", "مد", "مد", "مد", zlib.compress("Lane on مد".encode())),
    ])
    db.commit()
    db.close()
    full = {e["book"]: e["book_root"] for e in lexicons.entries_for("مدد")}
    assert full == {"lisan": None, "lane": "مد"}
    short = {e["book"]: e["book_root"] for e in lexicons.entries_for("مد")}
    assert short == {"lisan": "مدد", "lane": None}


def test_a_root_that_is_not_doubled_never_borrows_a_two_letter_entry(shelf):
    """كتب has no twin: its last two letters differ, so كت is a different root."""
    db = sqlite3.connect(shelf)
    db.execute("INSERT INTO entry VALUES ('lisan', 'كت', 'كت', 'كت', ?)", (zlib.compress(b"kt"),))
    db.commit()
    db.close()
    assert [e["book"] for e in lexicons.entries_for("كتب")] == ["lane"]


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


# ── the one-line gist ───────────────────────────────────────────────────────
def test_a_kept_gist_reaches_its_book_and_only_its_book(tmp_path, monkeypatch):
    from backend.services.dictionary import lexicon_gists
    monkeypatch.setattr(lexicon_gists, "GISTS_FILE", tmp_path / "gists.json")
    lexicon_gists.put("lisan", "خصر", "  cold; and  the waist ")
    lexicon_gists.put("lane", "خصر", "never kept: Lane is in English")
    assert lexicon_gists.get("lisan", "خصر") == "cold; and the waist"
    assert lexicon_gists.get("taj", "خصر") is None
    assert lexicon_gists.get("lane", "خصر") is None


def test_the_shelf_sends_the_gist_with_its_own_badge_and_not_the_filing_key():
    from backend.routers.dictionary import _shelf_entry
    entry = {"book": "lisan", "title": "لسان العرب", "english": "x", "author": "a", "died": 711,
             "language": "ar", "source": "openiti-lexicons", "book_root": None, "text": "t", "filed": "خصر"}
    sent = _shelf_entry(entry, "cold; and the waist").model_dump()
    assert sent["gist"] == "cold; and the waist"
    assert sent["gist_source"]["key"] == "lexicon_gist"
    assert "filed" not in sent
    assert _shelf_entry(entry, None).gist_source is None
