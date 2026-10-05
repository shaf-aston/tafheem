"""The bracket picture for a typed sentence, built from the parser's links."""
from backend.services.nahw_book import role_units
from backend.services.syntax import naming, tree
from backend.services.nahw_book import term_ar
from tests.test_naming import token


def built(words, toks):
    return tree.build(words, toks, naming.roles(words, toks))


def roles_in(node):
    """Every role in the tree, outermost first."""
    found = [node.get("role")] if node.get("role") else []
    for child in node.get("children", []):
        found += roles_in(child)
    return found


def test_verb_sentence_is_one_bracket():
    toks = [token(1, "كتب", "كتب", "VRB", 0, "---", vox="a", asp="p"),
            token(2, "الطالب", "طالب", "NOM", 1, "SBJ", stt="d", cas="n"),
            token(3, "رسالة", "رسالة", "NOM", 1, "OBJ", cas="a")]
    drawn = built(["كَتَبَ", "الطَّالِبُ", "رِسَالَةً"], toks)
    assert drawn["coverage"] == 1.0
    assert drawn["tree"]["label"] == tree.VERBAL
    assert [child["word"] for child in drawn["tree"]["children"]] == [0, 1, 2]
    assert roles_in(drawn["tree"]) == ["فعل", "فاعل", "مفعول به"]
    assert drawn["tree"]["children"][0]["tone"] == "fil"


def test_idafa_is_a_unit_that_plays_one_role():
    toks = [token(1, "كتاب", "كتاب", "NOM", 0, "---", stt="c", cas="n"),
            token(2, "الطالب", "طالب", "NOM", 1, "IDF", stt="d", cas="g"),
            token(3, "جديد", "جديد", "NOM", 1, "MOD", ud="ADJ", cas="n")]
    drawn = built(["كِتَابُ", "الطَّالِبِ", "جَدِيدٌ"], toks)
    unit = drawn["tree"]
    assert unit["label"] == term_ar("murakkab_idafi")  # what it is
    assert [child.get("role") for child in unit["children"]] == ["مضاف", "مضاف إليه", "خبر"]


def test_a_word_no_rule_could_name_is_a_gap_not_a_guess():
    # a word with no case anywhere, hung off the verb by a link that names nothing
    toks = [token(1, "ذهب", "ذهب", "VRB", 0, "---", asp="p"),
            token(2, "أمس", "أمس", "NOM", 1, "MOD", cas="u")]
    drawn = built(["ذَهَبَ", "أَمْسِ"], toks)
    gaps = [child for child in drawn["tree"]["children"] if child.get("gap")]
    assert [leaf["role"] for leaf in gaps] == [None]
    assert drawn["coverage"] == 0.5


def test_two_words_pointing_at_each_other_still_draw():
    # the parser does this on a short nominal sentence; it must not loop forever
    toks = [token(1, "السماء", "سماء", "NOM", 2, "SBJ", stt="d", cas="n"),
            token(2, "صافية", "صاف", "NOM", 1, "MOD", ud="ADJ", cas="n")]
    drawn = built(["السَّمَاءُ", "صَافِيَةٌ"], toks)
    assert [child["word"] for child in drawn["tree"]["children"]] == [0, 1]


def test_nothing_is_drawn_when_the_words_do_not_line_up():
    toks = [token(1, "كتب", "كتب", "VRB", 0, "---")]
    drawn = tree.build(["كَتَبَ", "زَيْدٌ"], toks, [{"role": None, "case": None}] * 2)
    assert drawn["coverage"] == 0.0 and not tree.is_drawable(drawn)


def test_a_jar_majroor_is_not_given_the_job_harf():
    # مَا فِي الْقُبُورِ: the unit was drawn as a حرف; the parser names no job for it
    toks = [token(1, "ما", "ما", "NOM", 0, "---", pos_camel="pron_rel"),
            token(2, "في", "في", "PRT", 1, "MOD", pos_camel="prep"),
            token(3, "القبور", "قبر", "NOM", 2, "OBJ", stt="d", cas="g")]
    drawn = built(["مَا", "فِي", "الْقُبُورِ"], toks)
    unit = next(child for child in drawn["tree"]["children"] if child.get("children"))
    assert unit["label"] == term_ar("jar_majroor")
    assert unit["role"] is None
    assert [child["role"] for child in unit["children"]] == ["حرف جر", "مجرور"]


def test_the_labels_are_the_shared_terms():
    assert tree.VERBAL == term_ar("jumlah_filiyyah")
    assert {tree._label({"pos": "NOM"}, [unit["child"]]) for unit in role_units() if not unit.get("on_particle")}         == {term_ar(unit["label"]) for unit in role_units() if not unit.get("on_particle")}


