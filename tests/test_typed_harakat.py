"""Step 5: the vowel the reader typed is evidence the parser may not overrule.

Each test pairs the case that fires with the nearest one that must not, since
the parser is fed letters only and the same links come back for both.
"""
import pytest

from backend.services import harakat
from backend.services.syntax import naming, tree
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
    assert harakat.vowel_agreement("فَهِمَ", "فَهْمَ") is None
    assert harakat.vowel_agreement("فَهِمَ", "فَهِمَ") == (3, 0)
    assert harakat.vowel_agreement("فهم", "فَهْمَ") == (0, 0)  # bare letters say nothing
    # a full reading beats a bare one the reader's vowels cannot contradict
    assert harakat.best_reading("إِنَّكَ", [{"diac": "انك"}, {"diac": "إِنَّكَ"}]) == {"diac": "إِنَّكَ"}
    # the dagger alef is the fatha typed: لٰكِنْ keeps its rank over a stray لَ+كِن
    assert harakat.best_reading("لَكِنْ", [{"diac": "لٰكِن"}, {"diac": "لَكِن"}]) == {"diac": "لٰكِن"}
    # a doubling the reader did not type on a voweled letter counts against: أَبُوْهُ, not أَبُّوهُ
    assert harakat.best_reading("أَبُوْهُ", [{"diac": "أَبُوه"}, {"diac": "أَبُّوهُ"}]) == {"diac": "أَبُوه"}
    assert harakat.best_reading("أَبُوْهُ", [{"diac": "أَبُّوهُ"}, {"diac": "أَبُوه"}]) == {"diac": "أَبُوه"}  # whatever the order
    assert harakat.vowel_agreement("أَبُوْهُ", "أَبُّوهُ") is not None  # a dropped shadda is no contradiction


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
        assert harakat.past_passive_shape(word)
    for word in ("كَتَبَ", "الْكِتَابُ", "قُرَيْشٌ", "كتب"):  # active, a noun, a name, bare
        assert not harakat.past_passive_shape(word)


def test_a_final_ta_is_the_verbs_only_when_it_is_not_a_plural_ending():
    for word in ("قُرِئَتْ", "كُتِبَتْ", "قُرِئَتِ"):
        assert harakat.past_passive_shape(word)
    for word in ("مُسْلِمَاتُ", "مُسْلِمَاتِ"):  # damma first, kasra inside, ends ت: a plural noun
        assert not harakat.past_passive_shape(word)


def test_a_present_passive_is_read_before_its_plural_or_dual_ending():
    for word in ("يُعَلَّمُونَ", "يُكْتَبْنَ", "يُكْتَبَانِ", "يُكْتَبُ"):
        assert harakat.typed_passive(word, present=True)
    for word in ("يُكَافِئُونَ", "يُكْرِمَانِ", "يُكْرِمُ"):  # active: no fatha before the last stem letter
        assert not harakat.typed_passive(word, present=True)


def test_a_word_the_morphology_calls_a_name_is_still_a_passive_verb_by_its_vowels():
    toks = [token(1, "NOAN", "قرئ", "PROP", 0, "---", pos_camel="noun_prop"),
            token(2, "الكتاب", "كتاب", "NOM", 1, "OBJ", stt="d", cas="n")]
    assert roles(["قُرِئَ", "الْكِتَابُ"], toks) == ["فعل", "نائب فاعل"]


@pytest.mark.parametrize("word, command", [
    ("اُكْتُبْ", True), ("اِجْلِسْ", True), ("قُمْ", True), ("بِعْ", True),
    ("أَكْتُبُ", False), ("يَكْتُبْ", False), ("كَتَبَ", False), ("اكتب", False), ("قم", False)])
def test_command_shape(word: str, command: bool):
    assert harakat.command_shape(word) is command


def test_a_hollow_form_iv_command_needs_the_root_to_say_so():
    assert harakat.command_shape("أَقِمْ", hollow=True)
    assert not harakat.command_shape("أَقِمْ")                      # أَمِنْ, أَحْمَدْ: no hollow root, no command
    assert not harakat.command_shape("أَقِمْ", after_jazm=True, hollow=True)  # لم أَقِمْ is a present verb


