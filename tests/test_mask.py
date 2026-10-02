"""The book's vetoes over the parser's scores: pure, so no model is needed."""
import numpy as np

from backend.services.syntax.mask import book_links, book_mask

LABELS = ["<bos>", "---", "IDF", "MOD", "OBJ", "PRD", "SBJ", "TMZ", "TPC"]


def tok(pos, **feats):
    return {"pos": pos, "pos_camel": "noun", "case": None, **feats}


def allowed(toks, dep, head, label):
    rel_ok = book_mask(toks, LABELS)
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
    assert book_mask([tok("NOM"), tok("VRB")], LABELS).shape == (3, 3, len(LABELS))


def test_a_pointer_takes_its_nouns_place_and_the_noun_hangs_on_it():
    # قرأتُ هذا الكتابَ, drawn by the parser with the pointer under the noun
    toks = [tok("VRB", pos_camel="verb"), tok("NOM", pos_camel="pron_dem"), tok("NOM", stt="d")]
    heads, rels = book_links(toks, [0, 3, 1], ["---", "MOD", "OBJ"])
    assert (heads, rels) == ([0, 1, 2], ["---", "OBJ", "MOD"])


def test_a_pointer_before_an_indefinite_noun_is_left_alone():
    # هذا كتابٌ: a whole sentence, the noun its khabar
    toks = [tok("NOM", pos_camel="pron_dem"), tok("NOM", stt="i")]
    assert book_links(toks, [2, 0], ["SBJ", "---"]) == ([2, 0], ["SBJ", "---"])


def test_a_pointer_already_heading_its_noun_is_unchanged():
    toks = [tok("NOM", pos_camel="pron_dem"), tok("NOM", stt="d"), tok("NOM", stt="i")]
    assert book_links(toks, [3, 1, 0], ["SBJ", "MOD", "---"]) == ([3, 1, 0], ["SBJ", "MOD", "---"])
