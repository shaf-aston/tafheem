"""أمّا, its mim doubled (Ibn Hisham, Awdah al-Masalik, vol 4 p231-232, فصل في أما; page unchecked).

It is «حرف شرط وتفصيل وتوكيد»; the word after it is the مبتدأ, and the فاء that must follow is «الفاء الواقعة في
جواب أما», opening the خبر. A مَنْ or ما after it is the relative, not a condition and not a question, and the verb
after it is its صلة. أَمَا, its mim light, opens speech and asks no فاء.
"""
from tests.nahw_helpers import analyze, needs_parser

pytestmark = needs_parser

AMMA = "حرف شرط وتفصيل وتوكيد"
FA = "الفاء الواقعة في جواب أما"


def nodes(node: dict):
    yield node
    for kid in node.get("children", []):
        yield from nodes(kid)


def tree(sentence: str) -> list[dict]:
    return list(nodes(analyze(sentence)["tree"]["tree"]))


def roles(sentence: str) -> list:
    return [n.get("role") for n in tree(sentence)]


def test_amma_and_its_fa_are_named():
    found = roles("أَمَّا زَيْدٌ فَقَائِمٌ")
    assert AMMA in found and FA in found


def test_a_light_ama_is_no_amma_and_names_no_fa():
    found = roles("أَمَا إِنَّ زَيْدًا قَائِمٌ فَاذْهَبْ إِلَيْهِ")
    assert AMMA not in found and FA not in found


def test_the_fa_named_is_the_answers_not_the_one_joining_amma():
    found = roles("فَأَمَّا الْيَتِيمَ فَلَا تَقْهَرْ")
    assert found.count(FA) == 1 and AMMA in found


def test_man_after_amma_is_the_relative_mubtada_not_a_condition():
    found = tree("فَأَمَّا مَنْ أَعْطَى وَاتَّقَى فَسَنُيَسِّرُهُ")
    relative = next(n for n in found if n.get("role") == "مبتدأ")
    assert "صلة" in [n.get("role") for n in nodes(relative)]
    assert "فعل الشرط" not in [n.get("role") for n in found]


def test_ma_after_amma_is_the_mubtada_not_the_doer_of_its_sila():
    found = tree("فَأَمَّا مَا يَنْفَعُ النَّاسَ فَيَمْكُثُ")
    relative = next(n for n in found if n.get("role") == "مبتدأ")
    assert "صلة" in [n.get("role") for n in nodes(relative)]
    assert "فاعل" not in [n.get("role") for n in found]


def test_man_kana_after_amma_is_no_question():
    found = tree("وَأَمَّا مَنْ كَانَ مِنْ أَهْلِ الشَّقَاءِ فَيُيَسَّرُ")
    assert "استفهام" not in (found[0].get("label") or "")
    relative = next(n for n in found if n.get("role") == "مبتدأ")
    assert "صلة" in [n.get("role") for n in nodes(relative)]


def test_man_kana_with_no_amma_still_asks():
    assert "اسم كان" in roles("مَنْ كَانَ مَعَكَ")


def test_a_relative_ma_after_its_verb_is_still_its_doer():
    assert "فاعل" in roles("قَامَ مَا قَامَ")
