"""Step 6: the teacher turns a reading that breaks a book rule into a gap with a reason.

Every check is paired with the nearest reading that must be left alone, and the
last tests follow a gap all the way to the card and the picture.
"""
from backend.services import iraab, morphology
from backend.services.nahw_book import teacher_rules as config
from backend.services.syntax import naming, teacher, tree
from tests.test_naming import token

VERB = dict(vox="a", asp="p")


def review(words, toks):
    """What the route does: name the words, then let the teacher re-read them."""
    return teacher.review(words, toks, naming.roles(words, toks))


def gapped(found):
    return [bool(entry.get("gap")) for entry in found]


def test_every_check_has_a_switch_and_both_reasons():
    assert set(teacher.CHECKS) == set(config()["checks"])
    for rule in config()["checks"].values():
        assert rule["on"] in (True, False) and rule["ar"] and rule["en"]


def test_two_doers_for_one_verb_are_both_doubted_one_doer_and_an_object_are_not():
    verb = token(1, "أكل", "أكل", "VRB", 0, "---", **VERB)
    two = [verb, token(2, "الولد", "ولد", "NOM", 1, "SBJ", stt="d"),
           token(3, "الطالب", "طالب", "NOM", 1, "SBJ", stt="d")]
    # both typed with damma: two claims on one job
    assert gapped(review(["أَكَلَ", "الْوَلَدُ", "الطَّالِبُ"], two)) == [False, True, True]
    one_and_object = [verb, two[1], token(3, "الطعام", "طعام", "NOM", 1, "OBJ", stt="d")]
    assert gapped(review(["أَكَلَ", "الْوَلَدُ", "الطَّعَامَ"], one_and_object)) == [False, False, False]


def test_a_typed_vowel_that_does_not_fit_the_role_makes_a_gap_with_its_reason():
    toks = [token(1, "الولد", "ولد", "NOM", 0, "---", stt="d"),
            token(2, "مجتهد", "مجتهد", "NOM", 1, "PRD", stt="i")]
    clash = review(["الْوَلَدِ", "مُجْتَهِدٌ"], toks)  # a mubtada with a typed kasra
    assert clash[0]["role"] is None
    assert clash[0]["gap"] == {"ar": config()["checks"]["typed_case_fits_role"]["ar"],
                               "en": config()["checks"]["typed_case_fits_role"]["en"]}
    assert review(["الْوَلَدُ", "مُجْتَهِدٌ"], toks)[0]["role"] == "مبتدأ"


def test_a_diptote_or_a_sound_feminine_plural_is_not_a_clash():
    prep = token(1, "مر", "مر", "VRB", 0, "---", **VERB)
    diptote = [prep, token(2, "ب", "ب", "PRT", 1, "MOD"),
               token(3, "أحمد", "أحمد", "NOM", 2, "OBJ", stt="i")]
    assert review(["مَرَّ", "بِ", "أَحْمَدَ"], diptote)[2]["role"] == "مجرور"
    plural = [token(1, "رأى", "رأى", "VRB", 0, "---", **VERB),
              token(2, "المعلمات", "معلمة", "NOM", 1, "OBJ", stt="d", cas="a")]
    assert review(["رَأَى", "الْمُعَلِّمَاتِ"], plural)[1]["role"] == "مفعول به"


def test_la_before_a_typed_nominative_keeps_its_name():
    # لا رجلٌ في الدار: the لا works like ليس, so the noun is raf' and is not a clash
    toks = [token(1, "لا", "لا", "PRT", 0, "---"),
            token(2, "رجل", "رجل", "NOM", 1, "SBJ", stt="i")]
    assert review(["لَا", "رَجُلٌ"], toks)[1]["role"] == "اسم إن"


def found_of(*roles):
    return [{"role": role, "case": None} for role in roles]


def plain(n, **feats):
    return [token(i + 1, f"و{i}", f"و{i}", "NOM", 0, "---", **feats) for i in range(n)]


