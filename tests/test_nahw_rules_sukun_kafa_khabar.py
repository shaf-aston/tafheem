"""Three nahw rules the analyser identifies, each on held-out sentences:
التقاء الساكنين on a built word's sign, the تمييز/حال after كفى بـ (فاعل behind a
زائدة باء), and a sentence after a describing khabar as خبر ثانٍ."""
from tests.nahw_helpers import analyze, cards as _words, needs_parser, tree_roles

pytestmark = needs_parser


def test_a_built_word_moved_for_the_next_sakin_says_so():
    moved = "مبني على السكون، وحُرِّك بالكسر لالتقاء الساكنين"
    assert _words("اسْتَمِعْ إِلَى مَنِ اسْتَنْصَحَكَ")[2]["sign"] == moved
    assert _words("رَوَيْتُ عَنِ ابْنِ عَبَّاسٍ")[1]["sign"] == moved
    assert _words("جَاءَ هَؤُلَاءِ")[1]["sign"] == "مبني على الكسر"  # its own kasra


def test_after_kafa_with_an_extra_ba_the_nasb_noun_is_no_object():
    for s in ("كَفَى بِالْمَرْءِ إِثْمًا", "كَفَى بِاللَّهِ حَسِيبًا"):
        assert _words(s)[2]["role"] in ("تمييز", "حال"), s
    assert _words("كَفَاكَ اللَّهُ شَرَّهُمْ")[2]["role"] == "مفعول به"  # no ba: a real object


def test_a_sentence_after_a_describing_khabar_is_a_second_khabar():
    jobs = tree_roles(analyze("إِنَّ اللَّهَ رَحِيمٌ يَغْفِرُ الذُّنُوبَ")["tree"]["tree"])
    assert "خبر ثانٍ لإن" in jobs
    jobs = tree_roles(analyze("هَذَا رَجُلٌ يُحِبُّ الْعِلْمَ")["tree"]["tree"])
    assert "صفة" in jobs and not any(j and "ثانٍ" in j for j in jobs)  # a plain noun: its صفة
