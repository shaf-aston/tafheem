"""Links the parser scores near a tie, which another processor's floats may tip the other way (CI's AMD
runners read t004, p028, p042, u037 and x004 so): each rule makes the word's job the same either way.

Run: python -m pytest tests/nahw/test_near_ties.py
"""
from __future__ import annotations

import pytest
from tests.nahw_helpers import needs_parser, parsed_as, _role, tree_roles
from backend.services.nahw import iraab

pytestmark = needs_parser


def _roles(sentence: str) -> list[str]:
    return [w["role"] for w in iraab.analyze(sentence, recorded=False)["words"]]


@pytest.mark.parametrize("sentence, form, head, rel", [
    # اسم كان is in raf': one typed in nasb is the خبر, the اسم hidden in the verb (subject_clash.kana_nasb_khabar)
    ("إِنَّكُمْ سَتَحْرِصُونَ عَلَى الْإِمَارَةِ وَسَتَكُونُ نَدَامَةً يَوْمَ الْقِيَامَةِ", "ندامة", None, "SBJ"),
    # three to ten count a plural, so after the singular إحدى ثلاث is no صفة (typed.number_after_one)
    ("لَا يَحِلُّ دَمُ امْرِئٍ مُسْلِمٍ يَشْهَدُ أَنْ لَا إِلَهَ إِلَّا اللَّهُ وَأَنِّي رَسُولُ اللَّهِ إِلَّا بِإِحْدَى ثَلَاثٍ", "ثلاث", None, "MOD"),
    # the pronoun written onto وجد is its object, whatever word the parser hung it on (subject_clash.pronoun_on_its_verb)
    ("قَرَأْتُ وَحَلَّلْتُ التَّقْرِيرَ السَّنَوِيَّ الَّذِي أَصْدَرَتْهُ الْوِزَارَةُ فَوَجَدْتُهُ أَشْمَلَ مِمَّا تَوَقَّعْتُ وَأَدَقَّ مِنْ سَابِقِهِ", 12, 13, None),
    # نحن heads its clause, never stands under the و written onto it (mask._topic_carries_its_verb)
    ("فَإِنَّمَا الْعَدْلُ أَنْ يُسْمَعَ الطَّرَفَانِ وَنَحْنُ الْقُضَاةَ نَلْتَزِمُ بِالدَّلِيلِ", "نلتزم", 8, None),
])
def test_job_holds_whichever_way_the_tie_falls(sentence: str, form, head, rel):
    plain = _roles(sentence)
    with parsed_as(form, head, rel):
        assert _roles(sentence) == plain


def test_a_pronoun_opening_a_clause_after_waw_stays_its_mubtada():
    """u037 on CI's AVX2 runner: the و hung on the verb before and نلتزم on the و, so نحن stood under the و as a
    معطوف; a word between a pronoun and its verb leaves the verb its khabar all the same (hal.hal_clause)."""
    sentence = "فَإِنَّمَا الْعَدْلُ أَنْ يُسْمَعَ الطَّرَفَانِ وَنَحْنُ الْقُضَاةَ نَلْتَزِمُ بِالدَّلِيلِ"
    plain = _roles(sentence)
    with parsed_as(8, 6, "MOD"), parsed_as(11, 8, "OBJ"):
        assert _roles(sentence) == plain


def test_a_raf_word_after_an_opening_jar_is_the_mubtada():
    """n005 on CI's AVX2 runner: لقيمات hung as the object of حسب, which opens the sentence behind its ب; a noun
    takes no object, and one in jarr is told of nothing, so the raf' word is the mubtada (khabar.object_of_noun)."""
    with parsed_as(5, 2, "OBJ"):
        assert _roles("بِحَسْبِ ابْنِ آدَمَ لُقَيْمَاتٌ يُقِمْنَ صُلْبَهُ فَإِنْ كَانَ لَا مَحَالَةَ فَثُلُثٌ لِطَعَامِهِ")[3] == "مبتدأ"


def test_a_zarf_on_la_is_its_khabars_mafool_fihi():
    """x004: بَعْدِي hung on لا as its خبر is «خبر لا», hung as a modifier it is the unwritten خبر's مفعول فيه, both
    the books' (its key takes either); verbs elsewhere in the sentence leave لا's clause verbless (slot.zarf_of_khabar)."""
    with parsed_as("بعد", None, "MOD"):
        assert _roles("أَمَا تَرْضَى أَنْ تَكُونَ مِنِّي بِمَنْزِلَةِ هَارُونَ مِنْ مُوسَى، إِلَّا أَنَّهُ لَا نَبِيَّ بَعْدِي")[-1] == "مفعول فيه"


@pytest.mark.parametrize("sentence, at, role", [
    ("إِنَّ زَيْدًا جَالِسٌ عِنْدَنَا", 3, "مفعول فيه"),  # nearest case: on إنّ's وصف khabar the ظرف stays a ظرف
    ("لاَ هِجْرَةَ بَعْدَ الْفَتْحِ", 2, "مفعول فيه"),  # h31: a verbless sentence, named so before the rule
    ("كَانَ زَيْدٌ قَائِمًا", 1, "اسم كان"),  # nearest case: a raf' اسم stays the اسم
    ("قَرَأْتُ التَّقْرِيرَ فَوَجَدْتُهُ أَشْمَلَ مِمَّا تَوَقَّعْتُ", 3, "مفعول به"),  # here the parser itself hangs ه on أشمل
    ("جَاءَ رِجَالٌ ثَلَاثَةٌ", 2, "صفة"),  # nearest case: after a plural, the number describes it
    ("الْعِلْمُ نُورٌ وَنَحْنُ نَطْلُبُهُ", 2, "مبتدأ"),  # nearest case: parsed plainly, نحن is the مبتدأ
    ("فِي الدَّارِ رَجُلٌ", 2, "مبتدأ"),  # nearest case: after a plain jar-majroor the raf' noun is the مبتدأ
    ("زَيْدٌ أَكْثَرُ مِنْكَ مَالًا", 1, "خبر"),  # a raf' opener keeps its khabar
])
def test_sibling_left_alone(sentence: str, at: int, role: str):
    assert _role(sentence, at).startswith(role)


def test_a_clause_under_its_waw_stays_there():
    """وَاللَّهُ أَكْبَرُ hangs under its و, the book's shape: only a loop moves the noun off it."""
    assert "واو الحال" in tree_roles(iraab.analyze("خَرَجَ زَيْدٌ وَاللَّهُ أَكْبَرُ", recorded=False)["tree"]["tree"])