def test_a_khabar_needs_a_mubtada_anywhere_in_the_sentence():
    words = ["س", "ص"]
    toks = plain(2)
    assert teacher.review(words, toks, found_of(None, "خبر"))[1]["gap"]
    assert not teacher.review(words, toks, found_of("مبتدأ", "خبر"))[1].get("gap")


def test_an_ism_of_inna_needs_inna_before_it():
    words = ["س", "ص"]
    no_inna = plain(2)
    assert teacher.review(words, no_inna, found_of(None, "اسم إن"))[1]["gap"]
    with_inna = [token(1, "إن", "إن", "PRT", 0, "---"), token(2, "ص", "ص", "NOM", 1, "SBJ")]
    assert not teacher.review(words, with_inna, found_of("حرف", "اسم إن"))[1].get("gap")


def test_a_follower_needs_a_noun_before_it():
    words = ["س", "ص"]
    assert teacher.review(words, plain(2), found_of("معطوف", "مبتدأ"))[0]["gap"]
    assert not teacher.review(words, plain(2), found_of("مبتدأ", "معطوف"))[1].get("gap")


def test_a_tamyeez_needs_a_number_a_measure_or_a_verb_of_nisba():
    words = ["اشتريت", "عشرين", "كتابا"]

    def sentence(verb, number):
        return [token(1, verb, verb, "VRB", 0, "---", **VERB),
                token(2, number, number, "NOM", 1, "OBJ", stt="c"),
                token(3, "كتابا", "كتاب", "NOM", 2, "TMZ", stt="i", cas="a")]

    assert not review(words, sentence("اشتريت", "عشرون"))[2].get("gap")
    assert review(words, sentence("اشتريت", "مال"))[2]["gap"]  # no number: the book allows three names
    nisba = [token(1, "طاب", "طاب", "VRB", 0, "---", **VERB),
             token(2, "المكان", "مكان", "NOM", 1, "SBJ", stt="d", cas="n"),
             token(3, "هواء", "هواء", "NOM", 1, "TMZ", stt="i", cas="a")]
    assert review(["طاب", "المكان", "هواء"], nisba)[2]["role"] == "تمييز"


def test_a_gap_reaches_the_card_as_the_dash_and_the_reason():
    found = [{"role": None, "case": None, "gap": {"ar": "سبب", "en": "reason"}}]
    card = iraab.cards(morphology.analyze_sentence("الْوَلَدُ"), found)[0]
    assert (card["role"], card["role_key"], card["reason"], card["notes"]) == ("–", None, "سبب", "reason")
    assert card["sign"] is None and card["case"] is None


def test_a_gap_reaches_the_picture_as_a_dashed_leaf_with_the_reason_to_hover():
    toks = [token(1, "الولد", "ولد", "NOM", 0, "---", stt="d", cas="n"),
            token(2, "مجتهد", "مجتهد", "NOM", 1, "PRD", stt="i", cas="n")]
    words = ["الْوَلَدِ", "مُجْتَهِدٌ"]
    drawn = tree.build(words, toks, review(words, toks))
    leaf = next(child for child in drawn["tree"]["children"] if child["word"] == 0)
    assert leaf["gap"] and leaf["role"] is None
    assert leaf["detail"] == (f'{config()["checks"]["typed_case_fits_role"]["ar"]} · '
                              f'{config()["checks"]["typed_case_fits_role"]["en"]}')
    assert drawn["coverage"] < 1.0


def test_a_head_the_teacher_dashed_stays_a_dash_in_its_unit():
    toks = [token(1, "الولد", "ولد", "NOM", 0, "---", stt="d", cas="n"),
            token(2, "المدير", "مدير", "NOM", 1, "IDF", stt="d", cas="g")]
    words = ["الْوَلَدِ", "الْمُدِيرِ"]
    drawn = tree.build(words, toks, review(words, toks))
    head = next(child for child in drawn["tree"]["children"] if child["word"] == 0)
    assert head["gap"] and head["role"] is None


def test_every_role_the_teacher_names_is_a_role_naming_can_give():
    cases = config()["case_of_role"]
    assert {role for key, roles in cases.items() if not key.startswith("_") for role in roles} <= set(naming.ROLES)
