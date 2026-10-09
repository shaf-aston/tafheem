"""The naming layer reads links plus typed vowels, so both are tested without a model."""
import pytest

from backend.services.syntax import facts, naming
from backend.services.syntax.naming import roles as named
from backend.services.harakat import typed_case, typed_passive


def roles(words, tokens):
    return [found["role"] for found in named(words, tokens)]


def token(id, form, lemma, pos, head, rel, **feats):
    base = {"id": id, "form": form, "lemma": lemma, "pos": pos, "head": head, "rel": rel,
            "token_type": "baseword", "ud": "", "pos_camel": "", "vox": "na", "asp": "na",
            "stt": "i", "cas": "u", "base": form.strip("+")}
    return {**base, **feats}


def test_typed_case_and_passive():
    assert typed_case("رِسَالَةً") == "a"
    assert typed_case("الْوَلَدُ") == "u"
    assert typed_case("الْبَيْتِ") == "i"
    assert typed_case("مُنْتَصِرِينَ") is None  # the plural ending hides it
    assert typed_passive("كُتِبَتِ", present=False)
    assert not typed_passive("كَتَبَ", present=False)
    assert not typed_passive("كُنْتَ", present=False)  # a hollow verb's damma before its تاء
    assert not typed_passive("كُنْتِ", present=False)
    assert not typed_passive("كُنَّا", present=False)
    assert typed_passive("حُفَّتِ", present=False)  # a doubled verb's shadda stands for the kasra
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
    from backend.services.harakat import vowel_agreement
    assert vowel_agreement("أَفَلَا", "آفِلاً") is None      # kasra and tanween the reader did not type
    assert vowel_agreement("أَفَلَا", "أَفَلا") is not None
    assert vowel_agreement("الْقُبُورِ", "القُبُورَ") is None  # the case typed is jarr
    assert vowel_agreement("افلا", "آفِلاً") == (0, 0)              # nothing typed, nothing contradicted


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


def clitic(id, form, head, rel, **feats):
    return token(id, form, form, "PRT", head, rel, token_type="prc2", pos_camel="conj", **feats)


VERB = dict(vox="a", asp="p")


def test_a_noun_after_an_atf_particle_is_matuf_but_an_oath_is_not():
    # جاء محمد وعلي: the و is attached, so the parser gives it as its own token
    toks = [token(1, "جاء", "جاء", "VRB", 0, "---", **VERB),
            token(2, "محمد", "محمد", "PROP", 1, "SBJ"),
            clitic(3, "و+", 2, "MOD"),
            token(4, "علي", "علي", "PROP", 3, "OBJ")]
    assert roles(["جَاءَ", "مُحَمَّدٌ", "وَعَلِيٌّ"], toks) == ["فعل", "فاعل", "معطوف"]
    # the same word typed apart is a base word of its own, and is a حرف
    toks[2] = token(3, "و", "و", "PRT", 2, "MOD", pos_camel="conj")
    assert roles(["جَاءَ", "مُحَمَّدٌ", "وَ", "عَلِيٌّ"], toks) == ["فعل", "فاعل", "حرف", "معطوف"]
    # والله: nothing comes before the و for it to join to, so it swears and the noun is majroor
    oath = [clitic(1, "و+", 3, "MOD"),
            token(2, "الله", "الله", "PROP", 1, "OBJ"),
            token(3, "أقسم", "أقسم", "VRB", 0, "---", vox="a", asp="i")]
    assert roles(["وَاللَّهِ", "أُقْسِمُ"], oath) == ["مجرور", "فعل"]
    # لكنّ is an inna sister, not a joiner
    toks = [token(1, "الجو", "جو", "NOM", 0, "---", stt="d"),
            token(2, "لكن", "لكن", "PRT", 1, "MOD"),
            token(3, "الشمس", "شمس", "NOM", 2, "OBJ", stt="d")]
    assert roles(["الْجَوُّ", "لَكِنَّ", "الشَّمْسَ"], toks)[2] != "معطوف"


def test_the_called_noun_is_munada_and_the_particle_is_a_harf():
    toks = [token(1, "يا", "يا", "PRT", 3, "MOD", pos_camel="part_voc"),
            token(2, "محمد", "محمد", "PROP", 1, "OBJ"),
            token(3, "أجلس", "أجلس", "VRB", 0, "---", **VERB)]
    assert roles(["يَا", "مُحَمَّدُ", "اجْلِسْ"], toks) == ["حرف", "منادى", "فعل"]
    # the nearest case: a real preposition still makes its noun majroor
    toks = [token(1, "جلس", "جلس", "VRB", 0, "---", **VERB),
            token(2, "في", "في", "PRT", 1, "MOD", pos_camel="prep"),
            token(3, "البيت", "بيت", "NOM", 2, "OBJ", stt="d")]
    assert roles(["جَلَسَ", "فِي", "الْبَيْتِ"], toks) == ["فعل", "حرف جر", "مجرور"]


