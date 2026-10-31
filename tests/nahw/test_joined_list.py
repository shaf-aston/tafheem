"""A list joined by و: every معطوف of it is joined on its first word, the معطوف عليه (as the cards say,
card_wording.counting.followed), so the picture draws the معطوفات side by side under the list's job, not
each one inside the one before; and a known noun after an indefinite one is its بدل, never its صفة."""
from __future__ import annotations

from backend.services.nahw import iraab

HADITH = "بُنِيَ الْإِسْلَامُ عَلَى خَمْسٍ شَهَادَةِ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَإِقَامِ الصَّلَاةِ وَإِيتَاءِ الزَّكَاةِ وَالْحَجِّ وَصَوْمِ رَمَضَانَ"


def _units(node: dict, role: str) -> list[dict]:
    found = [node] if node.get("role") == role else []
    for kid in node.get("children", []):
        found += _units(kid, role)
    return found


def test_each_matoof_of_a_list_stands_beside_the_others_under_one_unit():
    tree = iraab.analyze(HADITH, recorded=False)["tree"]["tree"]
    matoof = _units(tree, "معطوف")
    # four معطوفات, none inside another, all under the one unit that holds the معطوف عليه
    assert len(matoof) == 4
    assert not any(_units(kid, "معطوف") for unit in matoof for kid in unit.get("children", []))
    whole = next(u for u in _units(tree, "بدل") if any(k.get("role") == "معطوف عليه" for k in u.get("children", [])))
    assert sum(k.get("role") == "معطوف" for k in whole["children"]) == 4


def test_the_first_word_of_a_list_is_named_its_matoof_alayh():
    tree = iraab.analyze("جَاءَ زَيْدٌ وَعَمْرٌو وَبَكْرٌ", recorded=False)["tree"]["tree"]
    roles = [kid.get("role") for unit in _units(tree, "فاعل") for kid in unit["children"]]
    assert roles == ["معطوف عليه", "حرف عطف", "معطوف", "حرف عطف", "معطوف"]


def test_a_hollow_masdar_with_its_ta_fallen_is_a_noun_with_its_mudaf_ilayh():
    roles = [w["role"] for w in iraab.analyze(HADITH, recorded=False)["words"]]
    assert roles[10:13] == ["معطوف", "مضاف إليه", "معطوف"]  # وَإِقَامِ الصَّلَاةِ وَإِيتَاءِ


def test_a_known_noun_after_an_indefinite_one_is_its_badal():
    assert [w["role"] for w in iraab.analyze(HADITH, recorded=False)["words"]][4] == "بدل"  # شَهَادَةِ after خَمْسٍ
    assert [w["role"] for w in iraab.analyze("اهْدِنَا إِلَى صِرَاطٍ مُسْتَقِيمٍ صِرَاطِ اللَّهِ", recorded=False)["words"]][4] == "بدل"


def test_a_describing_word_added_to_a_noun_with_al_is_still_a_sifah():
    # its إضافة is لفظية and makes nothing known
    assert [w["role"] for w in iraab.analyze("جَاءَ رَجُلٌ حَسَنُ الْوَجْهِ", recorded=False)["words"]][2] == "صفة"
