"""ما/مَن heading a verbless sentence, and the active participle the dictionary lacks."""
import pytest

from backend.services import iraab, noun_reader


def _roles(sentence):
    return [w["role"] for w in iraab.analyze(sentence)["words"]]


@pytest.mark.parametrize("sentence, roles", [
    ("مَا هِيَ", ["مبتدأ", "خبر"]),
    ("مَنْ أَبُوكَ", ["مبتدأ", "خبر"]),
    ("الْقَارِعَةُ مَا الْقَارِعَةُ", ["مبتدأ", "مبتدأ", "خبر"]),
    ("الْحَاقَّةُ مَا الْحَاقَّةُ", ["مبتدأ", "مبتدأ", "خبر"]),
    # متى/كيف stand for a time or state: the khabar brought forward, not the mubtada
    ("مَتَى السَّفَرُ", ["خبر", "مبتدأ"]),
])
def test_question_noun_heads_its_sentence(sentence, roles):
    assert _roles(sentence) == roles


@pytest.mark.parametrize("word, lex, pattern, gen, stt", [
    ("الْحَاقَّةُ", "حاق", "ال1َا2ّة", "f", "d"),
    ("الْقَارِعَةُ", "قارع", "ال1َا2ِ3ة", "f", "d"),
    ("كَاتِبٌ", "كاتب", "1َا2ِ3", "m", "i"),
])
def test_active_participle_read_off_sarf(word, lex, pattern, gen, stt):
    r = noun_reader.reading_of(word)
    assert (r["pos"], r["lex"], r["pattern"], r["gen"], r["stt"]) == ("adj", lex, pattern, gen, stt)


def test_a_reading_spelled_with_other_letters_does_not_fit():
    from backend.services.morphology import _agreeing
    assert not _agreeing("الْحَاقَّةُ", [{"diac": "إِلْحاقُهُ", "atbtok": "إِلْحاق+ُهُ"}])