def test_mustathna_follows_illa_only_in_a_positive_sentence():
    toks = [token(1, "حضر", "حضر", "VRB", 0, "---", **VERB),
            token(2, "الطلاب", "طالب", "NOM", 1, "SBJ", stt="d"),
            token(3, "إلا", "إلا", "PRT", 1, "MOD"),
            token(4, "زيدا", "زيد", "VRB", 3, "OBJ")]  # the parser tags this name a verb
    assert roles(["حَضَرَ", "الطُّلَّابُ", "إِلَّا", "زَيْدًا"], toks) == ["فعل", "فاعل", "حرف", "مستثنى"]
    # after a negation it is restriction, and the noun is simply the doer
    toks = [token(1, "ما", "ما", "PRT", 2, "MOD", pos_camel="part_neg"),
            token(2, "حضر", "حضر", "VRB", 0, "---", **VERB),
            token(3, "إلا", "إلا", "PRT", 2, "MOD"),
            token(4, "زيد", "زيد", "PROP", 2, "SBJ")]
    assert roles(["مَا", "حَضَرَ", "إِلَّا", "زَيْدٌ"], toks)[3] == "فاعل"


def test_kaada_takes_a_ism_and_leaves_its_present_verb_a_verb():
    toks = [token(1, "كاد", "كاد", "VRB", 0, "---", **VERB),
            token(2, "المريض", "مريض", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "يموت", "مات", "VRB", 1, "PRD", vox="a", asp="i")]
    assert roles(["كَادَ", "الْمَرِيضُ", "يَمُوتُ"], toks) == ["فعل", "اسم كاد", "فعل"]
    assert facts.completes_kaada(toks[2], facts.Sentence(toks)) and not facts.completes_kaada(toks[0], facts.Sentence(toks))
    # أخذ with a noun object is the ordinary verb 'took', not a commencement verb
    toks = [token(1, "أخذ", "أخذ", "VRB", 0, "---", **VERB),
            token(2, "الولد", "ولد", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "الكتاب", "كتاب", "NOM", 1, "OBJ", stt="d", cas="a")]
    assert roles(["أَخَذَ", "الْوَلَدُ", "الْكِتَابَ"], toks) == ["فعل", "فاعل", "مفعول به"]


def test_a_zarf_word_on_a_verb_is_mafool_fihi_but_not_as_a_subject():
    toks = [token(1, "جاء", "جاء", "VRB", 0, "---", **VERB),
            token(2, "يوم", "يوم", "NOM", 1, "MOD", stt="c", cas="a"),
            token(3, "الجمعة", "جمعة", "NOM", 2, "IDF", stt="d", cas="g")]
    assert roles(["جِئْتُ", "يَوْمَ", "الْجُمُعَةِ"], toks) == ["فعل", "مفعول فيه", "مضاف إليه"]
    # typed with a damma it is the doer, whatever the parser hung it on
    assert roles(["جَاءَ", "يَوْمٌ", "الْجُمُعَةِ"], toks)[1] != "مفعول فيه"
    toks[1]["rel"] = "SBJ"
    assert roles(["جَاءَ", "يَوْمُ", "الْجُمُعَةِ"], toks)[1] == "فاعل"


def test_tawkeed_needs_its_pronoun_so_a_bare_kull_is_a_plain_noun():
    toks = [token(1, "جاء", "جاء", "VRB", 0, "---", **VERB),
            token(2, "القوم", "قوم", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "كل", "كل", "NOM", 2, "MOD", stt="c", cas="n"),
            token(4, "+هم", "+هم", "NOM", 3, "IDF", pos_camel="pron", token_type="enc0")]
    assert roles(["جَاءَ", "الْقَوْمُ", "كُلُّهُمْ"], toks)[2] == "توكيد"
    toks = [token(1, "كل", "كل", "NOM", 3, "TPC", stt="c"),
            token(2, "الطلاب", "طالب", "NOM", 1, "IDF", stt="d", cas="g"),
            token(3, "حاضرون", "حاضر", "NOM", 0, "---")]
    assert roles(["كُلُّ", "الطُّلَّابِ", "حَاضِرُونَ"], toks)[0] != "توكيد"


def test_zanna_has_two_objects_and_an_ordinary_verb_does_not():
    toks = [token(1, "ظننت", "ظن", "VRB", 0, "---", **VERB),
            token(2, "الجو", "جو", "NOM", 1, "OBJ", stt="d", cas="a"),
            token(3, "باردا", "بارد", "NOM", 1, "MOD", ud="ADJ", cas="a")]
    assert roles(["ظَنَنْتُ", "الْجَوَّ", "بَارِدًا"], toks) == ["فعل", "مفعول به", "مفعول به"]
    toks[0].update(lemma="شرب", form="شربت")
    assert roles(["شَرِبْتُ", "الْمَاءَ", "بَارِدًا"], toks)[2] == "حال"


