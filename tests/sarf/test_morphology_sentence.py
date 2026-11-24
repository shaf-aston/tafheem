"""Sentence context must decide undiacritised homographs.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import pytest

from backend.services.dictionary import roots
from backend.services.quran import corpus as quran_corpus
from backend.services.sarf import engine, morphology
from backend.services.text.harakat import vowel_agreement

VERB_SENTENCE = "ذهب الولد إلى المدرسة"  # "the boy went to school"
NOUN_SENTENCE = "الذهب غالٍ"  # "gold is expensive"

needs_camel = pytest.mark.skipif(
    engine.camel is None, reason="CAMeL Tools not installed"
)


def _pos_of(sentence: str, word: str) -> str:
    tags = morphology.analyze_sentence(sentence)
    return next(t["pos"] for t in tags if t["word"] == word)


@needs_camel
def test_a_reading_the_typed_vowels_contradict_gives_the_command_no_root():
    # كِلْ is كَالَ يَكِيلُ's command; CAMeL's كُلْ (أكل) carries a damma the typed kasra rules out
    assert morphology.analyze_sentence("كِلْ لَنَا")[0]["root"] == "كيل"


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
    assert agree("حِجَارَةٌ", "حَجّارُهُ") is None     # a typed ة is never the pronoun ه
    assert agree("حجاره", "حِجارَة") == (0, 0)           # a typed ه may be a ة written loosely: no verdict


def test_with_no_reading_agreeing_one_spelled_as_typed_is_kept():
    # حِجَارَةٌ "stones": the dictionary has only حَجّارَة, a vowel and a shadda off, and "his حَجّار"
    readings = [{"diac": "حَجّارُهُ", "atbtok": "حَجّارُ_+هُ"}, {"diac": "حَجّارَةٌ", "atbtok": "حَجّارَةٌ"}]
    assert morphology._reading("حِجَارَةٌ", readings)["diac"] == "حَجّارَةٌ"


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
@pytest.mark.parametrize("sentence, word, pos", [
    ("رَكِبُوا الْفُلْكَ", "الْفُلْكَ", "noun"),
    ("اِلْتَقَطَهُ بَعْضُ السَّيَّارَةِ", "اِلْتَقَطَهُ", "verb"),
])
def test_a_word_the_dictionary_reads_only_with_the_article_is_no_command(sentence: str, word: str, pos: str):
    # الْفُلْكَ: the dictionary has فَلَك only, its vowels not the ones typed; ال is a sign of the noun, so the word is
    # no command of a verb it has no record of (اُلْفُلْ + كَ); اِلْتَقَطَهُ, a verb it has, stays one
    assert _pos_of(sentence, word) == pos


@needs_camel
@pytest.mark.parametrize("sentence, lemma", [
    # فَاذْخَرْهَا: يَذْخَرُ is فَتَحَ's and سَمِعَ's, and the dictionary has neither past, so the closest cells name no
    # one past: the word is the verb alone, its فَ and هَا peeled off
    ("فَاذْخَرْهَا", "اذخر"),
    ("فَاقْبَلْهَا", "قبل"),   # nearest case: of the two, the dictionary has قَبِلَ, so the past settles it
])
def test_a_command_the_table_reads_with_no_one_past_is_named_by_its_own_letters(sentence: str, lemma: str):
    assert morphology.analyze_sentence(sentence)[0]["lemma"] == lemma


@needs_camel
@pytest.mark.skipif(not quran_corpus.is_loaded(), reason="corpus.db not built")
@pytest.mark.parametrize("word", ["رَأَيْتُ", "يَرَى", "تَرَ"])
def test_a_lemma_the_word_does_not_carry_is_the_qurans_lemma_of_its_root(word):
    # CAMeL files every form of رأى (see) under راوند (rhubarb), and ظن وأخواتها is known by its lemma
    assert morphology.analyze_sentence(word)[0]["lemma"] == "رأى"
    assert roots.readings(word)[0].lemma == "رأى"  # the dictionary reads it so too


@needs_camel
@pytest.mark.skipif(not quran_corpus.is_loaded(), reason="corpus.db not built")
def test_a_noun_takes_the_qurans_noun_lemma_not_its_verbs():
    assert morphology.analyze_sentence("ٱلْمُعْتَدِينَ")[0]["lemma"] == "معتدي"  # CAMeL: متعدي; اعتدى is the verb


@needs_camel
@pytest.mark.skipif(not quran_corpus.is_loaded(), reason="corpus.db not built")
@pytest.mark.parametrize("sentence, word, pos", [
    ("كَانَ اسْمُ أَبِيهِ آزَرَ", "آزَرَ", "noun_prop"),  # the Qur'an's name (6:74), in فاعَلَ's shape
    ("آزَرَ زَيْدٌ عَمْرًا", "آزَرَ", "verb"),            # opening the sentence: the verb stays
    ("كان اسم أبيه آزر", "آزر", "noun_prop"),             # typed bare, nothing after it for the verb to take
    ("قال إبراهيم لأبيه آزر", "آزر", "noun_prop"),
    ("الرجل آزر صديقه", "آزر", "verb"),                   # a noun after it: what the verb is done to
    ("آزر الجيش الشعب", "آزر", "verb"),
    ("قال لأبيه سافر", "سافر", "verb"),                   # the Qur'an knows no name سافر
    ("قال إبراهيم لأبيه آزر أنا ذاهب", "آزر", "noun_prop"),  # a new sentence opens after it
    ("في قلبي حنين", "حنين", "noun"),                     # a noun's shape: the word, not the Qur'an's name
])
def test_a_quran_name_in_a_verbs_shape(sentence, word, pos):
    assert _pos_of(sentence, word) == pos


@pytest.mark.parametrize("word, lemma", [
    # a hamza the vowels seat on و (its damma after a fatha) the dictionary writes on the stem's alif (يقرأه):
    # the word is read there and spelled on the typed seat, with a particle on it too
    ("يَقْرَؤُهُ", "قَرَأ"), ("يَمْلَؤُهُ", "مَلَأ"), ("فَيَقْرَؤُهُ", "قَرَأ"),
    # siblings: the dictionary's own spelling, and one it knows with the و seat, read as they were
    ("يَقْرَأُهُ", "قَرَأ"), ("رُؤُوسُهُمْ", "رَأْس"),
])
@needs_camel
def test_a_hamza_on_its_vowels_seat_is_read_on_the_stems(word, lemma):
    read = morphology.pick([word])[0]
    assert read["pos"] in ("verb", "noun") and read["lex"] == lemma and morphology.bare_letters(read["diac"])[-3:] == \
        morphology.bare_letters(word)[-3:]



@needs_camel
@pytest.mark.parametrize("sentence, root", [
    ("قِفْ هُنَا", "وقف"), ("ضَعْ يَدَكَ", "وضع"), ("كُلِي", "أكل"),    # a command alone: the root its jussive is
    ("ضَعْهُ هُنَا", "وضع"), ("عِدْنِي خَيْرًا", "وعد"),               # nearest: with its object on, read from the table
])
def test_a_command_whose_first_letter_fell_is_read_on_its_own_root(sentence: str, root: str):
    assert morphology.analyze_sentence(sentence)[0]["root"] == root   # not ضوع، كول، عدن


def test_signs_and_numbers_alone_are_no_word_and_get_no_reading():
    # an ayah's end sign and number with no word (۝ ٢٨ ۚ ،): nothing to read, not a crash
    assert morphology.pick([]) == []


@needs_camel
def test_a_word_the_letters_leave_open_carries_its_rival_reading():
    # كتب typed bare is كَتَبَ or كُتِبَ: the voice not chosen rides along for a second reading (morphology._rivals);
    # a word with a vowel typed on it speaks for itself and has none
    bare, voweled = morphology.pick(["كتب", "الطالب", "الدرس"]), morphology.pick(["كَتَبَ", "الطَّالِبُ", "الدَّرْسَ"])
    assert {bare[0]["vox"], bare[0]["rival"]["vox"]} == {"a", "p"}
    assert "rival" not in voweled[0]


@needs_camel
def test_the_overrides_and_passes_run_in_the_order_written():
    # pick reads each word through WORD_OVERRIDES, then the sentence through SENTENCE_PASSES, each in its list's order
    assert morphology.WORD_OVERRIDES[0] is morphology._name_adding_fewer
    assert morphology.WORD_OVERRIDES[-1] is morphology._by_shape
    assert morphology.SENTENCE_PASSES[-1] is morphology._rivals  # last: it reads every reading the others settled


def test_a_reading_in_the_other_voice_the_typed_vowels_contradict_does_not_stand():
    from backend.services.sarf.morphology import _voice_against
    active = {"asp": "i", "vox": "a"}
    passive = {"asp": "i", "vox": "p", "diac": "أُغار"}
    assert _voice_against(active, passive, "أَغَارُ")  # fatha typed on the hamza: not the passive
    assert not _voice_against(active, passive, "أُغَارُ")  # damma typed: it is the passive
    assert not _voice_against(active, {**passive, "vox": "a"}, "أَغَارُ")  # same voice: another باب's matter
    assert not _voice_against({"asp": "p", "vox": "p"}, {"asp": "p", "vox": "a", "diac": "خَلَقَ"}, "خُلِقَ")  # a passive typed keeps the active
