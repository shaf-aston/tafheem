"""services/roots.py: one answer to "what is this word's root?" for every tab.

Five places used to answer it, each its own way, and قالوا had a root in none:
CAMeL writes ق#ل for it and the app threw that away, so Sarf had no table for
it, Nahw printed no root, and the dictionary found nothing.

Maqayees ships with the repository, so it is the book these tests settle a weak
radical against; the dictionary and the corpus are built on the server and are
stood in for here.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app
from backend.services import arabic_text, dictionary_service, morphology, quran_corpus, roots, sarf_word
from backend.services.daleel.query.lexicon import DictionaryLexicon


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    """No dictionary and no corpus unless a test gives one; nothing remembered between tests."""
    monkeypatch.setattr(dictionary_service, "_dictionary", [])
    monkeypatch.setattr(dictionary_service, "_arabic_index", {})
    monkeypatch.setattr(dictionary_service, "_loaded", True)
    monkeypatch.setattr(quran_corpus, "root_of", lambda word: None)  # None: no word the Qur'an has
    monkeypatch.setattr(roots, "_corpus_roots", lambda: {})
    remembered = roots.roots_of  # a test may stand in for it; its cache is still this one's
    remembered.cache_clear()
    dictionary_service._arabic_matches.cache_clear()
    yield
    remembered.cache_clear()
    dictionary_service._arabic_matches.cache_clear()


def dictionary(monkeypatch, *entries: tuple[str, str]) -> None:
    """Headwords (word, root), indexed exactly as load_dictionary() indexes them."""
    written = [{"arabic": word, "root": root, "definitions": ["-"]} for word, root in entries]
    monkeypatch.setattr(dictionary_service, "_dictionary", written)
    monkeypatch.setattr(dictionary_service, "_arabic_index", dictionary_service._build_indices(written)[0])


def read_as(monkeypatch, table: dict[str, list[tuple[str, str]]]) -> None:
    """CAMeL's readings, as CI has no CAMeL data."""
    read = {word: [morphology.Reading(lemma, root, rooted=True) for lemma, root in rows] for word, rows in table.items()}
    monkeypatch.setattr(morphology, "readings", lambda word: read.get(word, []))


def test_a_weak_radical_becomes_the_letter_the_word_itself_carries():
    assert roots.settle("ب#ت", "بيت") == "بيت"  # Maqayees has بيت, not بوت
    assert roots.settle("#فق", "توفيق") == "وفق"


def test_a_weak_radical_no_book_files_is_no_root():
    assert roots.settle("ظ#ظ", "ظاظ") == ""


def test_two_that_fit_are_told_apart_by_where_the_word_is_filed(monkeypatch):
    # Maqayees has بوع (a fathom) and بيع (selling); باع shows neither letter.
    dictionary(monkeypatch, ("بَاعَ", "بيع"))
    assert roots.settle("ب#ع", "باع") == "بيع"


def test_a_doubled_root_is_found_in_maqayees_under_its_two_letters():
    assert roots.spelling("فرر") == "فرر"


def test_the_corpus_answers_first(monkeypatch):
    monkeypatch.setattr(quran_corpus, "root_of", lambda word: "قول" if word == "قالوا" else None)
    read_as(monkeypatch, {"قالوا": [("قيل", "قيل")]})
    assert roots.roots_of("قالوا") == ("قول", "قيل")


def test_any_form_is_read_to_its_root(monkeypatch):
    read_as(monkeypatch, {"قالوا": [("قال", "ق#ل")], "مُنْتَصِرًا": [("منتصر", "نصر")]})
    dictionary(monkeypatch, ("قَالَ", "قول"))
    assert roots.root_of("قالوا") == "قول"
    assert roots.root_of("مُنْتَصِرًا") == "نصر"
    assert roots.root_of("زززز") == ""


