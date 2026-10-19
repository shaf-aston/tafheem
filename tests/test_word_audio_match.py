"""A quiz word may only borrow a reciter's recording of the very same word."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend/scripts"))
from build_word_audio import audio_path, matches

same = matches


def test_uthmani_spelling_folds_to_the_plain_word():
    assert same("كِتَاب", "كِتَٰبْ")          # dagger alef is a full alef
    assert same("عَسَى", "عَسَىٰ")             # dagger on alef maqsura adds nothing


def test_a_bare_ending_never_borrows_a_case_ending_the_screen_does_not_show():
    # The reciter says the ayah's ending: أَثِيمٍ is heard as athīmin.
    assert not same("أَثِيم", "أَثِيمٍ")
    assert not same("عَذَاب", "عَذَابٌ")
    assert same("عَذَاب", "عَذَابْ")
    assert same("أَبَى", "أَبَىٰ")               # a long vowel at the end carries no case


def test_a_joining_alif_is_never_borrowed():
    # Mid-ayah the reciter runs over ٱ, so ٱبْتَغَىٰ is heard as btaghā.
    assert not same("ابْتَغَى", "ٱبْتَغَىٰ")
    assert not same("اسْتَمْسَكَ", "ٱسْتَمْسَكَ")


def test_a_file_is_named_by_the_word_place_not_quran_coms_audio_url():
    # 4:88's 14th word is أَضَلَّ; quran.com's audio_url says 016, which says وَمَن.
    assert audio_path("4:88", 14) == "wbw/004_088_014.mp3"
    assert audio_path("52:24", 6) == "wbw/052_024_006.mp3"


def test_a_sukun_is_not_a_vowel():
    assert not same("أَكْل", "أَكَلَ")          # noun vs verb


def test_a_written_ending_must_match():
    assert not same("شَكَّ", "شَكٍّ")           # verb vs noun


def test_a_word_with_no_vowels_is_not_guessed():
    assert not same("كتب", "كُتِبَ")


def test_different_letters_never_match():
    assert not same("كِتَاب", "ٱلْكِتَٰبُ")      # the article is a different word
    assert not same("عَالِم", "عَالَم")          # identical letters, different vowel
