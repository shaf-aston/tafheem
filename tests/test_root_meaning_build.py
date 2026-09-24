"""Where one entry of the classical book starts and stops.

This is the only thing the builder decides, the words themselves are typed out
by people and taken verbatim. Every case here is a shape the printed book really
takes, and each one was a defect on screen before it was a test.
"""

import json

import pytest

from backend.scripts.build_root_meanings import (
    Config,
    DATA,
    attach_english,
    carries_a_sense,
    clean_body,
    index_key,
    named_by_the_prose,
    origin_sentence,
    slice_entries,
)


@pytest.fixture(scope="module")
def cfg():
    """The shipped config, so a knob edited in build.json is felt here first."""
    return Config(DATA / "build.json")


# ── What counts as a sense ──────────────────────────────────────────────────

def test_naming_the_roots_letters_is_not_a_sense(cfg):
    """"The B and the H and the R" tells the reader the letters they typed."""
    assert not carries_a_sense(cfg, "الْبَاءُ وَالْحَاءُ وَالرَّاءُ")


def test_a_weak_letter_named_the_long_way_is_still_not_a_sense(cfg):
    assert not carries_a_sense(cfg, "الْهَاءُ وَالنُّونُ وَالْحَرْفُ الْمُعْتَلُّ")


def test_the_letters_plus_what_they_mean_is_a_sense(cfg):
    assert carries_a_sense(cfg, "الْكَافُ وَالتَّاءُ وَالْبَاءُ أَصْلٌ يَدُلُّ عَلَى الْجَمْعِ")


# ── Reading the opening statement ───────────────────────────────────────────

def test_the_sense_continues_past_a_full_stop_after_the_letters(cfg):
    """The editor sometimes closes the enumeration with a full stop. Stopping
    there left 221 entries with a headline that said nothing."""
    body = clean_body(cfg, "الْبَاءُ وَالْحَاءُ وَالرَّاءُ. قَالَ الْخَلِيلُ هُوَ الْمَاءُ الْوَاسِعُ. وَغَيْرُ ذَلِكَ")
    core = origin_sentence(cfg, body)
    assert "الْخَلِيلُ" in core
    assert "وَغَيْرُ ذَلِكَ" not in core  # only as far as it takes to say something


def test_a_chapter_name_is_not_the_meaning_of_a_root(cfg):
    """جح opened "in the doubled-letter chapter", the book's own furniture,
    printed under Ibn Faris's name as though it were his definition."""
    body = clean_body(cfg, "فِي الْمُضَاعَفِ. الْجِيمُ وَالْحَاءُ يَدُلُّ عَلَى عِظَمِ الشَّيْءِ")
    assert not body.startswith("فِي")
    assert origin_sentence(cfg, body).startswith("الْجِيمُ")


def test_the_body_and_the_sense_agree_about_where_the_entry_starts(cfg):
    """The card strips the sense off the body by matching its opening. Ten
    entries carried a stray bracket in one and not the other, so the match
    failed and the first sentence was printed twice."""
    body = clean_body(cfg, "الْبَاءُ وَالْقَافُ وَالرَّاءُ] أَصْلَانِ. وَمِنْهُ الْبَقَرُ")
    assert body.startswith(origin_sentence(cfg, body))


def test_a_gap_in_the_manuscript_is_not_a_meaning(cfg):
    """The editor marks an unreadable stretch with dots spaced apart."""
    assert origin_sentence(cfg, "الْكَافُ وَالسِّينُ وَالْحَرْفُ الْمُعْتَلُّ . . . . .") == ""


def test_the_two_halves_of_a_line_of_verse_are_not_a_gap(cfg):
    """He separates the halves of a line with three dots and no spaces.

    Read as a gap, that threw away 3,467 lines of poetry and with them every
    entry whose sense is stated before one, العلهب, اليعفور, أقر and the rest.
    """
    verse = "التَّيْسُ الطَّوِيلُ الْقَرْنَيْنِ. قَالَ: إِذَا قَعِسَتْ ... تَكَشَّفَ عَنْ عَلَاهِبَةٍ"
    assert origin_sentence(cfg, verse).startswith("التَّيْسُ")


# ── Where the entry stops ───────────────────────────────────────────────────

def test_the_entry_stops_where_the_next_chapter_begins(cfg):
    """The last root of a chapter is followed by the chapter's closing matter and
    the next chapter's opening. 654 entries carried that, eleven almost entirely."""
    body = clean_body(cfg, "الْجِيمُ وَالثَّاءُ وَالْمِيمُ أَصْلٌ يَدُلُّ عَلَى التَّجَمُّعِ [بَابُ الْجِيمِ وَالْحَاءِ] وَمَا بَعْدَهُ")
    assert "بَابُ" not in body
    assert body.endswith("التَّجَمُّعِ")


# ── The machine-read English ────────────────────────────────────────────────