def test_a_question_particle_only_asks():
    toks = [token(1, "هل", "هل", "PRT", 3, "MOD", pos_camel="part_interrog"),
            token(2, "الطالب", "طالب", "NOM", 3, "SBJ", stt="d", cas="n"),
            token(3, "مجتهد", "مجتهد", "NOM", 0, "---", cas="n")]
    assert roles(["هَلِ", "الطَّالِبُ", "مُجْتَهِدٌ"], toks) == ["حرف", "مبتدأ", "خبر"]


def test_a_bare_name_after_a_noun_with_al_is_badal():
    toks = [token(1, "جاء", "جاء", "VRB", 0, "---", **VERB),
            token(2, "الخليفة", "خليفة", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "عمر", "عمر", "PROP", 2, "MOD")]
    assert roles(["جَاءَ", "الْخَلِيفَةُ", "عُمَرُ"], toks)[2] == "بدل"
    # without ال the first noun is a مضاف and the name its مضاف إليه
    toks[1].update(form="خليفة", stt="c")
    toks[2]["rel"] = "IDF"
    assert roles(["جَاءَ", "خَلِيفَةُ", "عُمَرَ"], toks)[2] == "مضاف إليه"


def test_noun_before_its_verb_is_mubtada_but_a_typed_fatha_makes_it_the_fronted_object():
    verb = token(2, "كتب", "كتب", "VRB", 0, "---", vox="a", asp="p")
    opening = [token(1, "الطالب", "طالب", "NOM", 2, "TPC", stt="d"), verb]
    assert roles(["الطالب", "كتب"], opening) == ["مبتدأ", "فعل"]
    assert roles(["الدرسَ", "كتب"], [token(1, "الدرس", "درس", "NOM", 2, "TPC", stt="d"), verb]) \
        == ["مفعول به", "فعل"]
    # the nearest case it must not touch: the subject after its verb
    after = [token(1, "كتب", "كتب", "VRB", 0, "---", vox="a", asp="p"),
             token(2, "الطالب", "طالب", "NOM", 1, "SBJ", stt="d")]
    assert roles(["كتب", "الطالب"], after) == ["فعل", "فاعل"]


def test_inna_khabar_verb_stays_a_verb_and_a_fronted_pp_gives_the_ism_to_the_noun():
    toks = [token(1, "ليت", "ليت", "PRT", 0, "---"),
            token(2, "الشباب", "شباب", "NOM", 1, "SBJ", stt="d"),
            token(3, "يعود", "عاد", "VRB", 1, "PRD", asp="i")]
    assert roles(["ليت", "الشباب", "يعود"], toks) == ["حرف", "اسم إن", "فعل"]
    toks = [token(1, "أن", "إن", "PRT", 0, "---"),
            token(2, "في", "في", "PRT", 1, "PRD"),
            token(3, "البيت", "بيت", "NOM", 2, "OBJ", stt="d"),
            token(4, "رجلا", "رجل", "NOM", 1, "PRD", cas="a")]
    assert roles(["إن", "في", "البيت", "رجلا"], toks)[3] == "اسم إن"
    toks = [token(1, "إن", "إن", "PRT", 0, "---"),
            token(2, "الطالب", "طالب", "NOM", 1, "SBJ", stt="d"),
            token(3, "مجتهد", "مجتهد", "NOM", 1, "PRD")]
    assert roles(["إن", "الطالب", "مجتهد"], toks)[2] == "خبر إن"


def test_bare_thumma_before_a_verb_is_the_particle_not_the_adverb():
    toks = [token(1, "قرأ", "قرأ", "VRB", 0, "---"),
            token(2, "ثم", "ثم", "NOM", 1, "MOD"),
            token(3, "نام", "نام", "VRB", 2, "OBJ")]
    assert roles(["قرأ", "ثم", "نام"], toks)[1] == "حرف"
    assert roles(["قرأ", "ثَمَّ", "نام"], toks)[1] != "حرف"


@pytest.mark.parametrize("zarf_head, verb_head, verb_rel", [(2, 0, "---"), (0, 1, "MOD")])
def test_fronted_zarf_is_mafool_fihi_whichever_way_the_parser_hangs_it(zarf_head, verb_head, verb_rel):
    # one CAMeL/onnx build makes the verb the root, another makes متى the root with the verb under it
    toks = [token(1, "متى", "متى", "NOM", zarf_head, "MOD" if zarf_head else "---", pos_camel="adv_interrog"),
            token(2, "سافر", "سافر", "VRB", verb_head, verb_rel, vox="a", asp="p"),
            token(3, "الرجل", "رجل", "NOM", 2, "SBJ", stt="d", cas="n")]
    assert roles(["مَتَى", "سَافَرَ", "الرَّجُلُ"], toks) == ["مفعول فيه", "فعل", "فاعل"]


