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
    assert walker.walk({"kind": "ism", "follows": "none"}) is None
