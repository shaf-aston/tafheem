"""Smoke tests for the torch-free CATiB parser (backend/services/nahw/syntax/catib_onnx.py).

Skips cleanly, rather than failing, when the model files have not been
dropped into backend/data/parser/ (see catib_onnx.py's docstring).
"""

from backend.services.sarf import morphology
from backend.services.nahw.syntax import catib_onnx
from backend.services.nahw.syntax.catib_onnx import parse
from tests.nahw_helpers import needs_parser

pytestmark = needs_parser


def test_verb_subject_object():
    typed = ["كَتَبَ", "الطَّالِبُ", "رِسَالَةً"]
    catib_onnx.warm()
    tokens = parse(typed, morphology.pick(typed, catib_onnx.disambiguator()))
    by_form = {t["form"]: t for t in tokens}

    verb = by_form["كتب"]
    assert verb["head"] == 0, "the verb should be the sentence root"

    subject = by_form["الطالب"]
    assert tokens[subject["id"] - 1]["head"] == verb["id"]
    assert subject["rel"] == "SBJ"

    obj = by_form["رسالة"]
    assert tokens[obj["id"] - 1]["head"] == verb["id"]
    assert obj["rel"] == "OBJ"


def test_empty_input_returns_empty_list():
    assert parse([], []) == []


def test_a_sentence_rooted_on_a_harf_atf_still_gets_its_roles():
    """Al-Baqarah 2:259, as the Qur'an writes it: the parser roots the whole ayah on its first أَوْ,
    and a jar-majroor hung on that حرف عطف used to crash the tree (KeyError 'pos'), leaving every
    word of the ayah unnamed. Found by the Dictionary's sentence yardstick."""
    from backend.services.nahw import iraab

    ayah = (
        "أَوْ كَٱلَّذِى مَرَّ عَلَىٰ قَرْيَةٍۢ وَهِىَ خَاوِيَةٌ عَلَىٰ عُرُوشِهَا قَالَ أَنَّىٰ يُحْىِۦ "
        "هَـٰذِهِ ٱللَّهُ بَعْدَ مَوْتِهَا ۖ فَأَمَاتَهُ ٱللَّهُ مِا۟ئَةَ عَامٍۢ ثُمَّ بَعَثَهُۥ ۖ قَالَ "
        "كَمْ لَبِثْتَ ۖ قَالَ لَبِثْتُ يَوْمًا أَوْ بَعْضَ يَوْمٍۢ ۖ قَالَ بَل لَّبِثْتَ مِا۟ئَةَ "
        "عَامٍۢ فَٱنظُرْ إِلَىٰ طَعَامِكَ وَشَرَابِكَ لَمْ يَتَسَنَّهْ ۖ وَٱنظُرْ إِلَىٰ حِمَارِكَ "
        "وَلِنَجْعَلَكَ ءَايَةًۭ لِّلنَّاسِ ۖ وَٱنظُرْ إِلَى ٱلْعِظَامِ كَيْفَ نُنشِزُهَا ثُمَّ "
        "نَكْسُوهَا لَحْمًۭا ۚ فَلَمَّا تَبَيَّنَ لَهُۥ قَالَ أَعْلَمُ أَنَّ ٱللَّهَ عَلَىٰ كُلِّ "
        "شَىْءٍۢ قَدِيرٌۭ"
    )
    read = iraab.analyze(ayah, recorded=False)
    assert read["read_failed"] is False
    assert any(word.get("role") for word in read["words"])
