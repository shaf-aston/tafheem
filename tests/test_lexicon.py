"""What makes a Qur'anic word fair to quiz on.

The bank is 3,600 words nobody grouped by hand, so these two rules are the only
thing standing between the reader and a question that answers itself: a wrong
option must be the same type of word as the answer, and a gloss must read as a
meaning rather than as a piece of the ayah it was lifted from.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from backend.scripts.build_lexicon import (
    ARABIC_LETTER,
    Lexicon,
    Word,
    anki_gloss,
    anki_lemma,
    clean_gloss,
    content_digest,
    gloss_flaws,
    only_new_words,
    type_of,
)
from backend.scripts.export_quiz_words import already_taught


@pytest.mark.parametrize(
    ("pos", "features", "expected"),
    [
        ("V", "PERF|3MS", "verb"),
        ("N", "M|GEN", "noun"),
        ("N", "MS|GEN|ADJ", "adjective"),
        ("N", "PN|GEN", "noun"),  # named separately; PN is dropped, not a type
    ],
)
def test_the_corpus_says_which_type_of_word_it_is(pos: str, features: str, expected: str) -> None:
    assert type_of(pos, features) == expected


@pytest.mark.parametrize(
    "gloss",
    [
        "and not he delayed",   # carries the wa in front of it
        "on the bank",          # carries the 'ala in front of it
        "of it would hasten",   # a clause, not a meaning
        "",                     # the cleaning took the whole gloss away
    ],
)
def test_a_gloss_that_is_a_piece_of_the_ayah_is_flawed(gloss: str) -> None:
    assert gloss_flaws(gloss, "verb") > 0


@pytest.mark.parametrize("gloss", ["pen", "the cows", "he guides", "to bring forth"])
def test_a_gloss_that_reads_as_a_meaning_is_clean(gloss: str) -> None:
    assert gloss_flaws(gloss, "verb") == 0


def test_a_thing_with_a_person_inside_it_is_flawed_but_a_verb_is_not() -> None:
    """"their fingers" is fingers with a pronoun stuck on; "He guides" is just
    how English writes a conjugated verb."""
    assert gloss_flaws("their fingers", "noun") > 0
    assert gloss_flaws("He guides", "verb") == 0


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("(is) Allah", "Allah"), ("[the] cows", "cows"), ("darkness[es]", "darkness"), ("[a fear]", "")],
)
def test_bracketed_helper_text_never_reaches_the_screen(raw: str, expected: str) -> None:
    assert clean_gloss(raw) == expected


# ── what counts as one word ───────────────────────────────────────────────────


def a_word(ar: str, en: str, **rest: object) -> Word:
    return Word(ar=ar, en=en, meaningKey=en.lower(), source="test", **rest)


def gather(*words: Word) -> Lexicon:
    lexicon = Lexicon()
    for word in words:
        lexicon.add(word)
    return lexicon


def test_the_same_spelling_twice_is_one_word_holding_both_lists() -> None:
    lexicon = gather(
        a_word("كِتاب", "book", sets={"everyday"}),
        a_word("كِتاب", "book", sets={"quran"}, places={(2, 1)}),
    )
    assert len(lexicon.words) == 1
    assert lexicon.words[0].sets == {"everyday", "quran"}
    assert lexicon.words[0].places == {(2, 1)}


def test_two_spellings_of_one_meaning_are_one_word() -> None:
    """سَلام from the book and سَلَام from the corpus are the same word written twice."""
    lexicon = gather(
        a_word("سَلَام", "peace", sets={"book"}),
        a_word("سَلام", "peace", sets={"quran"}),
    )
    assert len(lexicon.words) == 1
    assert lexicon.merged == 1


def test_two_words_that_share_their_letters_stay_two_words() -> None:
    """عالَم (worlds) and عالِم (All-Knower) are only the same with the vowels off."""
    lexicon = gather(
        a_word("عالَم", "the worlds"),
        a_word("عالِم", "All-Knower"),
    )
    assert len(lexicon.words) == 2


def test_the_hand_written_english_wins_and_the_corpus_only_adds_to_it() -> None:
    lexicon = gather(
        a_word("أَوَّل", "first", sets={"book"}),
        a_word("أَوَّل", "First", wordType="noun", timesInQuran=82, sets={"quran"}),
    )
    kept = lexicon.words[0]
    assert (kept.en, kept.wordType, kept.timesInQuran) == ("first", "noun", 82)


def test_a_word_that_stands_alone_anywhere_is_not_joined() -> None:
    lexicon = gather(
        a_word("رَحْمَة", "mercy", attached=True),
        a_word("رَحْمَة", "mercy", attached=False),
    )
    assert lexicon.words[0].attached is False


# ── the export the browser actually reads ────────────────────────────────────
# The quiz never opens lexicon.db; it fetches files exported from it. So the one
# failure this cannot see for itself is a table rebuilt and never re-exported,
# which leaves the quiz on the previous build's words with nothing on screen to
# say so. The digest is carried from one to the other so that this test can.

LEXICON = Path(__file__).parent.parent / "backend" / "data" / "lexicon.db"
EXPORT = Path(__file__).parent.parent / "frontend" / "public" / "words" / "index.json"


@pytest.mark.skipif(
    not (LEXICON.exists() and EXPORT.exists()),
    reason="both are generated: run build_lexicon.py then export_quiz_words.py",
)
def test_the_shipped_files_came_from_the_table_as_it_stands_now() -> None:
    db = sqlite3.connect(LEXICON)
    stored = db.execute("SELECT value FROM meta WHERE key = 'content'").fetchone()[0]
    assert content_digest(db) == stored, "lexicon.db does not match its own recorded digest"
    shipped = json.loads(EXPORT.read_text("utf-8"))["builtFrom"]
    assert shipped == stored, (
        "frontend/public/words/ is from an older build of lexicon.db, "
        "run: python backend/scripts/export_quiz_words.py"
    )


# ── which words a surah or a juz leaves out ──────────────────────────────────


def test_the_book_covers_a_second_spelling_of_a_word_it_names() -> None:
    # Same letters, same type: one word written twice, so a surah should not
    # hand back the corpus's copy of a word the book already teaches.
    identity = {1: ("رحمن", "noun"), 2: ("رحمن", "noun")}
    assert already_taught(identity, {1}) == {1, 2}


def test_two_words_that_share_their_letters_are_not_both_taught() -> None:
    # هُدًى (guidance, a noun) and هَدَى (he guided, a verb). Matching on the
    # letters alone deleted the verb from every surah cut, the bug this guards.
    identity = {1: ("هدي", "noun"), 2: ("هدي", "verb")}
    assert already_taught(identity, {1}) == {1}


def test_a_word_the_book_never_names_stays() -> None:
    identity = {1: ("رحمن", "noun"), 2: ("بعوضة", "noun")}
    assert already_taught(identity, {1}) == {1}


# ── the Anki deck ────────────────────────────────────────────────────────────
# Its cards carry notes their author left himself, which are useful on a
# flashcard and wrong in a quiz option: they describe a different word, and they
# put Arabic inside the English.


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("noble, honoured (not كريم or نبيل)", "noble, honoured"),
        ("to bless/to be kind (with على)", "to bless, to be kind"),  # one "or", not three
        ("road, way, lane (not طريق,", "road, way, lane"),          # never closed
        ("guidance (not هُدًى)", "guidance"),
        ("<b>offspring</b>;&nbsp;descendant(s)", "offspring, descendant"),
        ("to follow (تبع) , to pursue", "to follow, to pursue"),    # gap the bracket left
        ("to bite/", "to bite"),                                    # nothing after the "or"
    ],
)
def test_a_card_note_never_reaches_the_quiz(raw: str, expected: str) -> None:
    assert anki_gloss(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("اِعْتَدَى (على)", "اِعْتَدَى"),      # the preposition it governs: a note
        ("أَحَقُّ (بِـ)", "أَحَقُّ"),          # same particle, vocalised differently
        ("كَادَ (يكاد)", "كَادَ (يكاد)"),   # not a particle; it names the other كَادَ
        ("سِنٌّ (ليس في فم)", "سِنٌّ (ليس في فم)"),
        ("(أَغْنَى (عَنْ", "أَغْنَى"),        # brackets typed on the wrong sides
    ],
)
def test_the_preposition_a_verb_governs_is_not_part_of_its_spelling(raw: str, expected: str) -> None:
    assert anki_lemma(raw) == expected


def test_a_note_beside_a_word_never_counts_as_letters() -> None:
    """اِعْتَدَى (على) spells اعتدى. Counted with the note it matched nothing, and
    24 words the Qur'anic sets already teach came in behind that."""
    assert a_word("اِعْتَدَى (على)", "to transgress").bare == a_word("اِعْتَدَى", "x").bare


