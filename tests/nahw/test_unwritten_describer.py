"""What a noun for a thing can hold, and what a بدل is named, in the picture a reader sees.

A jar-majroor after رَجُلٌ cannot hang on a noun that works on nothing: it hangs on a word no one
writes (ثابت) that describes it, and the noun is its موصوف. A بدل's head is its مبدل منه. A pronoun
sharing the one written nun of إِنَّ is its own column (إِنِّ، ي), not a split of the nun.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.nahw.syntax.catib_onnx import files_present
from backend.services.text.arabic_text import strip_diacritics

pytestmark = pytest.mark.skipif(not files_present(), reason="CATiB parser model files not present")
client = TestClient(app)


def drawn(sentence: str) -> tuple[list[str], list[dict]]:
    """The picture's columns, and every node in it."""
    tree = client.post("/api/analyze", json={"sentence": sentence}).json()["tree"]
    nodes: list[dict] = []

    def walk(node):
        nodes.append(node)
        for child in node.get("parts", []) + node.get("children", []):
            walk(child)
    walk(tree["tree"])
    return tree["words"], nodes


def role_of(columns: list[str], nodes: list[dict], bare: str) -> list[str | None]:
    return [n["role"] for n in nodes if n.get("word") is not None and strip_diacritics(columns[n["word"]]) == bare]


@pytest.mark.parametrize("sentence, noun", [
    ("دَبَّرَ رَجُلٌ مِنَ الأَنْصَارِ غُلاَمًا لَهُ", "رجل"),
    ("جَاءَ رَجُلٌ مِنَ الْعَرَبِ", "رجل"),
    ("اشْتَرَيْتُ كِتَابًا مِنَ الْمَكْتَبَةِ", "كتابا"),  # not the sentence it was built on
])
def test_what_hangs_on_a_noun_for_a_thing_hangs_on_its_unwritten_describer(sentence, noun):
    columns, nodes = drawn(sentence)
    assert "موصوف" in role_of(columns, nodes, noun)
    assert any(n.get("hidden") and n["role"] == "صفة" for n in nodes)
    assert any((n.get("label") or "").startswith("متعلق بـثابت") for n in nodes)


def test_a_jar_majroor_after_a_known_noun_or_a_verb_keeps_its_own_head():
    for sentence in ("جَاءَ الرَّجُلُ مِنَ الْبَيْتِ", "كُوبٌ مِنَ الْقَهْوَةِ"):
        _, nodes = drawn(sentence)
        assert not any(n.get("hidden") and n["role"] == "صفة" for n in nodes)



@pytest.mark.parametrize("sentence, head", [
    ("هَذَا حُبٌّ لِلْوَطَنِ", "حُبٌّ"),  # tanween does not stop a masdar working
    ("أَعْجَبَنِي حِرْصُ الْمُهَنْدِسِينَ عَلَى الْمَوَاعِيدِ", "حِرْصُ"),  # annexed
    ("الْحُكْمُ عَلَى الْمُتَّهَمِينَ عَادِلٌ", "الْحُكْمُ"),  # with ال
    ("رَأَيْتُ مَوْجًا كَالْجِبَالِ", "ثابت"),  # the kaf 'like' completes no masdar: it describes
    ("جَاءَ الطَّالِبُ وَمِثْلُهُ مَعَهُ", "ثابت"),  # مِثْل has a masdar's measure and names no doing
])
def test_what_hangs_after_a_masdar_hangs_on_it_in_every_state_but_a_likeness_does_not(sentence, head):
    """facts.masdar_at_work and likeness_jarr: a masdar works bare, annexed or with ال; ك after it is its صفة."""
    _, nodes = drawn(sentence)
    hung = [n["label"] for n in nodes if (n.get("label") or "").startswith("متعلق بـ")]
    assert hung == [f"متعلق بـ{head}"], hung


@pytest.mark.parametrize("sentence, head", [
    ("جَاءَ الْخَلِيفَةُ عُمَرُ", "الخليفة"),
    ("أَعْجَبَنِي الطَّالِبُ عِلْمُهُ", "الطالب"),  # another بدل, another head
])
def test_the_head_of_a_badl_is_named_its_mubdal_minhu(sentence, head):
    columns, nodes = drawn(sentence)
    assert "مبدل منه" in role_of(columns, nodes, head)


def test_a_particle_before_a_badl_keeps_its_own_name():
    columns, nodes = drawn("لَا إِلَهَ إِلَّا اللَّهُ")
    assert role_of(columns, nodes, "إلا") == ["أداة استثناء"]


@pytest.mark.parametrize("sentence, columns", [
    ("إِنِّي طَالِبٌ", ["إِنِّ", "ي", "طَالِبٌ"]),
    ("كَأَنِّي طَالِبٌ", ["كَأَنِّ", "ي", "طَالِبٌ"]),
    ("إِنَّنِي طَالِبٌ", ["إِنَّ", "نِي", "طَالِبٌ"]),  # both nuns written: the wiqaya nun stays with the pronoun
])
def test_the_one_written_nun_of_inna_stays_with_inna(sentence, columns):
    assert drawn(sentence)[0] == columns


@pytest.mark.parametrize("sentence, said, not_said", [
    ("إِنِّي طَالِبٌ", "«ي» ضمير", "«ني»"),
    ("كَأَنِّي طَالِبٌ", "«ي» ضمير", "«ني»"),
    ("إِنَّنِي طَالِبٌ", "«ني» ضمير", "«ي» ضمير"),  # both nuns written: the pronoun is نِي
])
def test_the_card_says_the_pronoun_the_picture_cuts(sentence, said, not_said):
    reason = client.post("/api/analyze", json={"sentence": sentence}).json()["words"][0]["reason"]
    assert said in reason and not_said not in reason
