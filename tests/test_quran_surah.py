"""Reading a whole surah, the fast path must agree with the slow one.

The reading view gets its text from a single SQL query that stitches segments
into words and words into ayahs. That is a second way of doing what
words_for_surah already does properly, so the thing worth testing is that the two
never disagree, a shortcut that is subtly wrong is worse than no shortcut.

Also covered: the vowel-mark mismatch that used to make a fifth of the Qur'an
return a 500, because a surah reader walks straight through all of it.

Run: python -m pytest tests/test_quran_surah.py
"""
from __future__ import annotations

import pytest

from backend.services import quran_corpus, quran_meanings, quran_service

pytestmark = pytest.mark.skipif(
    not quran_corpus.is_loaded(),
    reason="corpus.db not built, run backend/scripts/build_quran_corpus.py",
)

# Al-Fatiha, the longest surah, one with a FAM tag, and the shortest.
SAMPLE = (1, 2, 3, 112, 114)


@pytest.mark.parametrize("surah", SAMPLE)
def test_fast_text_matches_the_word_by_word_reading(surah: int) -> None:
    fast = dict(quran_corpus.ayah_texts(surah))
    slow = {
        ayah: " ".join(word["arabic"] for word in words)
        for ayah, words in quran_corpus.words_for_surah(surah)
    }
    assert fast == slow


@pytest.mark.parametrize("surah", SAMPLE)
def test_a_surah_reads_the_same_as_its_ayahs_read_one_by_one(surah: int) -> None:
    for ayah, words in quran_corpus.words_for_surah(surah):
        assert words == quran_corpus.words_for_ayah(surah, ayah)


def test_ayahs_come_back_in_order_and_only_once() -> None:
    numbers = [ayah for ayah, _ in quran_corpus.words_for_surah(2)]
    assert numbers == sorted(numbers)
    assert len(numbers) == len(set(numbers)) == 286


def test_every_ayah_of_the_quran_can_be_described() -> None:
    """The FAM tag is spelled with a fatha in the corpus and without one in
    tags.json. Matching them literally raised KeyError on 1,283 ayahs."""
    for surah, ayah in quran_corpus._db().execute(
        "SELECT DISTINCT surah, ayah FROM segment"
    ):
        assert quran_corpus.words_for_ayah(surah, ayah), f"{surah}:{ayah} came back empty"


def test_a_surah_that_does_not_exist_is_none() -> None:
    assert quran_service.get_surah(115) is None
    assert quran_service.get_surah(0) is None


def test_reading_view_carries_no_word_grammar() -> None:
    """The whole point of the light path: ~2MB of segments stay unfetched."""
    surah = quran_service.get_surah(1)
    assert surah["ayah_count"] == 7
    assert all(ayah["words"] is None for ayah in surah["ayahs"])
    assert surah["ayahs"][0]["arabic"].startswith("بِسْمِ")


def test_studying_view_carries_the_grammar_and_the_meanings() -> None:
    surah = quran_service.get_surah(1, with_words=True)
    first = surah["ayahs"][0]
    assert first["words"], "asked for words and got none"
    assert first["words"][0]["grammar"], "a word came back with no grammar"


@pytest.mark.skipif(
    not quran_meanings.is_built(),
    reason="meanings.db not built, run backend/scripts/build_quran_meanings.py",
)
class TestTheEnglish:
    def test_a_word_is_numbered_the_same_as_the_corpus_numbers_it(self) -> None:
        """The English is keyed by word position, so if the two ever disagree the
        meanings would silently slide onto the wrong words."""
        for surah in SAMPLE:
            english = quran_meanings.for_surah(surah)
            for ayah, words in quran_corpus.words_for_surah(surah):
                if ayah in english:
                    assert max(english[ayah]) <= len(words), f"{surah}:{ayah} gloss past the last word"

    def test_the_reading_view_has_english(self) -> None:
        surah = quran_service.get_surah(112)
        assert all(ayah["english"] for ayah in surah["ayahs"])


# The hover gloss in the reading view. What matters is not that glosses exist,
# it is that a gloss is never put on a word it does not belong to: the reader
# lines these up against the printed words by position alone.


@pytest.mark.parametrize("surah", SAMPLE)
def test_every_glossed_ayah_has_one_gloss_per_printed_word(surah: int) -> None:
    glosses = quran_service.glosses_for_surah(surah)
    for ayah, text in quran_corpus.ayah_texts(surah):
        if ayah in glosses:
            assert len(glosses[ayah]) == len(text.split())


def test_the_one_ayah_the_two_sources_disagree_about_is_left_out() -> None:
    """37:130. إل ياسين is printed as two words and counted by the corpus as one.

    Included, it would shift nothing here but would hand the reader a list one
    short, and every gloss would sit on the word before its own.
    """
    if not quran_meanings.is_built():
        pytest.skip("meanings.db not built")
    assert 130 not in quran_service.glosses_for_surah(37)
    # And the rest of that surah is still glossed, rather than the whole surah
    # being dropped over one ayah.
    assert len(quran_service.glosses_for_surah(37)) > 100


def test_glosses_are_in_the_order_the_words_are_printed() -> None:
    if not quran_meanings.is_built():
        pytest.skip("meanings.db not built")
    first = quran_service.glosses_for_surah(1)[1]
    by_number = quran_meanings.for_ayah(1, 1)
    assert first == [by_number[n] for n in sorted(by_number)]
