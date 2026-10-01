"""Step 5: the vowel the reader typed is evidence the parser may not overrule.

Each test pairs the case that fires with the nearest one that must not, since
the parser is fed letters only and the same links come back for both.
"""
from backend.services.syntax import tree, vowels
from tests.test_naming import roles, token
from tests.test_syntax_tree import built

VERB = dict(vox="a", asp="p")


def after_verb(noun_word, rel="SBJ", verb_word="أكل", **verb):
    toks = [token(1, "أكل", "أكل", "VRB", 0, "---", **{**VERB, **verb}),
            token(2, "الطعام", "طعام", "NOM", 1, rel, stt="d", cas="n")]
    return roles([verb_word, noun_word], toks)[1]


def test_typed_fatha_after_an_active_verb_is_the_object_damma_the_doer():
    assert after_verb("الطَّعَامَ") == "مفعول به"
    assert after_verb("الطَّعَامُ") == "فاعل"
    assert after_verb("الطَّعَامَ", rel="IDF") == "مفعول به"  # the parser hung it as a mudaf-ilayh


def test_unvowelled_noun_after_a_verb_keeps_the_old_reading():
    assert after_verb("الطعام") == "فاعل"
    assert after_verb("الطعام", rel="OBJ") == "فاعل"  # a lone "object" is the doer


def test_nominative_noun_hung_as_a_modifier_of_the_verb_is_its_doer_only_when_typed():
    assert after_verb("الطَّالِبُ", rel="MOD") == "فاعل"
    assert after_verb("الطالب", rel="MOD") is None


def test_typed_kasra_on_a_noun_hung_off_a_verb_is_not_a_doer():
    assert after_verb("الطَّعَامِ", rel="IDF") == "مضاف إليه"


def test_passive_verb_takes_a_naib_fail_and_draws_a_verbal_unit():
    # CATiB tags the passive as VRB-PASS, which used to be missed as a verb
    toks = [token(1, "كتب", "كتب", "VRB-PASS", 0, "---", vox="p", asp="p"),
            token(2, "الدرس", "درس", "NOM", 1, "OBJ", stt="d", cas="n")]
    words = ["كُتِبَ", "الدَّرْسُ"]
    assert roles(words, toks) == ["فعل", "نائب فاعل"]
    drawn = built(words, toks)
    assert drawn["tree"]["label"] == tree.VERBAL


def test_passive_with_a_typed_fatha_keeps_that_noun_as_an_object():
    toks = [token(1, "أعطي", "أعطى", "VRB-PASS", 0, "---", vox="p", asp="p"),
            token(2, "زيد", "زيد", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "كتابا", "كتاب", "NOM", 1, "OBJ", cas="a")]
    assert roles(["أُعْطِيَ", "زَيْدٌ", "كِتَابًا"], toks) == ["فعل", "نائب فاعل", "مفعول به"]


def test_a_noun_after_a_preposition_stays_majroor_on_a_typed_kasra():
    toks = [token(1, "في", "في", "PRT", 0, "---"),
            token(2, "البيت", "بيت", "NOM", 1, "OBJ", stt="d", cas="g")]
    assert roles(["فِي", "الْبَيْتِ"], toks) == ["حرف جر", "مجرور"]


def test_a_typed_sukun_or_vowel_is_an_answer_when_choosing_a_reading():
    # فَهِمَ (he understood) is not the noun فَهْمَ
    assert not vowels.agrees_with_typed("فَهِمَ", "فَهْمَ")
    assert vowels.agrees_with_typed("فَهِمَ", "فَهِمَ")
    assert vowels.agrees_with_typed("فهم", "فَهْمَ")  # bare letters say nothing


def after_doer(word, *, participle, verb_lemma="جاء", **feats):
    toks = [token(1, verb_lemma, verb_lemma, "VRB", 0, "---", **VERB),
            token(2, "الطالب", "طالب", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, word, word, "NOM", 1, "OBJ", stt="i", cas="a",
                  pattern="1ا2ِ3اً" if participle else "1ِ2ا3اً", **feats)]
    return roles([verb_lemma, "الطالب", word], toks)[2]


def test_indefinite_participle_after_a_verb_with_its_doer_is_hal_a_plain_noun_is_the_object():
    assert after_doer("راكبا", participle=True) == "حال"
    assert after_doer("كتابا", participle=False) == "مفعول به"


def test_tamyeez_al_nisba_follows_its_verbs_only():
    assert after_doer("هواء", participle=False, verb_lemma="طاب") == "تمييز"
    assert after_doer("هواء", participle=False, verb_lemma="أكل") == "مفعول به"


def test_past_passive_shape_is_read_from_the_vowels_alone():
    for word in ("قُرِئَ", "قُرِئَتِ", "سُئِلَ", "بُنِيَ", "أُكِلَ", "ضُرِبَ"):
        assert vowels.past_passive_shape(word)
    for word in ("كَتَبَ", "الْكِتَابُ", "قُرَيْشٌ", "كتب"):  # active, a noun, a name, bare
        assert not vowels.past_passive_shape(word)


def test_a_final_ta_is_the_verbs_only_when_it_is_not_a_plural_ending():
    for word in ("قُرِئَتْ", "كُتِبَتْ", "قُرِئَتِ"):
        assert vowels.past_passive_shape(word)
    for word in ("مُسْلِمَاتُ", "مُسْلِمَاتِ"):  # damma first, kasra inside, ends ت: a plural noun
        assert not vowels.past_passive_shape(word)


def test_a_present_passive_is_read_before_its_plural_or_dual_ending():
    for word in ("يُعَلَّمُونَ", "يُكْتَبْنَ", "يُكْتَبَانِ", "يُكْتَبُ"):
        assert vowels.typed_passive(word, present=True)
    for word in ("يُكَافِئُونَ", "يُكْرِمَانِ", "يُكْرِمُ"):  # active: no fatha before the last stem letter
        assert not vowels.typed_passive(word, present=True)


def test_a_word_the_morphology_calls_a_name_is_still_a_passive_verb_by_its_vowels():
    toks = [token(1, "NOAN", "قرئ", "PROP", 0, "---", pos_camel="noun_prop"),
            token(2, "الكتاب", "كتاب", "NOM", 1, "OBJ", stt="d", cas="n")]
    assert roles(["قُرِئَ", "الْكِتَابُ"], toks) == ["فعل", "نائب فاعل"]
