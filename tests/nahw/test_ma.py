"""syntax/ma.py: the one place a step asks what a ما is (كافة on an إنّ sister, relative, مصدرية)."""
from backend.services.nahw.syntax import ma
from backend.services.nahw.syntax.facts import Sentence
from tests.nahw.test_naming import VERB, token


def test_a_ma_alone_or_cut_off_another_word():
    assert ma.is_ma(token(2, "مَا", "ما", "NOM", 0, "---"))
    assert ma.is_ma(token(2, "+مَا", "ما", "NOM", 1, "MOD"))  # إِنَّ+مَا
    assert not ma.is_ma(token(2, "+مَا", "ما", "NOM", 1, "MOD"), alone=True)
    assert not ma.is_ma(token(2, "مَنْ", "مَن", "NOM", 0, "---"))


def test_the_kaffa_ma_is_written_onto_an_inna_sister_only():
    assert ma.kaffa_sister("إِنَّمَا") == "إن"
    assert ma.kaffa_sister("مِمَّا") is None
    assert ma.stops_sister(token(1, "إِنَّ", "إِنَّ", "PRT", 0, "---"))
    assert ma.stops_sister(token(1, "كَأَنَّ", "كَأَنَّ", "PRT", 0, "---"))
    assert not ma.stops_sister(token(1, "مِنْ", "مِن", "PRT", 0, "---"))  # مِمَّا: the ما after a jar is no كافة


def kind_of(*after_ma):
    toks = [token(1, "أَكَلْتُ", "أَكَل", "VRB", 0, "---", **VERB), token(2, "مَا", "ما", "NOM", 1, "OBJ"), *after_ma]
    return ma.kind(toks[1], Sentence(toks))


def test_a_ma_whose_sila_has_room_for_its_aid_is_the_relative():
    # أكلتُ ما طبختَ: the verb lacks the object it may take, the place of the ما's pronoun
    assert kind_of(token(3, "طَبَخْتَ", "طَبَخ", "VRB", 2, "---", per="2", gen="m", num="s", **VERB)) == "relative"
    # أكلتُ ما طبختَه: the هـ that goes back to the ما
    assert kind_of(token(3, "طَبَخْتَ", "طَبَخ", "VRB", 2, "---", per="2", gen="m", num="s", **VERB),
                   token(4, "+هُ", "هُوَ", "NOM", 3, "OBJ", token_type="enc0", pos_camel="pron")) == "relative"


def test_a_ma_whose_verb_has_every_place_taken_is_masdariyya():
    # أكره ما يهمل الطلابُ دروسَهم: doer and object both written
    assert kind_of(token(3, "يُهْمِلُ", "أَهْمَل", "VRB", 2, "---", per="3", gen="m", num="s", **VERB),
                   token(4, "الطُّلَّابُ", "طالِب", "NOM", 3, "SBJ"),
                   token(5, "دُرُوسَ", "دَرْس", "NOM", 3, "OBJ")) == "masdar"


def test_no_verb_after_it_or_a_cut_off_piece_has_no_kind():
    assert kind_of(token(3, "زَيْدٌ", "زَيْد", "PROP", 2, "SBJ")) is None
    toks = [token(1, "إِنَّ", "إِنَّ", "PRT", 0, "---"), token(2, "+مَا", "ما", "NOM", 1, "MOD"),
            token(3, "يَخْشَى", "خَشِي", "VRB", 2, "---", **VERB)]
    assert ma.kind(toks[1], Sentence(toks)) is None


def told_by(word_form, word_lemma):
    from backend.services.nahw.syntax.repair.khabar import name_not_told_by_ma
    toks = [token(1, "زَيْدٌ", "زَيْد", "PROP", 0, "---"), token(2, word_form, word_lemma, "NOM", 1, "MOD"),
            token(3, "رَأَيْتُ", "رَأَى", "VRB", 2, "---", per="1", gen="m", num="s", **VERB),
            token(4, "+هُ", "هُوَ", "NOM", 3, "OBJ", token_type="enc0", pos_camel="pron")]
    s = Sentence(toks)
    name_not_told_by_ma(s)
    return toks[1]["pos"]


def test_only_a_ma_after_a_name_turns_to_the_negation():
    # زيدٌ ما رأيتُه: ما is for what has no mind, so after a person's name it negates the verb
    assert told_by("مَا", "ما") == "PRT"
    # زيدٌ مَن رأيتُه: مَن is for what has a mind and stays the relative
    assert told_by("مَنْ", "مَن") == "NOM"


def test_a_cut_off_ma_is_the_plus_piece_only():
    assert ma.cut_off(token(2, "+مَا", "ما", "NOM", 1, "MOD"))
    assert not ma.cut_off(token(2, "مَا", "ما", "NOM", 0, "---"))
    assert not ma.cut_off(token(2, "+مَا+", "ما", "NOM", 1, "MOD"))
