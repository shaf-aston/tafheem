"""Which باب a verb takes, end to end through /api/morphology.

conjugation.identify() cannot tell the six Form I babs apart from the bare
spelling alone; a named source can, and verb_forms.babs_of() is what carries
that answer from a source's own verb list into the table's form. Every
source here is a fake adapter registered in verb_sources.SOURCES, so these
tests check the merge/pick/verdict logic through the real router, never a
real dictionary or Lane; Lane's own behaviour is test_lane_source.py's job.

The one exception is test_wiktionary_adapter_folds_the_joining_alif below,
which checks the real Wiktionary adapter's own contract and so needs the real
dictionary_service index seeded, the same idiom test_root_is_searchable.py
uses for dictionary_service-level tests.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import conjugation, verb_forms, verb_sources
from backend.services import dictionary_service as service
from backend.services.verb_sources import wiktionary

client = TestClient(app)


def _sources(monkeypatch, **by_source: dict[str, list[dict]]) -> None:
    """Register one fake adapter per source named, keyed like the dictionary:
    bare letters, no shaddah, so one bucket can hold كَتَبَ and كَتَّبَ.

    A source not named here is simply absent from SOURCES, the same as a real
    adapter answering [] for every word.
    """
    monkeypatch.setattr(verb_sources, "SOURCES", {
        key: (lambda word, table=table: table.get(service.strip_diacritics(conjugation.bare(word)), []))
        for key, table in by_source.items()
    })


def test_katab_form_i_nasara(monkeypatch):
    _sources(monkeypatch, wiktionary={"كتب": [{"form": "I", "past": "كَتَبَ", "babs": ["a~u"]}]})
    verb = client.post("/api/morphology", json={"word": "كَتَبَ"}).json()["verb"]
    assert verb["form_key"] == "I-nasara"
    assert verb["readings"] == [{
        "label": "كَتَبَ · باب نَصَرَ يَنْصُرُ",
        "sources": [{"key": "wiktionary", "label": "Wiktionary", "confidence": "verified",
                      "detail": verb["readings"][0]["sources"][0]["detail"]}],
    }]


def test_samia_is_form_i_samia_not_the_bare_guess(monkeypatch):
    """Without this lookup the tab would fall back to I-nasara: the bare past
    tense سمع matches no other Form I shape uniquely, so identify() alone
    cannot rule out نصر either."""
    _sources(monkeypatch, wiktionary={"سمع": [{"form": "I", "past": "سَمِعَ", "babs": ["i~a"]}]})
    verb = client.post("/api/morphology", json={"word": "سَمِعَ"}).json()["verb"]
    assert verb["form_key"] == "I-samia"
    assert verb["readings"][0]["label"] == "سَمِعَ · باب سَمِعَ يَسْمَعُ"


def test_kattaba_is_form_ii(monkeypatch):
    """The dictionary files كَتَبَ (I) and كَتَّبَ (II) under one bare headword;
    the shaddah the reader typed picks the form."""
    _sources(monkeypatch, wiktionary={
        "كتب": [{"form": "I", "past": "كَتَبَ", "babs": ["a~u"]},
                {"form": "II", "past": "كَتَّبَ", "babs": []}],
    })
    body = client.post("/api/morphology", json={"word": "كَتَّبَ"}).json()
    assert body["verb"]["form_key"] == "II"


def test_dictionary_index_answers_the_shaddah_spelling(monkeypatch):
    """The index key carries no shaddah, so كَتَّبَ must still reach the كتب
    bucket; _pick then keeps only the Form II past."""
    entry = {"arabic": "كتب", "verbs": [
        {"form": "I", "past": "كَتَبَ", "babs": ["a~u"]},
        {"form": "II", "past": "كَتَّبَ", "babs": []},
    ]}
    monkeypatch.setattr(service, "_arabic_index", {"كتب": [entry]})
    monkeypatch.setattr(service, "_loaded", True)
    assert wiktionary.verb_forms_of("كَتَّبَ") == entry["verbs"]
    assert verb_forms.babs_of("كَتَّبَ", {"wiktionary": wiktionary.verb_forms_of})["form_key"] == "II"


def test_two_babs_are_two_readings(monkeypatch):
    _sources(monkeypatch, wiktionary={"زقم": [
        {"form": "I", "past": "زَقَمَ", "babs": ["a~u", "a~i"]},
    ]})
    verb = client.post("/api/morphology", json={"word": "زَقَمَ"}).json()["verb"]
    labels = [r["label"] for r in verb["readings"]]
    assert labels == ["زَقَمَ · باب نَصَرَ يَنْصُرُ", "زَقَمَ · باب ضَرَبَ يَضْرِبُ"]


def test_two_entries_same_bare_past_pick_by_vowel(monkeypatch):
    """بخع has two separate verb dicts, not one dict with two babs: بَخَعَ
    (a~a only) and بَخِعَ (a~a and i~a). Both strip to the same bare past, so a
    match on bare() alone would always return whichever is first regardless of
    which vowelling the reader typed."""
    _sources(monkeypatch, wiktionary={"بخع": [
        {"form": "I", "past": "بَخَعَ", "babs": ["a~a"]},
        {"form": "I", "past": "بَخِعَ", "babs": ["i~a"]},
    ]})
    verb = client.post("/api/morphology", json={"word": "بَخِعَ"}).json()["verb"]
    assert verb["form_key"] == "I-samia"
    assert len(verb["readings"]) == 1


def test_word_absent_from_every_source_has_no_readings(monkeypatch):
    _sources(monkeypatch, wiktionary={})
    body = client.post("/api/morphology", json={"word": "شَرِبَ"}).json()
    assert body["verb"]["readings"] == []
    assert body["verb"]["form_key"] is None
    # No source names a bab, and the shape alone cannot either: no table, and
    # the note says so instead of falling back to a guessed default.
    assert body["form"] is None
    assert body["table"] is None
    assert "No dictionary" in body["table_note"]


def test_form_still_resolves_from_shape_when_no_source_answers(monkeypatch):
    """A four-letter verb absent from every source is still IQ by its shape;
    identify() does not need a dictionary at all for a form this unambiguous."""
    _sources(monkeypatch, wiktionary={})
    body = client.post("/api/morphology", json={"word": "زهزه"}).json()
    assert body["verb"]["readings"] == []
    assert body["form"] == "IQ"


def test_request_form_wins_over_the_dictionary(monkeypatch):
    _sources(monkeypatch, wiktionary={"كتب": [{"form": "I", "past": "كَتَبَ", "babs": ["a~u"]}]})
    body = client.post("/api/morphology", json={"word": "كَتَبَ", "form": "II"}).json()
    assert body["form"] == "II"


def test_form_ix_has_no_form_key_but_still_labels_and_does_not_crash(monkeypatch):
    """Form IX is not one of the six Form I babs and has no table in
    conjugation.forms() either, so form_key stays None and the label falls
    back to "Form IX". The made-up spelling below is not a real root the
    tagger can resolve, so radicals_of() falls back to the whole word's six
    letters, guaranteeing the table itself is refused independently of the
    verb verdict; this proves that refusal cannot crash the response."""
    word = "زخفضلن"
    _sources(monkeypatch, wiktionary={conjugation.bare(word): [
        {"form": "IX", "past": word, "babs": []},
    ]})
    body = client.post("/api/morphology", json={"word": word}).json()
    assert body["verb"]["form_key"] is None
    assert body["verb"]["readings"][0]["label"] == f"{word} · Form IX"
    assert body["table_note"] is not None


def test_wiktionary_adapter_folds_the_joining_alif(monkeypatch):
    """ٱجْتَمَعَ typed with the joining alif must still find the entry stored
    under the plain alif, اِجْتَمَعَ: conjugation.bare() folds both to the
    same letters, where strip_diacritics() left the joining alif in place and
    the two spellings compared unequal."""
    entry = {"arabic": "اِجْتَمَعَ", "verbs": [{"form": "VIII", "past": "اِجْتَمَعَ", "babs": []}]}
    index = {service.strip_diacritics(entry["arabic"]): [entry]}
    monkeypatch.setattr(service, "_arabic_index", index)
    monkeypatch.setattr(service, "_loaded", True)
    assert wiktionary.verb_forms_of("ٱجْتَمَعَ") == entry["verbs"]
