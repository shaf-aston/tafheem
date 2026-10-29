"""A verb, its doer and its object when the case does not show: a مضاف typed bare with no
sentence (أكل الطعام), a noun the parser added to a verb (شرب الماء), a name and a noun after
it (شرب زيد الماء), and a name a verb of saying took as its object (لِأَبِيهِ آزَرَ)."""
import pytest

from backend.services.nahw.syntax.facts import agrees, shown_cases
from backend.services.nahw.syntax.repair.subject_clash import added_to_verb, doer_first, name_told_to
from tests.nahw.test_naming import VERB, token
from tests.nahw_helpers import cards, needs_parser


def roles(sentence: str) -> list[str]:
    return [c["role"] for c in cards(sentence)]


@needs_parser
@pytest.mark.parametrize("sentence, said", [
    ("شرب الماء", ["فعل", "فاعل"]),  # the doer comes straight after its verb
    ("أكل الطعام", ["فعل", "فاعل"]),
    ("نبح الكلب في الظلام", ["فعل", "فاعل", "حرف جر", "مجرور"]),
    ("أَكَلَ الطَّعَامَ", ["فعل", "مفعول به"]),  # typed in nasb
    ("شربتُ الماء", ["فعل", "مفعول به"]),  # the verb holds its doer
    ("صُمْتُ يَوْمَ الْخَمِيسِ", ["فعل", "مفعول فيه", "مضاف إليه"]),  # a time word is the مفعول فيه
    ("جَاءَ يَوْمُ الْخَمِيسِ", ["فعل", "فاعل", "مضاف إليه"]),  # unless its damma makes it the doer
    ("شرب زيد الماء", ["فعل", "فاعل", "مفعول به"]),
    ("شرب زيد الماء باردا", ["فعل", "فاعل", "مفعول به", "حال"]),
    ("رأى زيد عمرو", ["فعل", "فاعل", "مفعول به"]),
    ("أكرم محمد زيدا", ["فعل", "فاعل", "مفعول به"]),
    ("أَكْرَمَ مُحَمَّدٌ زَيْدًا", ["فعل", "فاعل", "مفعول به"]),  # the doer may show its raf'
    ("أكرم محمد حامدا", ["فعل", "فاعل", "مفعول به"]),  # a name on a participle's measure is no hal
    ("جاء زيد راكبا", ["فعل", "فاعل", "حال"]),
    ("أقبل زيد مسرعا", ["فعل", "فاعل", "حال"]),  # an unknown word filed as a name keeps a hal's shape
])
def test_with_no_case_shown_the_verb_takes_its_doer_then_its_object(sentence, said):
    assert roles(sentence) == said


@needs_parser
@pytest.mark.parametrize("sentence", ["عبد الله", "كتاب الله", "أَكْلُ الطَّعَامِ"])
def test_a_construct_that_is_a_name_or_typed_a_noun_stays_a_noun(sentence):
    assert roles(sentence)[0] != "فعل"


@needs_parser
@pytest.mark.parametrize("sentence", ["جاء زيد الكريم", "رأى زيد الحسن"])
def test_a_name_with_al_showing_no_case_may_describe_and_is_no_object(sentence):
    assert roles(sentence)[-1] != "مفعول به"


@needs_parser
def test_a_name_after_a_noun_in_jarr_that_a_verb_of_saying_holds_is_its_badal():
    azar = cards("قَالَ إِبْرَاهِيمُ لِأَبِيهِ آزَرَ")[-1]
    assert (azar["role"], azar["case"]) == ("بدل", "jarr")


@needs_parser
@pytest.mark.parametrize("sentence", ["قال إبراهيم لأبيه آزر", "قال زيد لأخيه عمرو"])
def test_a_name_typed_bare_after_a_noun_in_jarr_that_a_verb_of_saying_holds_is_its_badal(sentence):
    assert cards(sentence)[-1]["role"] == "بدل"


