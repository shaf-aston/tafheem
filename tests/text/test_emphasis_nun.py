"""The nun of emphasis read off the typed word alone (backend.services.text.harakat).

Before the doubled nun of emphasis the five verbs' own nun goes so three nuns do not meet: the men's و goes with it and
leaves its damma (لَيَقُولُنَّ), the one woman's ي leaves its kasra (لَتَقُولِنَّ), unless a fatha before keeps them with
their own vowel (لَتَرَوُنَّ، لَتَرَيِنَّ; Alfiyya, نونا التوكيد, page unchecked). One verb's damma goes to the fatha
(لَتَقُولَنَّ, built). A root's own doubled nun (لَنْ يَظُنَّ، أَيَظُنُّ) is none of these.
"""
import pytest

from backend.services.text.harakat import five_before_emphasis, five_verb_nun, typed_passive


@pytest.mark.parametrize("word, five, gone", [
    ("لَتَرَيِنَّ", False, True),  # a fatha before keeps the woman's ي, with its kasra
    ("لَتُبْعَثُنَّ", False, True),  # the men's و gone, its damma left
    ("أَيَظُنُّ", False, False),  # a damma on the doubled nun: the root's own, in raf'
    ("لَتَقُولَنَّ", True, False),  # a fatha before the nun: the one man's, though a tag names the woman
    ("يَظُنَّ", False, False),  # لَنْ يَظُنَّ: a doubled root's nun after its first letter
    ("فَيَظُنَّ", False, False),  # a ف written on it is no letter of the verb
])
def test_the_five_verbs_nun_goes_before_the_nun_of_emphasis(word, five, gone):
    assert five_before_emphasis(word, five=five) is gone


def test_the_kept_ya_before_the_nun_of_emphasis_is_no_kept_nun():
    assert five_verb_nun("لَتَرَيِنَّ") == "dropped"  # تَرَيْنَ: the nun went before the nun of emphasis


@pytest.mark.parametrize("word, passive", [
    ("تُبْعَثُنَّ", True),  # the fatha before the last stem letter, under the men's damma
    ("نُخْرِجَنَّ", False),  # the fatha is the built ending's, on the last letter
    ("تُكْرِمَانِّ", False),  # the pair's ا before the doubled nun: the stem stops before it
])
def test_a_present_passive_is_read_before_the_nun_of_emphasis(word, passive):
    assert typed_passive(word, present=True) is passive
