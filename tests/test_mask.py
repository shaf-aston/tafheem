"""The book's vetoes over the parser's scores: pure, so no model is needed."""
import numpy as np

from backend.services.syntax.mask import book_mask

LABELS = ["<bos>", "---", "IDF", "MOD", "OBJ", "PRD", "SBJ", "TMZ", "TPC"]


def tok(pos, **feats):
    return {"pos": pos, "pos_camel": "noun", "case": None, **feats}


def allowed(toks, dep, head, label):
    _, rel_ok = book_mask(toks, LABELS)
    return bool(rel_ok[dep, head, LABELS.index(label)])


def test_a_noun_before_its_verb_cannot_be_its_subject_or_object():
    toks = [tok("NOM"), tok("VRB")]
    for label in ("SBJ", "OBJ", "MOD"):
        assert not allowed(toks, 1, 2, label)
    assert allowed(toks, 1, 2, "TPC")


def test_the_subject_after_its_verb_is_untouched():
    toks = [tok("VRB"), tok("NOM")]
    assert allowed(toks, 2, 1, "SBJ")


def test_a_typed_fatha_keeps_the_fronted_object_open_and_a_pronoun_is_not_a_noun():
    assert allowed([tok("NOM", case="a"), tok("VRB")], 1, 2, "OBJ")
    assert allowed([tok("NOM", pos_camel="pron"), tok("VRB")], 1, 2, "SBJ")


def test_mask_shapes():
    arc_ok, rel_ok = book_mask([tok("NOM"), tok("VRB")], LABELS)
    assert arc_ok.shape == (3, 3) and rel_ok.shape == (3, 3, len(LABELS))
