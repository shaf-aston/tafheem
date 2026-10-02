"""The `follows` axis: one sentence per follower (tabi'), and the words that only look like one."""
from backend.services.syntax import facts, walker
from backend.services.syntax.naming import roles as named
from tests.test_naming import VERB, clitic, token


def follows(words, toks, index):
    named(words, toks)  # carries the typed vowels onto the tokens
    bases = [t for t in toks if t.get("typed")]
    return facts.of(bases[index], toks)["follows"]


def test_naat():
    toks = [token(1, "الطبيب", "طبيب", "NOM", 0, "---", stt="d", cas="n"),
            token(2, "الماهر", "ماهر", "NOM", 1, "MOD", ud="ADJ", stt="d", cas="n")]
    assert follows(["الطَّبِيبُ", "الْمَاهِرُ"], toks, 1) == "naat"


def test_naat_of_a_pointer():
    toks = [token(1, "هذا", "هذا", "NOM", 2, "MOD", pos_camel="dem", cas="n"),
            token(2, "البستان", "بستان", "NOM", 0, "---", stt="d", cas="n")]
    assert follows(["هَذَا", "الْبُسْتَانُ"], toks, 1) == "naat"


def test_indefinite_after_definite_is_not_a_follower():
    toks = [token(1, "السماء", "سماء", "NOM", 0, "---", stt="d", cas="n"),
            token(2, "صافية", "صاف", "NOM", 1, "MOD", ud="ADJ", stt="i", cas="n")]
    assert follows(["السَّمَاءُ", "صَافِيَةٌ"], toks, 1) == "none"


def test_atf():
    toks = [token(1, "جاء", "جاء", "VRB", 0, "---", **VERB),
            token(2, "محمد", "محمد", "PROP", 1, "SBJ"),
            clitic(3, "و+", 2, "MOD"),
            token(4, "علي", "علي", "PROP", 3, "OBJ")]
    assert follows(["جَاءَ", "مُحَمَّدٌ", "وَعَلِيٌّ"], toks, 2) == "atf"


def test_tawkeed():
    toks = [token(1, "جاء", "جاء", "VRB", 0, "---", **VERB),
            token(2, "القوم", "قوم", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "كل", "كل", "NOM", 2, "MOD", stt="c", cas="n"),
            token(4, "+هم", "+هم", "NOM", 3, "IDF", pos_camel="pron", token_type="enc0")]
    assert follows(["جَاءَ", "الْقَوْمُ", "كُلُّهُمْ"], toks, 2) == "tawkeed"


def test_badal():
    toks = [token(1, "جاء", "جاء", "VRB", 0, "---", **VERB),
            token(2, "الخليفة", "خليفة", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "عمر", "عمر", "PROP", 2, "MOD")]
    assert follows(["جَاءَ", "الْخَلِيفَةُ", "عُمَرُ"], toks, 2) == "badal"


def test_a_subject_follows_nothing():
    toks = [token(1, "كتب", "كتب", "VRB", 0, "---", **VERB),
            token(2, "الطالب", "طالب", "NOM", 1, "SBJ", stt="d", cas="n")]
    assert follows(["كَتَبَ", "الطَّالِبُ"], toks, 1) == "none"


def test_each_follower_reaches_its_leaf():
    for answer, role in (("naat", "صفة"), ("atf", "معطوف"), ("tawkeed", "توكيد"), ("badal", "بدل")):
        assert walker.walk({"kind": "ism", "follows": answer})[0] == role
    assert walker.walk({"kind": "ism", "follows": "none", "governor": "verb"}) is None


def governor(words, toks, index):
    named(words, toks)
    bases = [t for t in toks if t.get("typed")]
    return facts.of(bases[index], toks)["governor"]


def test_governor_harf_jarr_and_its_leaf():
    toks = [token(1, "في", "في", "PRT", 0, "---"),
            token(2, "البيت", "بيت", "NOM", 1, "OBJ", stt="d", cas="g")]
    assert governor(["فِي", "الْبَيْتِ"], toks, 1) == "harf_jarr"
    assert walker.walk({"kind": "ism", "follows": "none", "governor": "harf_jarr"})[0] == "مجرور"


def test_governor_idafa_and_its_leaf():
    toks = [token(1, "كتاب", "كتاب", "NOM", 0, "---", stt="c"),
            token(2, "الطالب", "طالب", "NOM", 1, "IDF", stt="d", cas="g")]
    assert governor(["كِتَابُ", "الطَّالِبِ"], toks, 1) == "idafa"
    assert walker.walk({"kind": "ism", "follows": "none", "governor": "idafa"})[0] == "مضاف إليه"


def test_governor_idafa_by_kasra_straight_after_a_noun():
    toks = [token(1, "عبد", "عبد", "NOM", 0, "---", stt="c"),
            token(2, "الله", "الله", "PROP", 1, "---", cas="g")]
    assert governor(["عَبْدَ", "اللهِ"], toks, 1) == "idafa"


def test_governor_idafa_under_a_verb_is_the_verbs_argument():
    toks = [token(1, "كتب", "كتب", "VRB", 0, "---", **VERB),
            token(2, "الطالب", "طالب", "NOM", 1, "IDF", stt="d", cas="n")]
    assert governor(["كَتَبَ", "الطَّالِبُ"], toks, 1) == "verb"


def test_governor_nida_particle_head():
    toks = [token(1, "يا", "يا", "PRT", 0, "---"),
            token(2, "ولد", "ولد", "NOM", 1, "OBJ", cas="n")]
    assert governor(["يَا", "وَلَدُ"], toks, 1) == "nida"


