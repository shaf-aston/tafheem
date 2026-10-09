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
from backend.services import dictionary_service, morphology, quran_corpus, roots, sarf_word
from backend.services.daleel.lexicon import DictionaryLexicon


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    """No dictionary and no corpus unless a test gives one; nothing remembered between tests."""
    monkeypatch.setattr(dictionary_service, "_dictionary", [])
    monkeypatch.setattr(dictionary_service, "_arabic_index", {})
    monkeypatch.setattr(dictionary_service, "_loaded", True)
    monkeypatch.setattr(quran_corpus, "root_of", lambda word: "")
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
    monkeypatch.setattr(morphology, "readings", lambda word: table.get(word, []))


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
    monkeypatch.setattr(quran_corpus, "root_of", lambda word: "قول" if word == "قالوا" else "")
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
