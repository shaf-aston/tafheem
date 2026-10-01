"""The answer key compares roles by family, whichever way each side spells them."""
import re

from backend.scripts.score_iraab import (
    KEY, book_sentences, disagreements, family, fresh_sentences, routed)
from backend.services.syntax.naming import ROLES
from backend.services.arabic_text import bare_letters, words


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


FRESH_ROLES = {
    "فعل", "فاعل", "نائب فاعل", "مبتدأ", "خبر", "اسم كان", "خبر كان", "اسم كاد", "خبر كاد",
    "اسم إن", "خبر إن", "مفعول به", "مفعول مطلق", "مفعول فيه", "مفعول لأجله", "مفعول معه",
    "تمييز", "حال", "صفة", "مضاف إليه", "حرف جر", "مجرور", "حرف", "معطوف", "منادى",
    "مستثنى", "توكيد", "بدل",
}


def test_fresh_set_is_well_formed():
    fresh = fresh_sentences()
    assert len({s["id"] for s in fresh}) == len(fresh)
    assert len({s["sentence"] for s in fresh}) == len(fresh)
    assert {s["split"] for s in fresh} == {"tune", "hold"}
    for s in fresh:
        assert len(s["key"]) == len(words(s["sentence"])), s["id"]
        assert set(s["key"]) <= FRESH_ROLES, s["id"]


def test_tree_leaf_clash_ignores_the_pictures_own_wording():
    leaf = lambda i, role: {"word": i, "role": role, "children": []}
    tree = {"words": ["a", "b", "c"], "tree": {"word": None, "children": [
        leaf(0, "مُضَافٌ"), leaf(1, "حرف جر"), leaf(2, "فاعل")]}}
    cards = [{"role": "مبتدأ"}, {"role": "حرف جر"}, {"role": "مفعول به"}]
    assert disagreements(cards, tree) == [(2, "مفعول به", "فاعل")]


def test_every_book_word_has_a_role():
    sentences = book_sentences()
    assert sentences
    assert all(len(s["roles"]) == len(s["words"]) and all(s["roles"]) for s in sentences)


def test_cards_and_picture_speak_one_vocabulary():
    """Each fresh sentence through the route: every card role is a name from
    naming.ROLES (or the tense form of a verb, or the dash for none), carries no
    Latin letter and no bracketed note, and agrees with the tree leaf of its word."""
    known = set(ROLES) | {"–"}
    for ex in fresh_sentences():
        answer = routed(ex["sentence"], None)
        for card in answer["words"]:
            role = card.get("role") or "–"
            assert not re.search(r"[A-Za-z(]", role), (ex["id"], role)
            assert role in known or role.startswith("فعل "), (ex["id"], role)
        assert disagreements(answer["words"], answer.get("tree")) == [], ex["id"]