def test_a_kasra_before_hamzat_al_wasl_is_the_paused_sukun():
    assert harakat.paused("أَقِمِ", "الصَّلَاةَ") == "أَقِمْ"
    assert harakat.paused("اُكْتُبِ", "ٱلدَّرْسَ") == "اُكْتُبْ"  # the Qur'an's own alef of wasl
    assert harakat.paused("أَقِمِ") == "أَقِمِ"                  # said alone, the kasra stays
    assert harakat.paused("الْبَيْتِ", "إِلَى") == "الْبَيْتِ"     # hamzat al-qat' moves nothing


def test_a_command_moved_to_kasra_is_still_built_on_the_sukun():
    toks = [token(1, "اكتب", "كتب", "VRB", 0, "---", vox="a", asp="i"),
            token(2, "الدرس", "درس", "NOM", 1, "OBJ", stt="d", cas="a")]
    found = naming.roles(["اُكْتُبِ", "الدَّرْسَ"], toks)
    assert [w["role"] for w in found] == ["فعل", "مفعول به"]
    assert found[0]["case"] == "mabni" and found[0]["aspect"] == "c"


@pytest.mark.parametrize("word, command", [
    ("اُكْتُبُوا", True), ("اعْبُدُوا", True), ("اِسْتَخْرِجُوا", True),  # its vowel on hamzat al-wasl may be left untyped
    ("اِجْتَمَعُوا", False), ("اِنْكَسَرُوا", False),                       # the past of a longer form: fatha in the middle
    ("كَتَبُوا", False), ("يَكْتُبُوا", False)])
def test_a_command_to_many_is_read_by_its_waw(word: str, command: bool):
    assert harakat.command_shape(word) is command


def test_the_light_lakin_joins_and_the_shadda_one_is_the_inna_sister():
    from backend.services.syntax.facts import is_light
    assert is_light({"typed": "لَكِنْ"})
    assert not is_light({"typed": "لَكِنَّ"})
    assert not is_light({"typed": "لكن"})  # untyped: the sentence decides


def test_the_six_nouns_show_their_case_by_a_letter():
    from backend.services.syntax.facts import typed_case_of
    six = lambda typed, lemma="أب", stuck_on=0: typed_case_of({"typed": typed, "lemma": lemma, "stuck_on": stuck_on})
    assert six("أَبَاهُ", stuck_on=1) == "a"
    assert six("أَخُوْ", "أخ") == "u"
    assert six("أَخِيْ", "أخ") == "i"
    assert six("أبو") == "u"                      # the letter is typed even when no vowel is
    assert six("أَبِي", stuck_on=1) is None       # the ya of the speaker: the case is unseen
    assert six("عَصَا", "عصا") is None            # a long alef on any other noun is no case


def test_a_word_before_its_noun_is_no_sifa():
    # هَذَانِ قَلَمَانِ, the pointer hung on the noun after it
    toks = [token(1, "هذان", "هذا", "NOM", 2, "MOD", pos_camel="pron_dem"),
            token(2, "قلمان", "قلم", "NOM", 0, "---")]
    assert roles(["هَذَانِ", "قَلَمَانِ"], toks) == ["مبتدأ", "خبر"]


def test_a_noun_sharing_a_verbs_lemma_governs_nothing():
    from backend.services.syntax.facts import Sentence
    noun = token(2, "علم", "علم", "NOM", 1, "MOD", stt="c")
    verb = token(1, "علمت", "علم", "VRB", 0, "---", **VERB)
    s = Sentence([verb, noun])
    assert s.family(verb) == "zanna"
    assert s.family(noun) is None


