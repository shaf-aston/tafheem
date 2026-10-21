"""ما/مَن heading a verbless sentence, and the active participle the dictionary lacks."""
import pytest

from backend.services import iraab, noun_reader
from tests.nahw_helpers import needs_parser


def _roles(sentence):
    return [w["role"] for w in iraab.analyze(sentence)["words"]]


@needs_parser
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


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("مَا جَزَاؤُهُ إِلَّا سَجْنُهُ", ["حرف", "مبتدأ", "حرف", "خبر"]),  # إلا hung on the mubtada
    ("إِنْ هَذَا إِلَّا سِحْرٌ", ["حرف", "مبتدأ", "حرف", "خبر"]),  # إلا hung on the negation
    ("مَا مُحَمَّدٌ إِلَّا رَسُولٌ", ["حرف", "مبتدأ", "حرف", "خبر"]),
    # left alone: a verb takes the word after إلا, and لا of the genus keeps its own reading
    ("مَا جَاءَ إِلَّا زَيْدٌ", ["حرف", "فعل", "حرف", "فاعل"]),
    ("لَا إِلَهَ إِلَّا اللَّهُ", ["حرف", "اسم لا", "حرف", "بدل"]),
    ("إِنْ أَنْتُمْ إِلَّا تَكْذِبُونَ", ["حرف", "مبتدأ", "حرف", "فعل"]),  # a verb after إلا is its own sentence
])
def test_after_negation_and_illa_the_noun_is_the_khabar(sentence, roles):
    assert _roles(sentence) == roles


def _tok(id, form, pos, head, rel, **feats):
    return {"id": id, "form": form, "lemma": form, "pos": pos, "head": head, "rel": rel, "token_type": "baseword",
            "ud": "", "pos_camel": "verb" if pos == "VRB" else "noun", "vox": "na", "asp": "p" if pos == "VRB" else "na",
            "stt": "i", "cas": "u", "base": form, **feats}


@pytest.mark.parametrize("with_verb", [False, True])
def test_hasr_khabar_waits_for_a_verbless_clause(with_verb):
    """ما زيدٌ [قالَ] إلا حقٌّ: with a verb before it the word after إلا is that verb's, not a khabar."""
    from backend.services.syntax.repair.khabar import hasr_khabar
    words = [_tok(1, "ما", "PRT", 0, "---"), _tok(2, "زيد", "PROP", 1, "SBJ")]
    if with_verb:
        words.append(_tok(3, "قال", "VRB", 2, "MOD"))
    n = len(words)
    words += [_tok(n + 1, "إلا", "PRT", 2, "MOD"), _tok(n + 2, "حق", "NOM", n + 1, "OBJ")]
    hasr_khabar(words)
    told = words[-1]
    assert (told["head"], told["rel"]) == ((n + 1, "OBJ") if with_verb else (0, "---"))


@pytest.mark.parametrize("change, moved", [
    (None, True),
    ("not_hasr", False),      # ما زيدٌ في حقٍّ: only إلا restricts; في does not
    ("before_illa", False),   # the khabar is the word after إلا
    ("subject_particle", False),  # a mubtada is a noun
    ("told_verb", False),     # إن أنتم إلا تكذبون: a verb after إلا is a sentence, not this noun khabar
])
def test_hasr_khabar_needs_each_of_its_parts(change, moved):
    from backend.services.syntax.repair.khabar import hasr_khabar
    words = [_tok(1, "ما", "PRT", 0, "---"), _tok(2, "زيد", "PROP", 1, "SBJ"),
             _tok(3, "إلا", "PRT", 2, "MOD"), _tok(4, "حق", "NOM", 3, "OBJ")]
    told = words[3]
    if change == "not_hasr":
        words[2].update(form="في", lemma="في")
    elif change == "before_illa":
        words[2]["id"], told["id"], words[2]["head"], told["head"] = 4, 3, 2, 4
        words[2], words[3] = words[3], words[2]
    elif change == "told_verb":
        told.update(pos="VRB", pos_camel="verb")
    elif change == "subject_particle":
        words[1].update(pos="PRT", pos_camel="part")
    hasr_khabar(words)
    assert (told["head"] == 0) is moved
