"""A و before أَنْ and its verb joins a second masdar to the first; it is no واو القسم, since no جار comes onto a particle.

أُرِيدُ أَنْ أَقْرَأَ وَأَنْ أَكْتُبَ: the two masdars are one مفعول به, the second معطوف on the first.
"""
from tests.nahw_helpers import analyze, needs_parser


def roles(node: dict) -> list:
    return [kid.get("role") for kid in node.get("children", [])]


@needs_parser
def test_the_second_masdar_is_joined_not_jarred():
    result = analyze("أُرِيدُ أَنْ أَقْرَأَ وَأَنْ أَكْتُبَ")
    tree = result["tree"]["tree"]
    assert roles(tree) == ["فعل", "مفعول به"]
    assert roles(tree["children"][1]) == ["معطوف عليه", "حرف عطف", "معطوف"]
    assert "حرف جر" not in str(tree)


@needs_parser
def test_the_oath_waw_still_jars():
    assert "حرف قسم وجر" in str(analyze("وَاللَّهِ لَأَفْعَلَنَّ")["tree"]["tree"])


@needs_parser
def test_a_jar_before_an_still_jars_its_masdar():
    assert "حرف جر" in str(analyze("عَمِلُوا إِلَى أَنْ يُوَفِّرُوا الْمَالَ")["tree"]["tree"])


@needs_parser
def test_after_imma_the_waw_joins():
    assert "حرف جر" not in str(analyze("إِمَّا أَنْ تَذْهَبَ وَإِمَّا أَنْ تَبْقَى")["tree"]["tree"])