def test_every_tab_gives_the_same_root(monkeypatch):
    read_as(monkeypatch, {"قالوا": [("قال", "ق#ل")]})
    dictionary(monkeypatch, ("قَالَ", "قول"), ("قَوْل", "قول"))
    monkeypatch.setattr(morphology, "analyze_word", lambda word: {"root": "", "pos": "verb", "gloss": "", "features": ""})
    assert sarf_word.analyze("قالوا", None).root == "قول"  # Sarf
    assert DictionaryLexicon().root_of("قالوا") == "قول"  # Daleel
    app = TestClient(create_app())
    assert app.get("/api/dictionary/search", params={"q": "قالوا"}).json()["root"] == "قول"  # dictionary


def test_the_quran_root_search_opens_the_first_root_the_quran_has(monkeypatch):
    monkeypatch.setattr(roots, "roots_of", lambda word: ("فري", "فرر") if word == "ففروا" else ())
    asked = []

    def occurrences(root, limit):
        asked.append(root)
        return {"root": root, "total": 3 if root == "فرر" else 0, "forms": [], "occurrences": []}

    monkeypatch.setattr(quran_corpus, "occurrences_of_root", occurrences)
    answer = TestClient(create_app()).get("/api/quran/root/ففروا")
    assert answer.status_code == 200 and answer.json()["root"] == "فرر"
    assert asked == ["ففروا", "فري", "فرر"]


def test_a_root_from_camel_is_settled_only_for_a_word_that_has_one():
    assert morphology.root_in_arabic("q.#.l", "قال") == "قول"
    assert morphology.root_in_arabic("q.#.l") == ""  # no lemma, no guess


@pytest.mark.skipif(morphology.get_engine_name() != "camel-tools", reason="CAMeL data not installed")
def test_the_nahw_chart_roots_weak_verbs_and_leaves_particles_rootless():
    rooted = {t["word"]: t["root"] for t in morphology.analyze_sentence("قالوا إنا لله وإنا إليه راجعون")}
    assert rooted["قالوا"] == "قول"
    assert rooted["إنا"] == "" and rooted["إليه"] == ""
    assert rooted["راجعون"] == "رجع"


def test_a_root_is_read_off_a_word_with_its_hamza_and_its_doubled_letter():
    assert arabic_text.as_root_letters("قَرَأَ") == "قرء"  # folded for searching, it had no ء: قرو
    assert arabic_text.as_root_letters("مُعْتَلّ") == "معتلل"  # a shadda is its letter twice
    assert arabic_text.as_root_letters("آتَى") == "ءتي"  # three letters: the ى is a ي
    assert arabic_text.as_root_letters("أَدْنَى") == "ءدن"  # past three it says nothing: أدنى is of د ن و


def test_a_roots_letters_count_only_in_order():
    assert arabic_text.root_letters_in_order("قول", "يقول") == 3
    assert arabic_text.root_letters_in_order("قيل", "يقول") == 2
    assert arabic_text.root_letters_in_order("رءد", "ءراد") == 2  # the أ before the ر is no third radical


def test_the_lemmas_own_letters_settle_a_weak_radical_hamza_and_all(monkeypatch):
    # Both are roots a book files, neither files قرأ itself: its ء, kept, picks.
    dictionary(monkeypatch, ("قِرَاءَة", "قرأ"), ("قَرْيَة", "قري"))
    assert roots.settle("قر#", "قَرَأ") == "قرأ"  # folded for searching, قرأ carried no ء: قري
    assert roots.settle("ر#د", "أراد") == "رود"


def test_the_root_the_lemma_is_filed_under_beats_its_letters(monkeypatch):
    # قال shows no و; يقيل (nap) would be قيل. The books file قال under قول.
    dictionary(monkeypatch, ("قَالَ", "قول"), ("زَادَ", "زيد"))
    assert roots.settle("ق#ل", "قال") == "قول"
    assert roots.settle("ز#د", "زاد") == "زيد"


