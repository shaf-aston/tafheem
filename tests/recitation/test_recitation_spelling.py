"""The ayah respelt as the Qur'an ear writes it. Each case is one of its habits;
the expected side is what the ear itself wrote for that ayah."""
from backend.services.recitation.spelling import as_heard

# Shadda then fatha, as the ear writes it. Typed Arabic usually puts the vowel
# first, which looks identical and is the bug this module exists for.
SF = "َّ"
SK = "ِّ"  # shadda then kasra


def test_standing_alif_and_shadda_order():
    assert as_heard("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ") == ["بِسْمِ", f"الل{SF}هِ", f"الر{SF}حْمَنِ", f"الر{SF}حِيمِ"]


def test_a_merged_letter_loses_its_shadda_and_the_bare_noon_gets_sukun():
    assert as_heard("عَلَىٰ هُدًى مِّن رَّبِّهِمْ ۖ") == ["عَلَى", "هُدًى", "مِنْ", f"رَب{SK}هِمْ"]


def test_long_vowels_and_silent_lam_stay_bare():
    assert as_heard("فِي الَّذِي آمَنُوا يُنفِقُونَ") == ["فِي", f"ال{SF}ذِي", "آمَنُوا", "يُنْفِقُونَ"]


def test_a_pause_sign_is_not_a_word_and_nothing_is_nothing():
    assert as_heard("ۚ ۛ") == []
    assert as_heard("") == []


def test_the_same_word_twice_is_kept_twice():
    assert as_heard("عَلَيْهِمْ عَلَيْهِمْ") == ["عَلَيْهِمْ", "عَلَيْهِمْ"]