def test_a_meaning_is_kept_whole_however_long_it_is() -> None:
    """Length is not the problem, an option that reads unlike the other three
    is. A full meaning is safe beside three that also open "to"."""
    long = "to carry out, to execute, to implement, to realize, to effect"
    assert anki_gloss(long) == long


def test_a_word_the_deck_never_glossed_in_english_is_left_out() -> None:
    # Arabic still there once the brackets are gone: an example, not a meaning.
    assert ARABIC_LETTER.search(anki_gloss("to be pleased رَضِيَ ٱللَّٰهُ عَنْهُ"))


def test_only_words_the_table_does_not_already_have_are_taken() -> None:
    """A Bayna Yadayk word already in the Qur'anic sets is dropped, not merged:
    it is already being asked there, so letting it in asks it twice."""
    lexicon = gather(a_word("كِتاب", "book", wordType="noun", sets={"quran"}))
    arriving = [
        a_word("كِتَاب", "a book", wordType="noun", sets={"everyday"}),   # same word
        a_word("مِفْتَاح", "a key", wordType="noun", sets={"everyday"}),  # new
    ]
    kept, dropped = only_new_words(lexicon, arriving)
    assert [w.en for w in kept] == ["a key"]
    assert dropped == {"already in quran": 1}


def test_the_same_letters_as_a_verb_is_still_a_new_word() -> None:
    """مَال (wealth) and مَالَ (to lean) share their letters and are two words."""
    lexicon = gather(a_word("هُدًى", "guidance", wordType="noun", sets={"quran"}))
    kept, _ = only_new_words(lexicon, [a_word("هَدَى", "to guide", wordType="verb")])
    assert [w.en for w in kept] == ["to guide"]


def test_the_same_letters_as_a_qur_anic_adjective_is_not_a_new_noun() -> None:
    """Arabic does not draw the noun/adjective line sharply, and this build
    re-labels whole groups of the book from one to the other, so رَبّ the
    adjective and رَبٌّ the noun are one word to someone deciding what to study.
    Thirteen pairs reached the everyday set through that gap once."""
    lexicon = gather(a_word("رَبّ", "Lord, Sustainer", wordType="adjective", sets={"book"}))
    kept, dropped = only_new_words(lexicon, [a_word("رَبٌّ", "master, lord", wordType="noun")])
    assert kept == []
    assert dropped == {"already in book": 1}
