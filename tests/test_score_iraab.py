"""The answer key compares roles by family, whichever way each side spells them."""
from backend.scripts.score_iraab import KEY, book_sentences, family
from backend.services.arabic_text import bare_letters


def test_longest_term_wins():
    assert family("فِعْلٌ مَعَ فَاعِلِهِ") == "fil"
    assert family("نَائِبُ الْفَاعِلِ") == "naib_fail"
    assert family("مُضَافٌ إِلَيْهِ") == "mudaf_ilayh"
    assert family("مُضَافٌ") == "mudaf"
    assert family("حَرْفٌ مُشَبَّهٌ بِالْفِعْلِ") == "harf"


def test_app_and_book_spellings_meet():
    assert family("مبتدأ (مرفوع)") == family("مُبْتَدَأٌ") == "mubtada"
    assert family("خبر إن") == family("خَبَرُ إِنَّ") == "khabar_inna"


def test_no_two_families_share_a_folded_term():
    # كأن folds to كان, which once filed اسم كان under إن
    assert family("اسم كان") == "ism_kana" and family("خبر كان") == "khabar_kana"
    seen = {}
    for fam, terms in KEY["families"].items():
        for term in terms:
            assert seen.setdefault(bare_letters(term), fam) == fam, term


def test_unknown_role_is_not_guessed():
    assert family("–") is None
    assert family(None) is None


def test_every_book_word_has_a_role():
    sentences = book_sentences()
    assert sentences
    assert all(len(s["roles"]) == len(s["words"]) and all(s["roles"]) for s in sentences)
