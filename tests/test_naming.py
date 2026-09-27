"""The naming layer reads links plus typed vowels, so both are tested without a model."""
import pytest

from backend.services.syntax.naming import roles as named, typed_case, typed_passive


def roles(words, tokens):
    return [found["role"] for found in named(words, tokens)]


def token(id, form, lemma, pos, head, rel, **feats):
    base = {"id": id, "form": form, "lemma": lemma, "pos": pos, "head": head, "rel": rel,
            "token_type": "baseword", "ud": "", "pos_camel": "", "vox": "na", "asp": "na",
            "stt": "i", "cas": "u"}
    return {**base, **feats}


def test_typed_case_and_passive():
    assert typed_case("رِسَالَةً") == "a"
    assert typed_case("الْوَلَدُ") == "u"
    assert typed_case("الْبَيْتِ") == "i"
    assert typed_case("مُنْتَصِرِينَ") is None  # the plural ending hides it
    assert typed_passive("كُتِبَتِ", present=False)
    assert not typed_passive("كَتَبَ", present=False)
    assert typed_passive("يُكَافَأُ", present=True)


def test_verb_sentence():
    toks = [token(1, "كتب", "كتب", "VRB", 0, "---", vox="a", asp="p"),
            token(2, "الطالب", "طالب", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "رسالة", "رسالة", "NOM", 1, "OBJ", cas="a")]
    assert roles(["كَتَبَ", "الطَّالِبُ", "رِسَالَةً"], toks) == ["فعل", "فاعل", "مفعول به"]


def test_passive_is_read_from_the_vowels():
    # the morphology has no passive reading for this verb, the typed damma and kasra do
    toks = [token(1, "كتبت", "كتب", "VRB", 0, "---", vox="a", asp="p"),
            token(2, "الرسالة", "رسالة", "NOM", 1, "SBJ", stt="d", cas="n")]
    assert roles(["كُتِبَتِ", "الرِّسَالَةُ"], toks) == ["فعل", "نائب فاعل"]


def test_kana_and_inna_are_told_apart():
    kana = [token(1, "كان", "كان", "VRB", 0, "---", asp="p"),
            token(2, "المعلم", "معلم", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "حاضرا", "حاضر", "NOM", 1, "PRD", ud="ADJ", cas="a")]
    assert roles(["كَانَ", "الْمُعَلِّمُ", "حَاضِرًا"], kana) == ["فعل", "اسم كان", "خبر كان"]
    # كأن folds onto كان once hamza is dropped, so it must be matched as written
    kaanna = [token(1, "كأن", "كأن", "PRT", 0, "---", pos_camel="verb_pseudo"),
              token(2, "القمر", "قمر", "NOM", 1, "SBJ", stt="d", cas="a"),
              token(3, "مصباح", "مصباح", "NOM", 1, "PRD")]
    assert roles(["كَأَنَّ", "الْقَمَرَ", "مِصْبَاحٌ"], kaanna) == ["حرف", "اسم إن", "خبر إن"]


def test_naat_needs_the_definiteness_to_match():
    definite = [token(1, "الطبيب", "طبيب", "NOM", 0, "---", stt="d", cas="n"),
                token(2, "الماهر", "ماهر", "NOM", 1, "MOD", ud="ADJ", stt="d", cas="n")]
    assert roles(["الطَّبِيبُ", "الْمَاهِرُ"], definite)[1] == "صفة"
    khabar = [token(1, "السماء", "سماء", "NOM", 0, "---", stt="d", cas="n"),
              token(2, "صافية", "صاف", "NOM", 1, "MOD", ud="ADJ", stt="i", cas="n")]
    assert roles(["السَّمَاءُ", "صَافِيَةٌ"], khabar) == ["مبتدأ", "خبر"]


def test_case_ignores_an_attached_pronoun():
    # the fatha of حَالُكَ belongs to the kaf; the noun's case is the damma before it
    toks = [token(1, "حال", "حال", "NOM", 0, "---", stt="c", cas="n"),
            token(2, "+ك", "+ك", "NOM", 1, "IDF", token_type="enc0", pos_camel="pron")]
    assert named(["حَالُكَ"], toks)[0]["case"] == "raf'"
    assert typed_case("حَالُكَ") == "a"  # read plainly it is the pronoun's vowel