@needs_parser
@pytest.mark.parametrize("name", ["آزَرَ", "إِبْرَاهِيمَ"])
def test_the_khabar_of_kana_is_no_badal_of_the_noun_before_it(name):
    assert cards(f"كَانَ اسْمُ هذا الرَجُلِ {name}")[-1]["role"] == "خبر كان"


@pytest.mark.parametrize("noun, verb, rel", [
    ({}, {}, "SBJ"),  # no case shows: the doer, straight after its verb
    ({"typed": "الْمَاءَ"}, {}, "OBJ"),  # typed in nasb
    ({}, {"per": "1"}, "OBJ"),  # شربتُ holds its doer
    ({"typed": "الْمَاءِ"}, {}, "IDF"),  # typed in jarr: left as read
])
def test_a_noun_hung_on_a_verb_as_its_mudaf_ilayh_is_its_doer_or_object(noun, verb, rel):
    toks = [token(1, "شرب", "شرب", "VRB", 0, "---", **{**VERB, **verb}), token(2, "الماء", "ماء", "NOM", 1, "IDF", **noun)]
    added_to_verb(toks)
    assert toks[1]["rel"] == rel


def test_a_noun_hung_on_a_verb_that_has_a_doer_is_its_object():
    toks = [token(1, "شرب", "شرب", "VRB", 0, "---", **VERB), token(2, "زيد", "زيد", "PROP", 1, "SBJ"),
            token(3, "الماء", "ماء", "NOM", 1, "IDF")]
    added_to_verb(toks)
    assert toks[2]["rel"] == "OBJ"


def test_a_mudaf_ilayh_on_a_noun_stays():
    toks = [token(1, "كتاب", "كتاب", "NOM", 0, "---"), token(2, "الله", "الله", "PROP", 1, "IDF")]
    added_to_verb(toks)
    assert toks[1]["rel"] == "IDF"


def name_then_noun(second: dict, first: str = "زيد", **verb) -> list[dict]:
    return [token(1, "شرب", "شرب", "VRB", 0, "---", **{**VERB, "per": "3", **verb}),
            token(2, "زيد", "زيد", "PROP", 1, "OBJ", pos_camel="noun_prop", typed=first), {"id": 3, "head": 2, **second}]


@pytest.mark.parametrize("second", [
    token(3, "الماء", "ماء", "NOM", 2, "---", cas="a", stt="d"),  # in nasb, as the parser reads it
    token(3, "الماء", "ماء", "NOM", 2, "OBJ", cas="a", stt="d"),  # a name takes no object
    token(3, "عمرو", "عمرو", "PROP", 2, "---", pos_camel="noun_prop"),  # a second bare name
])
def test_after_a_bare_name_the_word_its_case_lets_be_no_follower_is_the_verbs_object(second):
    toks = name_then_noun(second)
    doer_first(toks)
    assert (toks[1]["rel"], toks[2]["head"], toks[2]["rel"]) == ("SBJ", 1, "OBJ")


def test_after_a_name_showing_raf_a_word_in_nasb_is_the_verbs_object():
    toks = name_then_noun(token(3, "عمرا", "عمرو", "PROP", 2, "---", cas="a", pos_camel="noun_prop"), "زَيْدٌ")
    doer_first(toks)
    assert (toks[1]["rel"], toks[2]["head"], toks[2]["rel"]) == ("SBJ", 1, "OBJ")


@pytest.mark.parametrize("second, verb", [
    (token(3, "الماء", "ماء", "NOM", 2, "---", cas="a", stt="d"), {"per": "1"}),  # شربتُ holds its doer
    (token(3, "عمرو", "عمرو", "PROP", 2, "---", pos_camel="noun_prop"), {"first": "زَيْدٌ"}),  # after raf' a bare name may be its بدل
    (token(3, "زيد", "زيد", "PROP", 2, "---", pos_camel="noun_prop"), {"first": "زَيْدًا"}),  # the first in nasb is no doer
    (token(3, "الماء", "ماء", "NOM", 2, "---", cas="u", stt="d"), {}),  # raf' may follow the name
    (token(3, "الحسن", "حسن", "PROP", 2, "---", pos_camel="noun_prop", stt="d"), {}),  # ال: may describe
])
def test_a_word_that_may_follow_the_name_or_a_verb_with_its_own_doer_is_left(second, verb):
    toks = name_then_noun(second, **verb)
    doer_first(toks)
    assert (toks[1]["rel"], toks[2]["head"]) == ("OBJ", 2)


