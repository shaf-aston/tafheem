"""Reading a whole surah: order, the English, and the hover glosses and lemmas.

Also covered: the vowel-mark mismatch that used to make a fifth of the Qur'an
return a 500, because a surah reader walks straight through all of it.

Run: python -m pytest tests/quran/test_quran_surah.py
"""
from __future__ import annotations

import pytest

from backend.services.text import arabic_text
from backend.services.quran import corpus as quran_corpus
from backend.services.quran import meanings as quran_meanings
from backend.services.quran import service as quran_service

pytestmark = pytest.mark.skipif(
    not quran_corpus.is_loaded(),
    reason="corpus.db not built, run backend/scripts/build_quran_corpus.py",
)

# Al-Fatiha, the longest surah, one with a FAM tag, and the shortest.
SAMPLE = (1, 2, 3, 112, 114)


def test_ayahs_come_back_in_order_and_only_once() -> None:
    numbers = [ayah for ayah, _ in quran_corpus.ayah_texts(2)]
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


def test_reading_view_carries_the_text() -> None:
    surah = quran_service.get_surah(1)
    assert surah["ayah_count"] == 7
    assert surah["ayahs"][0]["arabic"].startswith("بِسْمِ")


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
            for ayah, text in quran_corpus.ayah_texts(surah):
                if ayah in english:
                    assert max(english[ayah]) <= len(text.split()), f"{surah}:{ayah} gloss past the last word"

    def test_the_reading_view_has_english(self) -> None:
        surah = quran_service.get_surah(112)
        assert all(ayah["english"] for ayah in surah["ayahs"])


# The hover gloss in the reading view. What matters is not that glosses exist,
# it is that a gloss is never put on a word it does not belong to: the reader
# lines these up against the printed words by position alone.


@pytest.mark.parametrize("surah", SAMPLE)
def test_every_glossed_ayah_has_one_gloss_per_printed_word(surah: int) -> None:
    glosses, _ = quran_service.aligned_for_surah(surah)
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
    glosses, _ = quran_service.aligned_for_surah(37)
    assert 130 not in glosses
    # And the rest of that surah is still glossed, rather than the whole surah
    # being dropped over one ayah.
    assert len(glosses) > 100


def test_glosses_are_in_the_order_the_words_are_printed() -> None:
    if not quran_meanings.is_built():
        pytest.skip("meanings.db not built")
    first = quran_service.aligned_for_surah(1)[0][1]
    by_number = quran_meanings.for_ayah(1, 1)
    assert first == [by_number[n] for n in sorted(by_number)]


# The learnt-word underline. Same rule as the glosses: one lemma per printed
# word, or the ayah is left out, so a mark never lands on the wrong word.


@pytest.mark.parametrize("surah", SAMPLE)
def test_one_lemma_list_per_printed_word(surah: int) -> None:
    _, lemmas = quran_service.aligned_for_surah(surah)
    texts = dict(quran_corpus.ayah_texts(surah))
    assert lemmas.keys() == texts.keys()
    for ayah, text in texts.items():
        assert len(lemmas[ayah]) == len(text.split())


def test_a_word_carries_every_piece_it_is_built_from() -> None:
    # بِسْمِ is بِ + اسْم, and the meter counts a word by any of its pieces.
    bare = [[arabic_text.bare_letters(w) for w in word] for word in quran_service.aligned_for_surah(1)[1][1]]
    assert bare[0] == ["ب", "اسم"]
    # يَبْنَؤُمَّ (20:94) is two taught words in one: ابْن and أُمّ.
    assert [arabic_text.bare_letters(w) for w in quran_service.aligned_for_surah(20)[1][94][1]][-2:] == ["ابن", "ام"]


def test_the_ayah_printed_with_an_extra_space_has_no_lemmas() -> None:
    # 37:130, the same ayah the glosses leave out.
    assert 130 not in quran_service.aligned_for_surah(37)[1]


def test_the_glosses_route_carries_the_lemmas() -> None:
    from fastapi.testclient import TestClient

    from backend.main import app

    body = TestClient(app).get("/api/quran/surah/1/glosses").json()
    assert body["lemmas"]["1"] == quran_service.aligned_for_surah(1)[1][1]
