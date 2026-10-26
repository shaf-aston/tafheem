"""A حال tells the state of its صاحب; it is no part of that noun, so the picture draws it beside
the noun, named for it (جملة عز وجل في محل نصب حال من لفظ الجلالة), never inside the noun's own
box. A noun read as a مضاف with nothing added to it is indefinite, so the indefinite word after
it in its case is its صفة (ضَلَّ ضَلَالًا بَعِيدًا typed bare)."""
import pytest

from backend.services.nahw.syntax.facts import agrees
from tests.nahw_helpers import analyze, cards, needs_parser


def nodes(node: dict):
    yield node
    for kid in node.get("children", []):
        yield from nodes(kid)


def tree(sentence: str) -> dict:
    return analyze(sentence)["tree"]["tree"]


@needs_parser
def test_a_haal_on_a_mudaf_ilayh_stands_beside_it_named_for_its_owner():
    top = tree("هُوَ رِزْقُ اللَّهِ عَزَّ وَجَلَّ")
    haal = next(n for n in nodes(top) if n.get("role") == "حال")
    assert "«اللَّهِ»" in haal["detail"]
    assert not any(n.get("role") == "مضاف إليه" and n.get("children") for n in nodes(top))


@needs_parser
def test_a_haal_hung_on_the_doer_stands_beside_it():
    top = tree("قال رسول الله صلى الله عليه وسلم")
    haal = next(n for n in top["children"] if n.get("role") == "حال")
    assert "«رسول»" in haal["detail"]


@needs_parser
@pytest.mark.parametrize("sentence,roles", [("جَاءَ الطَّالِبُ يَرْكُضُ", ["فعل", "فاعل", "حال"]),
                                            ("رَأَيْتُ صَدِيقَكَ مُسْرِعًا", ["فعل", "مفعول به", "حال"]),
                                            ("جَاءَ زَيْدٌ رَاكِبًا", ["فعل", "فاعل", "حال"])])
def test_a_haal_on_the_verb_stays_beside_it(sentence, roles):
    assert [n.get("role") for n in tree(sentence)["children"]] == roles


@needs_parser
@pytest.mark.parametrize("sentence,owner", [("مَرَرْتُ بِزَيْدٍ رَاكِبًا", "«زَيْدٍ»"), ("نظرت إلى السماء صافية", "«السماء»")])
def test_a_haal_of_a_majroor_stands_outside_the_jar_majroor_on_the_verb(sentence, owner):
    kids = tree(sentence)["children"]
    assert kids[-1]["role"] == "حال" and owner in kids[-1]["detail"]
    assert not any(k.get("role") == "حال" for jar in kids for k in jar.get("children", []))


@needs_parser
@pytest.mark.parametrize("sentence", ["ضرب ضرب شديدا", "ومن يشرك بالله فقد ضل ضلال بعيدا"])
def test_after_a_bare_noun_with_nothing_added_the_indefinite_word_is_its_sifah(sentence):
    assert cards(sentence)[-1]["role"] == "صفة"


@needs_parser
def test_after_a_real_mudaf_the_indefinite_word_in_nasb_is_no_sifah():
    assert cards("رأيت كتاب طالب جديدا")[-1]["role"] == "حال"


@pytest.mark.parametrize("stt,mudaf,agree", [("c", False, True), ("c", True, False), ("d", False, False), ("i", False, True)])
def test_a_noun_is_a_mudaf_only_with_something_added(stt, mudaf, agree):
    head = {"stt": stt, "mudaf": mudaf, "cas": "a", "pos": "NOM", "typed": "", "form": "x", "lemma": "x", "base": "x"}
    token = {"stt": "i", "cas": "a", "pos": "NOM", "typed": "", "form": "y", "lemma": "y", "base": "y"}
    assert agrees(token, head) is agree


@needs_parser
def test_the_waw_before_a_condition_stands_at_its_front_and_the_answer_holds_its_own_words():
    top = tree("ومن يشرك بالله فقد ضل ضلال بعيدا")
    assert top["label"] == "جُمْلَةٌ شَرْطِيَّةٌ" and top["children"][0]["role"] == "حرف عطف"
    answer = next(n for n in top["children"] if n.get("role") == "جواب الشرط")
    assert [n.get("role") for n in answer["children"]] == ["حرف", "فعل", "مفعول مطلق"]


@needs_parser
@pytest.mark.parametrize("sentence", ["ومن شاء فليصمه ومن شاء أفطر", "إن تدرس تنجح وإن تكسل ترسب"])
def test_a_waw_beside_a_condition_is_named_no_verbal_sentence(sentence):
    for n in nodes(tree(sentence)):
        kids = n.get("children", [])
        assert not (n.get("label") == "جُمْلَةٌ فِعْلِيَّةٌ" and not n.get("role")
                    and any(k.get("label") == "جُمْلَةٌ شَرْطِيَّةٌ" for k in kids))