def test_governor_istithna_particle_head_unless_negated():
    toks = [token(1, "إلا", "إلا", "PRT", 0, "---"),
            token(2, "زيدا", "زيد", "PROP", 1, "OBJ", cas="a")]
    assert governor(["إِلَّا", "زَيْدًا"], toks, 1) == "istithna"
    toks.insert(0, token(0, "ما", "ما", "PRT", 0, "---"))
    assert governor(["مَا", "إِلَّا", "زَيْدًا"], toks, 2) == "harf_jarr"


def test_governor_family_heads_and_none():
    for lemma, family in (("إن", "inna"), ("كان", "kana"), ("ظن", "zanna")):
        toks = [token(1, lemma, lemma, "VRB" if family != "inna" else "PRT", 0, "---", **VERB),
                token(2, "الولد", "ولد", "NOM", 1, "SBJ", stt="d", cas="n")]
        assert governor([lemma, "الْوَلَدُ"], toks, 1) == family
    toks = [token(1, "كاد", "كاد", "VRB", 0, "---", **VERB),
            token(2, "الولد", "ولد", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "يموت", "مات", "VRB", 1, "PRD", vox="a", asp="i")]
    assert governor(["كَادَ", "الْوَلَدُ", "يَمُوتُ"], toks, 1) == "kaada"
    toks = [token(1, "الولد", "ولد", "NOM", 0, "---", stt="d", cas="n")]
    assert governor(["الْوَلَدُ"], toks, 0) == "none"


def slot(words, toks, index):
    named(words, toks)
    bases = [t for t in toks if t.get("typed")]
    return facts.of(bases[index], toks)["slot"]


def test_slot_inna_subject_and_predicate():
    toks = [token(1, "إن", "إن", "PRT", 0, "---"),
            token(2, "الولد", "ولد", "NOM", 1, "SBJ", stt="d", cas="a"),
            token(3, "مجتهد", "مجتهد", "NOM", 1, "PRD", stt="i", cas="n")]
    assert slot(["إِنَّ", "الْوَلَدَ", "مُجْتَهِدٌ"], toks, 1) == "subject"
    assert slot(["إِنَّ", "الْوَلَدَ", "مُجْتَهِدٌ"], toks, 2) == "predicate"


def test_slot_inna_fronted_jar_makes_the_noun_the_subject():
    toks = [token(1, "إن", "إن", "PRT", 0, "---"),
            token(2, "في", "في", "PRT", 1, "PRD"),
            token(3, "رجلا", "رجل", "NOM", 1, "PRD", stt="i", cas="a")]
    assert slot(["إِنَّ", "فِي", "رَجُلًا"], toks, 2) == "subject"


def test_slot_kana_subject_and_predicate():
    toks = [token(1, "كان", "كان", "VRB", 0, "---", **VERB),
            token(2, "الولد", "ولد", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "مجتهدا", "مجتهد", "NOM", 1, "PRD", stt="i", cas="a")]
    assert slot(["كَانَ", "الْوَلَدُ", "مُجْتَهِدًا"], toks, 1) == "subject"
    assert slot(["كَانَ", "الْوَلَدُ", "مُجْتَهِدًا"], toks, 2) == "predicate"


def test_slot_a_verb_that_finishes_kaada_stays_a_verb():
    toks = [token(1, "كاد", "كاد", "VRB", 0, "---", **VERB),
            token(2, "الولد", "ولد", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "يموت", "مات", "VRB", 1, "PRD", vox="a", asp="i")]
    assert slot(["كَادَ", "الْوَلَدُ", "يَمُوتُ"], toks, 1) == "subject"
    assert slot(["كَادَ", "الْوَلَدُ", "يَمُوتُ"], toks, 2) == "none"


def test_slot_zanna_subject_object_second_object():
    toks = [token(1, "ظن", "ظن", "VRB", 0, "---", **VERB),
            token(2, "الولد", "ولد", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "الأمر", "أمر", "NOM", 1, "OBJ", stt="d", cas="a"),
            token(4, "سهلا", "سهل", "NOM", 1, "OBJ", stt="i", cas="a")]
    words = ["ظَنَّ", "الْوَلَدُ", "الْأَمْرَ", "سَهْلًا"]
    assert [slot(words, toks, i) for i in (1, 2, 3)] == ["subject", "object", "second_object"]


def test_slot_none_under_a_plain_verb():
    toks = [token(1, "كتب", "كتب", "VRB", 0, "---", **VERB),
            token(2, "الطالب", "طالب", "NOM", 1, "SBJ", stt="d", cas="n")]
    assert slot(["كَتَبَ", "الطَّالِبُ"], toks, 1) == "none"


def test_each_family_slot_reaches_its_leaf():
    base = {"kind": "ism", "follows": "none"}
    for governor, slot_answer, role in (
            ("inna", "subject", "اسم إن"), ("inna", "predicate", "خبر إن"),
            ("kana", "subject", "اسم كان"), ("kana", "predicate", "خبر كان"),
            ("kaada", "subject", "اسم كاد"), ("zanna", "subject", "فاعل"),
            ("zanna", "object", "مفعول به"), ("zanna", "second_object", "مفعول به"),
            ("nida", "none", "منادى"), ("istithna", "none", "مستثنى")):
        assert walker.walk({**base, "governor": governor, "slot": slot_answer})[0] == role
    for governor in ("verb", "none"):
        assert walker.walk({**base, "governor": governor, "slot": "none"}) is None
    assert walker.walk({**base, "governor": "kaada", "slot": "predicate"}) is None
