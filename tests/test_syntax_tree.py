"""The bracket picture for a typed sentence, built from the parser's links."""
from backend.services.syntax import naming, tree
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
    assert unit["label"] == tree.IDAFA  # what it is
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
