"""فَلَا أَدْرِي قَالَ ذَلِكَ لَهُ فِي سَنَةٍ أَوْ فِي ثَلَاثِ سِنِينَ: the second jar-majroor is
معطوف on the first and hangs where it hangs, and a number is added to what it counts."""
from tests.nahw_helpers import analyze, cards, needs_parser, tree_roles

SENTENCE = "فَلَا أَدْرِي قَالَ ذَلِكَ لَهُ فِي سَنَةٍ أَوْ فِي ثَلَاثِ سِنِينَ"


@needs_parser
def test_a_jar_majroor_after_a_harf_atf_is_matoof_and_hangs_on_the_verb():
    tree = analyze(SENTENCE)["tree"]["tree"]
    assert "معطوف" in tree_roles(tree)
    assert not any("أَوْ" in label for label in tree_roles(tree, "label"))
    assert tree_roles(tree, "label").count("متعلق بـقَالَ") == 3


@needs_parser
def test_i_know_is_the_present_its_doer_ana():
    know = cards(SENTENCE)[1]
    assert (know["role"], know["case"]) == ("فعل", "raf'") and "أنا" in know["reason"]


@needs_parser
def test_a_number_added_to_what_it_counts_is_idafa_of_min():
    counted = cards(SENTENCE)[-1]
    assert counted["role"] == "مضاف إليه" and "«من»" in counted["reason"] and "لفظية" not in counted["reason"]