def test_camels_weak_letter_can_be_the_books_other_letter(monkeypatch):
    dictionary(monkeypatch, ("مَاء", "موه"), ("دَار", "دور"), ("دَارّ", "درر"))
    assert roots.settle("م##", "ماء") == "موه"  # CAMeL has م## though its last radical is ه
    assert roots.settle("د#ر", "دار") == "دور"  # both filed, دار shows neither: و, the commoner
    assert roots.settle("د#ر", "دَارّ") == "درر"  # its shadda is the second ر


def test_a_two_letter_root_is_a_slip(monkeypatch):
    dictionary(monkeypatch, ("لَيْسَ", "ليس"))
    assert roots.settle("لس", "ليس") == "ليس"  # the lemma's own, holding CAMeL's letters
    assert roots.settle("لس") == ""
    assert morphology.root_in_arabic("l.s") == ""


def test_a_root_spelled_out_whole_is_kept_only_if_it_is_one():
    assert roots.settle("كتب", "كتب") == "كتب"
    assert roots.settle("بللّه", "الله") == ""  # a shadda is no radical: CAMeL's slip for بالله
    assert roots.settle("بنت", "بنات") == ""  # three letters no book files: بنات is of ب ن ي
    assert roots.settle("خنزر", "خنزير") == "خنزر"  # four: the books seldom list one as a root
    assert roots.settle("سفرجل", "سفرجل") == "سفرجل"  # five, a bare noun's most
    assert roots.settle("سفرجلل", "سفرجل") == ""


def rootless(monkeypatch, word: str) -> None:
    monkeypatch.setattr(morphology, "readings", lambda w: [morphology.Reading(word, "", rooted=False)] if w == word else [])


def test_a_harf_has_no_root_whatever_a_headword_spelled_alike_is_filed_under(monkeypatch):
    rootless(monkeypatch, "إنه")
    dictionary(monkeypatch, ("أَنْهِ", "نهي"))
    assert roots.roots_of("إنه") == ()


def test_a_word_the_quran_has_with_no_root_has_none(monkeypatch):
    read_as(monkeypatch, {"من": [("من", "منن")]})
    monkeypatch.setattr(quran_corpus, "root_of", lambda word: "" if word == "من" else None)
    assert roots.roots_of("من") == ()


def test_only_the_declined_noun_and_the_conjugated_verb_have_a_root():
    for pos in ("prep", "conj_sub", "part_neg", "pron", "pron_dem", "pron_rel", "verb_pseudo"):
        assert morphology.has_no_root(pos), pos
    for pos in ("verb", "noun", "adj", "noun_prop", "adv"):
        assert not morphology.has_no_root(pos), pos


def test_a_harf_reading_has_no_root_in_any_tab():
    assert morphology.reading_root({"pos": "prep", "root": "w.l.y", "lex": "إِلَى"}) == ""
    assert morphology.reading_root({"pos": "verb", "root": "q.#.l", "lex": "قال"}) == "قول"


class _Analyzer:
    def __init__(self, analyses):
        self.analyses = analyses

    def analyze(self, word):
        return list(self.analyses)


def test_camels_readings_come_likeliest_first(monkeypatch):
    # The analyzer lists them in no order: a first pick took وَتَر for يترك.
    unseen = {"lex": "وَتَر", "root": "w.t.r", "pos": "verb", "pos_lex_logprob": -99.0}
    common = {"lex": "تَرَك", "root": "t.r.k", "pos": "verb", "pos_lex_logprob": -3.1}
    rare = {"lex": "أَتْرَك", "root": "t.r.k", "pos": "verb", "pos_lex_logprob": -5.2}
    monkeypatch.setattr(morphology, "_camel_analyzer", _Analyzer([unseen, rare, common]))
    assert [a["lex"] for a in morphology._analyses("يترك")] == ["تَرَك", "أَتْرَك", "وَتَر"]
