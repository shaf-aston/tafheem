"""إنّما is إنّ with the ما الكافة written on it: it conditions nothing and works on nothing, so the
verb after it stays in raf' and its sentence stays verbal (Fatir 35:28), and a raf' noun that comes
after the verb and its object, with no other doer, is the doer, not a word hung on the noun before
it (Tasheel 1.8 n4 p21; Ibn Aqil V2 p95)."""
from backend.services.text.arabic_text import strip_diacritics
from tests.nahw_helpers import analyze, needs_parser

pytestmark = needs_parser

AYAH = "إِنَّمَا يَخْشَى اللَّهَ مِنْ عِبَادِهِ الْعُلَمَاءُ"


def leaves(node: dict) -> list[dict]:
    return [node] + [leaf for child in node.get("children", []) for leaf in leaves(child)]


def test_innama_with_a_verb_after_it_opens_no_condition():
    answer = analyze(AYAH)
    words = answer["words"]
    assert "شرطية" not in strip_diacritics(answer["summary"])
    assert words[1]["case"] == "raf'" and "الشرط" not in words[1]["reason"]
    assert words[2]["role"] == "مفعول به"


def test_the_raf_noun_after_the_verb_and_its_object_is_the_doer():
    answer = analyze(AYAH)
    assert answer["words"][5]["role"] == "فاعل"
    doers = [n for n in leaves(answer["tree"]["tree"]) if n.get("role") == "فاعل"]
    assert [answer["tree"]["words"][n["word"]] for n in doers] == ["الْعُلَمَاءُ"]  # no hidden pronoun beside it


def test_a_nominal_sentence_after_innama_keeps_its_mubtada_and_khabar():
    answer = analyze("إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ")
    assert "اسمية" in strip_diacritics(answer["summary"])
    assert answer["words"][1]["role"] == "مبتدأ"
    assert "خبر" in [n.get("role") for n in leaves(answer["tree"]["tree"])]


def drawn(answer: dict) -> list[tuple[str, str]]:
    words = answer["tree"]["words"]
    return [(strip_diacritics(words[n["word"]]), n.get("role")) for n in leaves(answer["tree"]["tree"])
            if n.get("word") is not None and not n.get("children")]


KAFFA = [("إِنَّمَا الْمُؤْمِنُونَ إِخْوَةٌ", "إن"),
         ("كَأَنَّمَا يُسَاقُونَ إِلَى الْمَوْتِ", "كأن"),
         ("أَنَّمَا إِلَٰهُكُمْ إِلَٰهٌ وَاحِدٌ", "أن"),
         ("لَيْتَمَا زَيْدٌ قَائِمٌ", "ليت"),
         ("لَعَلَّمَا زَيْدٌ قَائِمٌ", "لعل"),
         ("لَكِنَّمَا زَيْدٌ قَائِمٌ", "لكن"),
         ("إنما المؤمنون إخوة", "إن"),  # typed without vowels
         ("ليتما زيد قائم", "ليت")]


def test_every_sister_with_ma_is_drawn_as_the_stopped_sister_then_ma_al_kaffa():
    """A ما written onto an إن sister is always ما الكافة (Ibn Aqil on إن and her sisters, page unchecked)."""
    for sentence, sister in KAFFA:
        answer = analyze(sentence)
        assert drawn(answer)[:2] == [(sister, "حرف ناسخ مكفوف"), ("ما", "ما الكافة")], sentence
        assert answer["words"][0]["name"] == "كافة ومكفوفة", sentence


def test_a_joined_fa_stays_its_own_piece_before_the_stopped_sister():
    assert drawn(analyze("فَإِنَّمَا عَلَيْكَ الْبَلَاغُ"))[:3] == [("ف", "حرف عطف"), ("إن", "حرف ناسخ مكفوف"), ("ما", "ما الكافة")]


def test_a_verb_that_only_looks_like_laytama_stays_a_verb():
    pieces = drawn(analyze("لِيَتِمَّا الْأَمْرُ"))
    assert "ما الكافة" not in [role for _, role in pieces]
    assert pieces[1] == ("يتما", "فعل مضارع للأمر")