def told_to(name: dict, verb: str = "قال", before_case: str = "g") -> list[dict]:
    return [token(1, verb, verb, "VRB", 0, "---", **VERB), token(2, "ل", "ل", "PRT", 1, "MOD"),
            token(3, "صديق", "صديق", "NOM", 2, "OBJ", cas=before_case, pos_camel="noun"), {"id": 4, "head": 1, **name}]


def test_a_name_a_verb_of_saying_took_after_a_noun_in_jarr_follows_that_noun():
    toks = told_to(token(4, "آزر", "آزر", "PROP", 1, "OBJ", cas="g", pos_camel="noun_prop"))
    name_told_to(toks)
    assert (toks[3]["head"], toks[3]["rel"]) == (3, "MOD")


@pytest.mark.parametrize("name, verb, before_case", [
    (token(4, "آزر", "آزر", "PROP", 1, "OBJ", cas="g", pos_camel="noun_prop"), "ضرب", "g"),  # any other verb takes a name
    (token(4, "آزر", "آزر", "PROP", 1, "OBJ", cas="g", pos_camel="noun_prop"), "قال", "u"),  # no jarr to wear
    (token(4, "زيد", "زيد", "PROP", 1, "OBJ", cas="a", pos_camel="noun_prop"), "قال", "g"),  # nasb only
    (token(4, "كلام", "كلام", "NOM", 1, "OBJ", cas="g"), "قال", "g"),  # a word of speech is said
])
def test_a_name_any_other_verb_holds_or_that_cannot_wear_jarr_stays(name, verb, before_case):
    toks = told_to(name, verb, before_case)
    name_told_to(toks)
    assert (toks[3]["head"], toks[3]["rel"]) == (1, "OBJ")


def test_a_diptotes_typed_fatha_can_mean_jarr_and_a_plain_names_cannot():
    azar = token(1, "آزر", "آزر", "PROP", 0, "---", typed="آزَرَ", pos_camel="noun_prop")
    zayd = token(1, "زيد", "زيد", "PROP", 0, "---", typed="زَيْدًا", pos_camel="noun_prop")
    assert "i" in shown_cases(azar) and "i" not in shown_cases(zayd)


def test_a_noun_no_vowel_nor_reading_gave_a_case_may_wear_any():
    bare = token(1, "آزر", "آزر", "PROP", 0, "---", typed="آزر", cas="na", pos_camel="noun_prop")
    read = token(1, "زيد", "زيد", "PROP", 0, "---", typed="زيد", cas="n", pos_camel="noun_prop")
    verb = token(1, "آزر", "آزر", "VRB", 0, "---", typed="آزر", cas="na", pos_camel="verb")
    assert shown_cases(bare) == {"u", "a", "i"} and shown_cases(read) == {"u"} and not shown_cases(verb)


def test_a_word_showing_tanween_never_describes_a_name_whatever_its_tag():
    name = token(1, "زيد", "زيد", "PROP", 0, "---", typed="زيد", cas="u", stt="i", pos_camel="noun_prop")
    man = token(1, "رجل", "رجل", "NOM", 0, "---", typed="رجل", cas="u", stt="i", pos_camel="noun")
    cold = token(2, "بارد", "بارد", "NOM", 1, "MOD", typed="بَارِدٌ", cas="n", stt="i", pos_camel="adj")
    lord = token(2, "رب", "رب", "NOM", 1, "MOD", typed="رَبِّ", cas="g", stt="i", pos_camel="noun")
    allah = {**name, "typed": "لِلَّهِ", "cas": "g"}  # رَبِّ shows no tanween: nothing says it is indefinite
    assert not agrees(cold, {**name, "typed": "زَيْدٌ"}) and agrees(cold, {**man, "typed": "رَجُلٌ"}) and agrees(lord, allah)