def test_a_gloss_reaches_the_entry_however_either_side_spells_the_root(cfg, tmp_path, monkeypatch):
    """The book files أخ and the gloss is filed under اخ. Matching the letters as
    typed lost 407 real glosses to that difference alone."""
    monkeypatch.setattr(
        "backend.scripts.build_root_meanings.sidecar",
        lambda name: {"اخ": {"core_meaning_english": "brotherhood"}},
    )
    book = {"أخ": {"core_meaning": "الأخوة"}}
    assert attach_english(cfg, book) == 1
    assert book["أخ"]["english"] == "brotherhood"


def test_a_gloss_two_roots_could_belong_to_is_given_to_neither(cfg, monkeypatch):
    """هنأ and هنا fold together and are different roots. A gloss keyed on the
    folded spelling names no one root, and guessing would badge a machine
    reading of one root as the meaning of another.

    Matching the key exactly is not a way out. That file is written with no
    hamza signs anywhere, and the hamza is the entire difference between the
    two, so an exact hit on هنا only means the key could not have spelled
    هنأ. It was landing "the opposite of coldness" on دفا, a long bend, when it
    was written for دفأ, warmth.
    """
    monkeypatch.setattr(
        "backend.scripts.build_root_meanings.sidecar",
        lambda name: {"هنا": {"core_meaning_english": "here"}},
    )
    book = {"هنأ": {"core_meaning": "إصابة الخير"}, "هنا": {"core_meaning": "المعتل"}}
    assert attach_english(cfg, book) == 0
    assert book["هنأ"].get("english", "") == ""
    assert book["هنا"].get("english", "") == ""


def test_a_gloss_still_reaches_a_root_nothing_else_could_claim(cfg, monkeypatch):
    """The rule above must not cost the 4,561 glosses that are unambiguous."""
    monkeypatch.setattr(
        "backend.scripts.build_root_meanings.sidecar",
        lambda name: {"هنا": {"core_meaning_english": "here"}},
    )
    book = {"هنا": {"core_meaning": "المعتل"}}
    assert attach_english(cfg, book) == 1
    assert book["هنا"]["english"] == "here"


def test_an_empty_gloss_is_not_attached(cfg, monkeypatch):
    monkeypatch.setattr(
        "backend.scripts.build_root_meanings.sidecar",
        lambda name: {"كتب": {"core_meaning_english": "   "}},
    )
    book = {"كتب": {"core_meaning": "الجمع"}}
    assert attach_english(cfg, book) == 0
    assert "english" not in book["كتب"]


# ── The shipped file itself ─────────────────────────────────────────────────
# Standing checks on the real data, not on the rules that produced it; so a
# hand-edit or a half-finished rebuild is caught too. The book is built once and
# never committed, so on a machine that has not built it there is nothing to check.

built = pytest.mark.skipif(
    not (DATA / "roots.json").is_file(),
    reason="the book has not been built on this machine, see build_root_meanings.py",
)


@built
def test_the_book_on_disk_holds_no_entry_that_says_nothing(cfg):
    """A standing check on the real data: every printed meaning is a meaning.

    The one exception is a root whose printed text the edition itself leaves
    incomplete, which the card should show as the book shows it.
    """
    book = json.loads((DATA / "roots.json").read_text(encoding="utf-8"))
    silent = [root for root, entry in book.items() if not carries_a_sense(cfg, entry["core_meaning"])]
    assert silent == ["عشط"], silent


@built
def test_no_entry_on_disk_carries_another_chapter(cfg):
    book = json.loads((DATA / "roots.json").read_text(encoding="utf-8"))
    assert not [
        r
        for r, e in book.items()
        if cfg.section_heading.search(e.get("body", ""))
    ]


@built
def test_every_entry_on_disk_opens_the_way_its_sense_does(cfg):
    book = json.loads((DATA / "roots.json").read_text(encoding="utf-8"))
    assert not [
        r
        for r, e in book.items()
        if e.get("body") and not e["body"].startswith(e["core_meaning"])
    ]


def test_a_label_closed_by_more_than_one_full_stop_leaves_no_punctuation_behind(cfg):
    """The sentence list drops empty pieces and the string slice does not, so the
    two could disagree about where the entry opens, and the card strips the
    sense off the body by matching that opening exactly."""
    body = clean_body(cfg, "فِي الْمُضَاعَفِ.. الْجِيمُ وَالْحَاءُ يَدُلُّ عَلَى عِظَمِ الشَّيْءِ")
    assert body.startswith("الْجِيمُ")
    assert body.startswith(origin_sentence(cfg, body))


# ── What the contents page calls an entry ───────────────────────────────────

