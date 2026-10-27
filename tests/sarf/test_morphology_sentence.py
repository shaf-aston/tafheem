"""Sentence context must decide undiacritised homographs.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import pytest

from backend.services.quran import corpus as quran_corpus
from backend.services.sarf import morphology
from backend.services.text.harakat import vowel_agreement

VERB_SENTENCE = "ذهب الولد إلى المدرسة"  # "the boy went to school"
NOUN_SENTENCE = "الذهب غالٍ"  # "gold is expensive"

needs_camel = pytest.mark.skipif(
    not morphology._CAMEL_AVAILABLE, reason="CAMeL Tools not installed"
)


def _pos_of(sentence: str, word: str) -> str:
    tags = morphology.analyze_sentence(sentence)
    return next(t["pos"] for t in tags if t["word"] == word)


@needs_camel
def test_homograph_reads_as_verb_when_the_sentence_needs_one():
    # ذهب on its own ranks as the noun "gold"; only the sentence makes it a verb.
    assert _pos_of(VERB_SENTENCE, "ذهب") == "verb"


@needs_camel
def test_following_noun_keeps_its_noun_reading():
    assert _pos_of(VERB_SENTENCE, "الولد") == "noun"


@needs_camel
def test_same_root_stays_a_noun_when_the_sentence_has_no_verb():
    assert _pos_of(NOUN_SENTENCE, "الذهب") == "noun"


@needs_camel
def test_fully_diacritised_input_settles_its_own_reading():
    # Exact-diacritic match must win over the disambiguator's ranking.
    tags = morphology.analyze_sentence("ذَهَبَ الوَلَدُ")
    assert tags[0]["pos"] == "verb"


def test_empty_sentence_returns_no_tags():
    assert morphology.analyze_sentence("   ") == []


@needs_camel
def test_incomplete_root_is_reported_as_no_root_not_as_a_placeholder():
    # The database gives ولد the root "#.ل.د", an unresolved first radical.
    tags = morphology.analyze_sentence(VERB_SENTENCE)
    roots = [t["root"] for t in tags]
    assert all("#" not in r for r in roots), roots


@needs_camel
def test_a_fully_known_root_still_renders():
    tags = morphology.analyze_sentence(VERB_SENTENCE)
    # Plain letters, no hyphens: the same string is what the Define and
    # In-the-Qur'an buttons search with, and "د-ر-س" is in no index.
    assert next(t for t in tags if t["word"] == "المدرسة")["root"] == "درس"


@needs_camel
def test_typed_vowels_overrule_the_statistics():
    # Ranked alone, فَتَحَ is the noun فَتْح; its vowels say it is the verb.
    assert _pos_of("فَتَحَ زَيْدٌ الْبَابَ", "فَتَحَ") == "verb"


@needs_camel
@pytest.mark.parametrize("sentence, word, kind", [
    ("أَقِمِ الصَّلَاةَ", "أَقِمِ", "fi'l"), ("بِعِ الْكِتَابَ", "بِعِ", "fi'l"),  # the sukun moved to a kasra
    ("قَدِ اسْتَقَامَ الْأَمْرُ", "قَدِ", "harf"),  # the same kasra on a particle leaves it a particle
    ("بِسْمِ اللَّهِ", "بِسْمِ", "ism")])           # and on a noun it is the kasra of jarr
def test_a_kasra_before_hamzat_al_wasl_settles_nothing(sentence, word, kind):
    tag = next(t for t in morphology.analyze_sentence(sentence) if t["word"] == word)
    assert tag["type"] == kind
    assert (tag.get("aspect") == "c") is (kind == "fi'l")


@needs_camel
def test_glued_punctuation_no_longer_hides_the_word():
    tags = morphology.analyze_sentence("مَرْحَبًا، كَيْفَ حَالُكَ؟")
    assert [t["word"] for t in tags] == ["مَرْحَبًا", "كَيْفَ", "حَالُكَ"]
    assert all(t["gloss"] != "NO_ANALYSIS" for t in tags)


def test_vowel_agreement():
    agree = vowel_agreement
    assert agree("فَتَحَ", "فَتْحَ") is None          # fatha typed where the reading has sukun
    assert agree("فَتَحَ", "فَتَحَ") == (3, 0)
    assert agree("زَيْدٌ", "زَيْد") == (2, 0)               # a bare letter in the reading agrees
    assert agree("كتب", "كَتَبَ") == (0, 0)                 # nothing typed, nothing to weigh
    assert agree("زَيْدٌ", "زَيْدٍ") is None          # the same letter, a different ending
    assert agree("زَيْدٌ", "زَيْدًا") == (0, 0)             # the tanween alef adds a letter: no verdict


@needs_camel
@pytest.mark.parametrize("past, seen", [
    ("هَدَى", True), ("آتَى", True), ("اِسْتَغْفَرَ", True),   # its hamzat al-wasl written ٱ in the dictionary
    ("ضَرَبَ", True),
    ("هَدَنَ", False),   # a verb no text the dictionary learnt from uses
    ("هَدَا", False),    # read as هَدَأ: the same letters but its hamza
    ("ضَرِبَ", False),   # read as ضَرَبَ: the same letters but a vowel both write
])
def test_a_verb_is_seen_only_as_the_dictionary_spells_it(past: str, seen: bool):
    assert morphology._seen_verb(past) is seen


@needs_camel
@pytest.mark.parametrize("word, lemma", [("اِهْدِنَا", "هدى"), ("آتِنَا", "آتى"), ("أَعْطِنَا", "أعطى")])
def test_a_command_with_its_object_written_on_is_split_off_the_pronoun(word: str, lemma: str):
    # اِهْدِنَا، آتِنَا: the dictionary has no reading, sarf's closest is a dual of a verb no text uses (هَدَنَ)
    tag = morphology.analyze_sentence(f"{word} كِتَابًا")[0]
    assert (tag["aspect"], tag["number"], tag["lemma"], tag["enclitic"]) == ("c", "s", lemma, "1p_dobj")


@needs_camel
def test_a_command_the_table_reads_with_no_one_past_is_named_by_its_own_letters():
    # فَاقْبَلْهَا: the table's closest cells name no one past, so the word is the verb alone, its فَ and هَا peeled off
    tag = morphology.analyze_sentence("فَاقْبَلْهَا")[0]
    assert tag["lemma"] == "اقبل"


@needs_camel
@pytest.mark.skipif(not quran_corpus.is_loaded(), reason="corpus.db not built")
@pytest.mark.parametrize("word", ["رَأَيْتُ", "يَرَى", "تَرَ"])
def test_a_lemma_the_word_does_not_carry_is_the_qurans_lemma_of_its_root(word):
    # CAMeL files every form of رأى (see) under راوند (rhubarb), and ظن وأخواتها is known by its lemma
    assert morphology.analyze_sentence(word)[0]["lemma"] == "رأى"


@needs_camel
@pytest.mark.skipif(not quran_corpus.is_loaded(), reason="corpus.db not built")
def test_a_noun_takes_the_qurans_noun_lemma_not_its_verbs():
    assert morphology.analyze_sentence("ٱلْمُعْتَدِينَ")[0]["lemma"] == "معتدي"  # CAMeL: متعدي; اعتدى is the verb
