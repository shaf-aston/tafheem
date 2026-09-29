"""A quiz word may only borrow a reciter's recording of the very same word."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend/scripts"))
from build_word_audio import compatible, letters  # noqa: E402


def same(quiz: str, quran: str) -> bool:
    return compatible(letters(quiz), letters(quran))


def test_uthmani_spelling_folds_to_the_plain_word():
    assert same("كِتَاب", "كِتَٰبٌ")          # dagger alef is a full alef
    assert same("اسْتَمْسَكَ", "ٱسْتَمْسَكَ")  # alef wasla is an alef
    assert same("عَسَى", "عَسَىٰ")             # dagger on alef maqsura adds nothing


def test_a_bare_dictionary_ending_accepts_the_case_ending():
    assert same("عَذَاب", "عَذَابٌ")


def test_a_sukun_is_not_a_vowel():
    assert not same("أَكْل", "أَكَلَ")          # noun vs verb


def test_a_written_ending_must_match():
    assert not same("شَكَّ", "شَكٍّ")           # verb vs noun


def test_a_word_with_no_vowels_is_not_guessed():
    assert not same("كتب", "كُتِبَ")


def test_different_letters_never_match():
    assert not same("كِتَاب", "ٱلْكِتَٰبُ")      # the article is a different word
    assert not same("عَالِم", "عَالَم")          # identical letters, different vowel