@pytest.mark.parametrize("typed, stt, role", [
    ("الكِتَابَ", "d", "مفعول به"),   # the server's parser hangs it as MOD, not OBJ
    ("مُسْرِعًا", "i", "حال"),         # nearest case: an indefinite fatha there is still a hal
])
def test_a_definite_fatha_hung_on_a_verb_is_its_object(typed, stt, role):
    toks = [token(1, "NOAN", "بع", "PROP", 0, "---", pos_camel="noun_prop"),
            token(2, "x", "كتاب" if stt == "d" else "مسرع", "NOM", 1, "MOD", stt=stt, pos_camel="noun")]
    assert roles(["بِعْ", typed], toks) == ["فعل", role]


def test_every_role_the_code_names_is_declared_in_roles_json():
    from backend.services.nahw_book import clause_of, named_roles, role_units
    declared = set(naming.ROLES)
    used = set(vars(named_roles()).values())
    for unit in role_units():
        used |= {unit["child"], unit.get("head_as", unit["child"])}
    for role in declared:
        if clause := clause_of(role):
            used.add(clause["job"])
    assert used - declared == set()


def test_a_word_is_split_where_its_tokenisation_splits_it(monkeypatch):
    # ثُلْثَ_+هُ comes tagged NOM alone; its pronoun is still its own token
    from backend.services.syntax import catib_onnx
    monkeypatch.setattr(catib_onnx, "_clitic_token_feats", lambda tok, order, a: dict.fromkeys(
        ("pos_camel", "asp", "vox", "stt", "cas", "token_type"), "na"))
    _split_word = catib_onnx._split_word
    reading = {"atbtok": "ثُلْثَ_+هُ", "catib6": "NOM", "ud": "NOUN", "pos": "noun", "lex": "ثُلْث",
               "enc0": "3ms_poss", "stt": "c", "cas": "a"}
    assert [t["form"] for t in _split_word("ثُلُثَهُ", reading)] == ["ثلث", "+ه"]


def test_a_word_joined_in_front_is_split_with_its_own_tag(monkeypatch):
    # ف+_ليست comes tagged PRT alone, the فاء's tag; ليست is still a verb
    from backend.services.syntax import catib_onnx
    monkeypatch.setattr(catib_onnx, "_clitic_token_feats", lambda tok, order, a: dict.fromkeys(
        ("pos_camel", "asp", "vox", "stt", "cas", "token_type"), "na"))
    reading = {"atbtok": "فَ+_لَيْسَتِ", "catib6": "PRT", "ud": "CCONJ", "pos": "verb", "lex": "لَيْس", "asp": "p"}
    pieces = catib_onnx._split_word("فَلَيْسَتِ", reading)
    assert [(t["form"], t["pos"]) for t in pieces] == [("ف+", "PRT"), ("ليست", "VRB")]


@pytest.mark.parametrize("front, passive", [(1, True), (0, False)])
def test_a_passive_verb_is_read_past_the_waw_joined_in_front(front, passive):
    # وَيُغْسَلُ: the و's fatha is not the verb's first vowel; read as one word it hides the damma
    verb = token(1, "يغسل", "غسل", "VRB", 0, "---", asp="i", vox="a", typed="وَيُغْسَلُ", front=front)
    assert facts.is_passive(verb) is passive


def test_allahumma_is_called_with_no_particle_before_it():
    toks = [token(1, "اللهم", "اللهم", "PROP", 2, "MOD"),
            token(2, "اغفر", "غفر", "VRB", 0, "---", vox="a", asp="c")]
    found = named(["اللَّهُمَّ", "اغْفِرْ"], toks)
    assert (found[0]["role"], found[0]["case"]) == ("منادى", "mabni")


@pytest.mark.parametrize("typed, verb", [("نِعْمَ", True), ("نَعَمْ", False)])
def test_the_praise_verb_is_told_from_yes_by_its_fatha(typed, verb):
    toks = [token(1, "نعم", "نعم", "NOM", 0, "---", pos_camel="noun", stt="c"),
            token(2, "العبد", "عبد", "NOM", 1, "SBJ", stt="d", cas="n")]
    found = roles([typed, "الْعَبْدُ"], toks)
    assert (found[0] == "فعل") is verb
    assert found[1] == "فاعل" or not verb  # the praised word after the verb is its doer