def test_question_word_is_the_fronted_khabar():
    toks = [token(1, "كيف", "كيف", "NOM", 0, "---", ud="ADV", pos_camel="adv_interrog", cas="u"),
            token(2, "حال", "حال", "NOM", 1, "TPC", stt="c", cas="n"),
            token(3, "+ك", "+ك", "NOM", 2, "IDF", token_type="enc0", pos_camel="pron")]
    assert roles(["كَيْفَ", "حَالُكَ"], toks) == ["خبر", "مبتدأ"]
    # كيف is mabni: its fatha is part of the word, not a case
    assert [found["case"] for found in named(["كَيْفَ", "حَالُكَ"], toks)] == ["mabni", "raf'"]


@pytest.mark.parametrize("words", [["كَتَبَ"], ["كَتَبَ", "زَيْدٌ", "دَرْسًا"]])
def test_nothing_is_guessed_when_the_split_does_not_line_up(words):
    toks = [token(1, "كتب", "كتب", "VRB", 0, "---"), token(2, "زيد", "زيد", "NOM", 1, "SBJ")]
    if len(words) != 2:
        assert roles(words, toks) == [None] * len(words)


# ── أَفَلَا يَعْلَمُ إِذَا بُعْثِرَ مَا فِي الْقُبُورِ: what the parser path got wrong ──

def test_a_reading_that_contradicts_the_typed_vowels_does_not_agree():
    from backend.services.syntax.naming import agrees_with_typed
    assert not agrees_with_typed("أَفَلَا", "آفِلاً")      # kasra and tanween the reader did not type
    assert agrees_with_typed("أَفَلَا", "أَفَلا")
    assert not agrees_with_typed("الْقُبُورِ", "القُبُورَ")  # the case typed is jarr
    assert agrees_with_typed("افلا", "آفِلاً")              # nothing typed, nothing contradicted


def test_the_parser_keeps_the_best_reading_that_agrees_with_the_vowels():
    from backend.services.syntax.catib_onnx import _reading
    readings = [{"diac": "آفِلاً", "atbtok": "آفِلاً", "pos": "noun"},
                {"diac": "افلا", "atbtok": "NOAN", "pos": "noun_prop"},
                {"diac": "أَفَلا", "atbtok": "أَفَلا", "pos": "verb"}]
    assert _reading("أَفَلَا", readings)["pos"] == "verb"
    # a guessed proper noun never wins just for having no vowels to disagree with,
    # and with no real reading agreeing the favourite stands
    assert _reading("بُعْثِرَ", [{"diac": "بَعْثَرَ", "atbtok": "بَعْثَرَ"},
                                 {"diac": "بعثر", "atbtok": "NOAN"}])["diac"] == "بَعْثَرَ"


def test_a_passive_verb_has_no_object_before_its_naib_fail():
    # بُعْثِرَ مَا: the parser drew مَا as the object, but a passive verb has no doer
    toks = [token(1, "بعثر", "بعثر", "VRB", 0, "---", vox="a", asp="p"),
            token(2, "ما", "ما", "NOM", 1, "OBJ", pos_camel="pron_rel", cas="na")]
    assert roles(["بُعْثِرَ", "مَا"], toks) == ["فعل", "نائب فاعل"]
    # the second noun of a passive verb is still its object: أُعْطِيَ زَيْدٌ دِرْهَمًا
    toks = [token(1, "أعطي", "أعطى", "VRB", 0, "---", vox="p", asp="p"),
            token(2, "زيد", "زيد", "NOM", 1, "SBJ", cas="n"),
            token(3, "درهما", "درهم", "NOM", 1, "OBJ", cas="a")]
    assert roles(["أُعْطِيَ", "زَيْدٌ", "دِرْهَمًا"], toks) == ["فعل", "نائب فاعل", "مفعول به"]


def test_a_tamyeez_never_comes_before_what_it_clarifies():
    # the parser's آفِلًا hung off يَعْلَمُ; accusative, indefinite, first in the sentence
    toks = [token(1, "آفلا", "آفل", "NOM", 2, "MOD", cas="a", stt="i"),
            token(2, "يعلم", "علم", "VRB", 0, "---", vox="a", asp="i")]
    assert roles(["آفِلًا", "يَعْلَمُ"], toks)[0] is None
    # after it, it is one: زَادَ الْمَاءُ عُمْقًا
    toks = [token(1, "زاد", "زاد", "VRB", 0, "---", vox="a", asp="p"),
            token(2, "الماء", "ماء", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "عمقا", "عمق", "NOM", 1, "MOD", cas="a", stt="i")]
    assert roles(["زَادَ", "الْمَاءُ", "عُمْقًا"], toks)[2] == "تمييز"