def test_a_word_hung_on_an_attached_particle_is_drawn_under_what_the_particle_joins():
    toks = [token(1, "جاء", "جاء", "VRB", 0, "---", vox="a", asp="p"),
            token(2, "محمد", "محمد", "PROP", 1, "SBJ"),
            token(3, "و+", "و+", "PRT", 2, "MOD", token_type="prc2", pos_camel="conj"),
            token(4, "علي", "علي", "PROP", 3, "OBJ")]
    drawn = built(["جَاءَ", "مُحَمَّدٌ", "وَعَلِيٌّ"], toks)
    # the وَ is a word of its own, in its own column, joining عليّ to محمد
    assert drawn["words"] == ["جَاءَ", "مُحَمَّدٌ", "وَ", "عَلِيٌّ"]
    joined = drawn["tree"]["children"][1]  # the noun with its معطوف inside, not a second root
    assert joined["children"][0]["word"] == 1
    assert roles_in(drawn["tree"]) == ["فعل", "فاعل", "فاعل", "حرف عطف", "معطوف"]  # the unit plays the faa'il


def test_a_verb_clause_hung_on_a_mubtada_is_its_khabar_in_the_place_of_raf():
    # الولدُ يكتبُ: the clause is the khabar, and a clause stands in a place, never in a case
    toks = [token(1, "الولد", "ولد", "NOM", 0, "SBJ", stt="d", cas="n"),
            token(2, "يكتب", "كتب", "VRB", 1, "MOD", vox="a", asp="i")]
    drawn = built(["الْوَلَدُ", "يَكْتُبُ"], toks)
    clause = drawn["tree"]["children"][1]
    assert (clause["role"], clause["detail"]) == ("خبر", "في محل رفع")
    assert [leaf["role"] for leaf in clause["children"]] == ["فعل"]


def test_a_nominal_sentence_as_khabar_is_drawn_as_a_sentence_in_place_of_raf():
    # زيدٌ أبوه عالمٌ, as the book links write it
    toks = [token(1, "زيد", "زيد", "PROP", 0, "---", pos_camel="noun_prop"),
            token(2, "أبو", "أب", "NOM", 4, "SBJ", stt="c", cas="n", pos_camel="noun"),
            token(3, "+ه", "+ه", "NOM", 2, "IDF", stt="d", cas="g", pos_camel="pron"),
            token(4, "عالم", "عالم", "NOM", 1, "PRD", stt="i", cas="n", pos_camel="noun")]
    drawn = built(["زَيْدٌ", "أَبُوْهُ", "عَالِمٌ"], toks)["tree"]
    khabar = drawn["children"][1]
    assert khabar["role"] == "خبر" and khabar["label"] == "جُمْلَةٌ اِسْمِيَّةٌ" and khabar["detail"]
    assert [kid["role"] for kid in khabar["children"]] == ["مبتدأ", "خبر"]


def test_a_verb_beside_the_ism_under_its_governor_is_the_khabar_clause():
    # كانَ الولدُ يكتبُ: the verb is the khabar (PRD) of كان, its clause in place of nasb
    toks = [token(1, "كان", "كان", "VRB", 0, "---", vox="a", asp="p", pos_camel="verb"),
            token(2, "الولد", "ولد", "NOM", 1, "SBJ", stt="d", cas="n", pos_camel="noun"),
            token(3, "يكتب", "كتب", "VRB", 1, "PRD", vox="a", asp="i", pos_camel="verb")]
    drawn = built(["كَانَ", "الْوَلَدُ", "يَكْتُبُ"], toks)["tree"]
    clause = drawn["children"][2]
    assert clause["role"] == "خبر كان" and clause["detail"]


def test_a_condition_draws_particle_condition_and_answer_side_by_side_with_the_masdar_inside():
    # إنْ تُرِدْ أنْ تنجحَ تدرسْ: the parser hangs the particle on the answer; the books draw
    # the particle, فعل الشرط and جواب الشرط apart, and أنْ with its verb as one masdar
    toks = [token(1, "إن", "إن", "PRT", 5, "MOD", pos_camel="conj_sub"),
            token(2, "ترد", "أراد", "VRB", 1, "OBJ", vox="a", asp="i", pos_camel="verb"),
            token(3, "أن", "أن", "PRT", 2, "OBJ", pos_camel="conj_sub"),
            token(4, "تنجح", "نجح", "VRB", 3, "OBJ", vox="a", asp="i", pos_camel="verb"),
            token(5, "تدرس", "درس", "VRB", 0, "---", vox="a", asp="i", pos_camel="verb")]
    drawn = built(["إِنْ", "تُرِدْ", "أَنْ", "تَنْجَحَ", "تَدْرُسْ"], toks)["tree"]
    condition = tree.FRAMES["condition"]
    assert drawn["label"] == tree.CONDITION
    particle, verb, answer = drawn["children"]
    assert particle["role"] == condition["particle"]
    assert (verb["role"], answer["role"]) == (condition["verb"], condition["answer"])
    masdar = verb["children"][1]
    assert (masdar["label"], masdar["role"]) == (tree.FRAMES["masdar"]["label"], "مفعول به")


def test_a_role_has_one_colour_in_every_tree():
    """A typed sentence draws like a book example: a role both tree files name wears one tone."""
    from backend.services.arabic_text import strip_diacritics
    from backend.services.nahw_book import role_table, tarkeeb_rules
    tones = {role: tone for role, (_, tone) in role_table().items()}
    clash = {key: (term["tone"], tones[strip_diacritics(term["ar"])])
             for key, term in tarkeeb_rules()["terms"].items()
             if tones.get(strip_diacritics(term["ar"]), term["tone"]) != term["tone"]}
    assert not clash
