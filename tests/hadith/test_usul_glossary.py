"""The usul glossary: every fault the checker names, the real file being sound, and the API carrying kids/confuse/answers."""

from backend.models.hadith import GlossaryGroup
from backend.services.hadith.usul import store

KINDS = {"daif": {}}


def term(ar, **more):
    return {"ar": ar, "en": ar, "say": "s", "quote": "q", "book": "taqrib", "page": "PageV01P001", **more}


def group(*terms, **more):
    return {"title": "G", "ar": "ج", "terms": list(terms), **more}


def test_duplicate_name_anywhere_in_the_tree():
    assert store.glossary_faults([group(term("أ", kids=[term("ب")])), group(term("ب"))], KINDS)


def test_confuse_must_name_a_term():
    assert store.glossary_faults([group(term("أ", confuse=[{"ar": "ز", "why": "w"}]))], KINDS)


def test_kind_must_be_a_ruling_kind():
    assert store.glossary_faults([group(term("أ", kind="nope"))], KINDS)


def test_answer_must_be_on_a_group_axis():
    assert store.glossary_faults([group(term("أ", answers={"x": "t"}), axes=[{"id": "y", "q": "?"}])], KINDS)


def test_sound_tree_has_no_faults():
    g = group(term("أ", kind="daif", answers={"y": "t"}, confuse=[{"ar": "ب", "why": "w"}], kids=[term("ب")]),
              axes=[{"id": "y", "q": "?"}])
    assert store.glossary_faults([g], KINDS) == []


def test_real_file_has_no_faults():
    cfg = store.rule()
    assert store.glossary_faults(cfg["glossary"], cfg["rulings"]["kinds"]) == []


def test_api_shape_carries_new_fields(monkeypatch):
    g = group(term("أ", lugha="l", kind="daif", answers={"y": "t"}, confuse=[{"ar": "ب", "why": "w"}], kids=[term("ك")]),
              term("ب"), by="what?", axes=[{"id": "y", "q": "?"}])
    monkeypatch.setattr(store, "rule", lambda: {"glossary": [g], "rulings": {"kinds": KINDS}, "sources": {"taqrib": {"label": "Taqrib"}}})
    store._glossary_sound.cache_clear()
    try:
        out = store.glossary()
    finally:
        store._glossary_sound.cache_clear()
    model = GlossaryGroup(**out[0])
    first = model.terms[0]
    assert (model.by, model.axes[0].q) == ("what?", "?")
    assert (first.lugha, first.kind, first.answers) == ("l", "daif", {"y": "t"})
    assert (first.meaning, first.quote, first.page) == ("s", "q", "p. 1")
    assert first.confuse[0].arabic == "ب" and first.kids[0].arabic == "ك"


def test_rejected_is_one_group_split_as_nuzha_splits_it():
    """A gap you can see or hidden, and the ten causes of a fault: five of integrity, five of precision."""
    groups = {g["title"]: g for g in store.glossary()}
    assert "A gap in the chain" not in groups and "A fault in a narrator" not in groups
    branches = {t["arabic"]: [k["arabic"] for k in t["kids"]] for t in groups["Rejected"]["terms"]}
    assert list(branches) == ["الضعيف", "السقط الواضح", "السقط الخفي", "العدالة", "الضبط"]
    assert {"الموضوع", "المتروك", "الفاسق", "المبتدع", "المبهم"} == set(branches["العدالة"])
    assert {"سيئ الحفظ", "المختلط"} <= set(branches["الضبط"])