def test_a_noun_with_its_own_pronoun_after_a_definite_noun_is_its_badal():
    # نَفَعَنِي الْمُعَلِّمُ عِلْمُهُ, the pronoun drawn as an object of the noun
    toks = [token(1, "نفع", "نفع", "VRB", 0, "---", **VERB),
            token(2, "+ني", "+ني", "NOM", 1, "OBJ", pos_camel="pron", stt="d", cas="a"),
            token(3, "المعلم", "معلم", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(4, "علم", "علم", "NOM", 3, "MOD", stt="c", cas="n"),
            token(5, "+ه", "+ه", "NOM", 4, "OBJ", pos_camel="pron", stt="d", cas="g")]
    assert roles(["نَفَعَنِي", "الْمُعَلِّمُ", "عِلْمُهُ"], toks)[2] == "بدل"
    # the nearest that is not: an object in another case keeps its own job
    toks[3]["cas"], toks[2]["rel"] = "a", "SBJ"
    assert roles(["نَفَعَنِي", "الْمُعَلِّمُ", "عِلْمَهُ"], toks)[2] != "بدل"


def test_ma_after_a_verb_with_no_object_is_that_object():
    # قَرَأْتُ مَا كَتَبْتُهُ: the relative ما; مَا رَأَيْتُهُ (nothing before it) negates
    def ma(words, before):
        toks = ([token(1, "قرأت", "قرأ", "VRB", 0, "---", **VERB)] if before else []) + [
            token(len(words) - 1, "ما", "ما", "NOM", 0 if not before else 1, "OBJ" if before else "---", pos_camel="pron_rel"),
            token(len(words), "كتبت", "كتب", "VRB", len(words) - 1, "MOD", **VERB),
            token(len(words) + 1, "+ه", "+ه", "NOM", len(words), "OBJ", pos_camel="pron", stt="d")]
        return roles(words, toks)[-2]
    assert ma(["قَرَأْتُ", "مَا", "كَتَبْتُهُ"], True) != "حرف"
    assert ma(["مَا", "كَتَبْتُهُ"], False) == "حرف"


def test_after_a_pointer_the_noun_carrying_a_verb_is_no_mubtada():
    # هَذَا رَجُلٌ يَعْمَلُ: the verb is the صفة's clause, the noun not the sentence's mubtada
    toks = [token(1, "هذا", "هذا", "NOM", 2, "MOD", pos_camel="pron_dem"),
            token(2, "رجل", "رجل", "NOM", 0, "---", stt="i", cas="n"),
            token(3, "يعمل", "عمل", "VRB", 2, "MOD", vox="a", asp="i")]
    assert roles(["هَذَا", "رَجُلٌ", "يَعْمَلُ"], toks)[1] != "مبتدأ"


def test_after_illa_in_a_negated_sentence_the_noun_in_its_case_is_the_badal():
    # مَا جَاءَ أَحَدٌ إِلَّا زَيْدٌ, as one parser draws it: زيد under إلا, which is no preposition
    toks = [token(1, "ما", "ما", "PRT", 2, "MOD", pos_camel="part_neg"),
            token(2, "جاء", "جاء", "VRB", 0, "---", **VERB),
            token(3, "أحد", "أحد", "NOM", 2, "SBJ", cas="n"),
            token(4, "إلا", "إلا", "PRT", 2, "MOD", pos_camel="part"),
            token(5, "زيد", "زيد", "PROP", 4, "OBJ", pos_camel="noun_prop")]
    named = roles(["مَا", "جَاءَ", "أَحَدٌ", "إِلَّا", "زَيْدٌ"], toks)
    assert named[3] != "حرف جر" and named[4] == "بدل"


def test_a_dual_describes_only_a_dual():
    # مُحَمَّدٌ وَعَلِيٌّ مُجْتَهِدَانِ, drawn with the dual under محمد: it is the khabar, not his صفة
    toks = [token(1, "محمد", "محمد", "PROP", 0, "---", pos_camel="noun_prop", num="s"),
            token(2, "و+", "و+", "PRT", 1, "MOD", pos_camel="conj", token_type="prc2"),
            token(3, "علي", "علي", "NOM", 2, "OBJ", cas="n", num="s"),
            token(4, "مجتهدان", "مجتهد", "NOM", 1, "MOD", cas="n", num="d")]
    assert roles(["مُحَمَّدٌ", "وَعَلِيٌّ", "مُجْتَهِدَانِ"], toks) == ["مبتدأ", "معطوف", "خبر"]