@pytest.mark.parametrize("printed, root", [
    ("(كَتَبَ)", "كتب"),                      # an ordinary entry, already right
    ("(زَكِنَ) :", "زكن"),                    # the editor's colon is not a letter
    ("(الْبَلْعُومُ)", "بلعوم"),               # a word of more than three letters wears "the"
    ("(وَالْحَنَاتِمُ) :", "حناتم"),           # …and sometimes the "and" he opened with
    ("(فَأَمَّا النَّبَهْرَجُ)", "نبهرج"),      # …and sometimes "as for"
    ("(وَطَرٌ) :", "وطر"),                    # the و of وطر is a letter, and stays
    (r"(رَبَى \ أ)", "ربى"),                 # one entry filed under two spellings
    ("(تَمَّ كِتَابُ الْغَيْنِ)", ""),          # the editor's closing line names no root
])
def test_the_contents_page_line_is_read_as_the_root_it_names(cfg, printed, root):
    key = index_key(cfg, printed)
    assert key == root or (root == "" and " " in key)


def test_a_heading_the_contents_page_left_out_is_found_in_the_prose(cfg):
    """Ibn Faris opens an entry by naming its own letters, so nothing else can
    look like one. Five entries are printed and unlisted, and without this each
    was swallowed by the entry above it, أم carried 615 characters of أه."""
    text = "وَقَدْ مَرَّ. (حدأ) الْحَاءُ وَالدَّالُ وَالْهَمْزَةُ أَصْلٌ وَاحِدٌ: طَائِرٌ"
    assert [root for root, _, _ in named_by_the_prose(cfg, text, [])] == ["حدأ"]


def test_a_bracketed_word_in_the_middle_of_a_sentence_is_not_a_heading(cfg):
    """Brackets run all through the prose; only the letter-naming makes a heading."""
    text = "وَمِنْ ذَلِكَ (بلسم) الرَّجُلُ: كَرِهَ وَجْهَهُ، فَالْمِيمُ فِيهِ زَائِدَةٌ"
    assert named_by_the_prose(cfg, text, []) == []


def test_a_word_the_book_prints_twice_does_not_get_swallowed(cfg):
    """The contents page has one row for ع-س-ل-ق and the book has two words
    under it: العَسْلَق, a bold predator, and العَسَلَّق, the ostrich. The row was
    spent on the first, so the entry printed between them ran straight over the
    ostrich and showed it as part of its own meaning."""
    text = ("(الْعُسْقُولُ) : قِطْعَةُ السَّرَابِ. وَالْأَصْلُ الْعَسَقُ.\n"
            "(الْعَسَلَّقُ) : الظَّلِيمُ. مُمْكِنٌ أَنْ يَكُونَ مِنَ السُّرْعَةِ")
    # عسلق was placed earlier in the book, on the other word of that spelling;
    # عسقول is the heading this excerpt opens with.
    already = [("عسلق", 0, 0), ("عسقول", 0, 12)]
    assert [root for root, _, _ in named_by_the_prose(cfg, text, already)] == ["عسلق"]


def test_a_defined_word_in_mid_sentence_is_not_a_heading(cfg):
    """Ibn Fāris defines a word inside a sentence the same way he heads an entry.
    Taking every one of those invented 35 roots and cut 29 entries short."""
    text = "وَمِنْ ذَلِكَ يَوْمٌ (عَمَرَّسٌ) : شَدِيدٌ ذُو شَرٍّ، قَالَ الْأُرَيْقِطُ"
    assert named_by_the_prose(cfg, text, [("عمرس", 0, 5)]) == []


def test_a_spelling_the_book_heads_twice_keeps_both_entries(cfg):
    """Twice in the book one spelling heads two different words, العَسْلَق a
    bold predator and العَسَلَّق an ostrich, and كتو twice over. One key holds one
    record, so keeping only the first quietly dropped 239 and 235 characters of
    Ibn Fāris with nothing on screen to show they were missing."""
    text = ("(الْعَسْلَقُ) : كُلُّ سَبُعٍ جَرُؤَ عَلَى الصَّيْدِ.\n"
            "(الْعَسَلَّقُ) : الظَّلِيمُ، وَهُوَ مِنَ السُّرْعَةِ.")
    first, second = text.split("\n")
    both = [
        ("عسلق", 0, first.index(")") + 1),
        ("عسلق", len(first) + 1, len(first) + 1 + second.index(")") + 1),
    ]
    book, blank, twice = slice_entries(cfg, text, both)
    assert twice == ["عسلق"]
    assert "سَبُعٍ" in book["عسلق"]["body"] and "الظَّلِيمُ" in book["عسلق"]["body"]
    assert book["عسلق"]["body"].startswith(book["عسلق"]["core_meaning"])


@built
def test_the_book_on_disk_keeps_every_entry_it_cut(cfg):
    """Nothing the builder cuts may vanish. A fix that shortens one entry and
    lengthens nothing is dropping Ibn Fāris's words with no sign on screen.

    The two spellings the book heads twice are the case that broke it: cutting
    the ostrich out of عسقول was right, and losing it was not.
    """
    book = json.loads((DATA / "roots.json").read_text(encoding="utf-8"))
    kept = " ".join(cfg.diacritics.sub("", entry.get("body", "")) for entry in book.values())
    for passage in ("الظليم. ممكن", "اكتوتى الرجل"):
        assert kept.count(passage) == 1, passage
