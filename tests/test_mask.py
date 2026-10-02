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


def test_a_listed_preposition_takes_the_next_word_in_jarr():
    # رُبَّ رَجُلٍ, tagged a noun by the parser
    toks = [tok("NOM", form="رب"), tok("NOM", form="رجل", cas="g", stt="i")]
    assert book_links(toks, [0, 0], ["---", "MOD"]) == ([0, 1], ["---", "OBJ"])
    assert toks[0]["pos"] == "PRT"


def test_before_a_noun_with_al_the_listed_word_is_a_mudaf():
    # رَبِّ الْعَالَمِينَ: رُبَّ takes an indefinite noun, so this رب is a noun
    toks = [tok("NOM", form="رب", stt="c"), tok("NOM", form="العالمين", cas="g", stt="d")]
    assert book_links(toks, [0, 1], ["---", "IDF"]) == ([0, 1], ["---", "IDF"])
    assert toks[0]["pos"] == "NOM"


def test_a_pronoun_on_the_same_word_is_no_majrur():
    # اُدْعُ رَبَّكَ: the كَ is the word's own, so رَبّ stays a noun
    toks = [tok("VRB", form="أدع"), tok("NOM", form="رب"), tok("NOM", pos_camel="pron", form="+ك", cas="g")]
    assert book_links(toks, [0, 1, 2], ["---", "OBJ", "IDF"]) == ([0, 1, 2], ["---", "OBJ", "IDF"])
    assert toks[1]["pos"] == "NOM"


def test_a_noun_before_its_verb_carries_the_verb():
    # الولدُ يكتبُ, drawn with the noun under its verb as a bare topic
    toks = [tok("NOM", stt="d"), tok("VRB", pos_camel="verb")]
    assert book_links(toks, [2, 0], ["---", "---"]) == ([0, 1], ["---", "---"])
    # الطعامَ أكل الولدُ: a noun in nasb before the verb is its fronted object, left alone
    toks[0]["case"] = "a"
    assert book_links(toks, [2, 0], ["---", "---"]) == ([2, 0], ["---", "---"])


def inner(first_pos="PROP", first_camel="noun_prop", khabar_case="n"):
    # زيدٌ أبوه عالمٌ: noun, noun + its pronoun, an indefinite noun
    return [tok(first_pos, pos_camel=first_camel, stt="i", form="زيد"),
            tok("NOM", stt="c", cas="n", form="أبو"),
            tok("NOM", pos_camel="pron", stt="d", cas="g", form="+ه"),
            tok("NOM", stt="i", cas=khabar_case, form="عالم")]


def test_a_noun_with_its_pronoun_and_a_khabar_is_a_sentence_inside_the_sentence():
    # the parser's own drawing: أبو a صفة of زيد, زيد under عالم
    heads, rels = book_links(inner(), [4, 1, 2, 0], ["SBJ", "MOD", "IDF", "---"])
    assert (heads, rels) == ([0, 4, 2, 1], ["---", "SBJ", "IDF", "PRD"])


def test_a_noun_with_its_pronoun_then_a_nasb_noun_is_no_sentence():
    # زيدٌ أبوه عالمًا is no khabar sentence: the third noun is not in raf'
    assert book_links(inner(khabar_case="a"), [4, 1, 2, 0], ["SBJ", "MOD", "IDF", "---"]) == (
        [4, 1, 2, 0], ["SBJ", "MOD", "IDF", "---"])


def test_after_a_relative_the_inner_sentence_is_its_sila():
    # جاء الذي أبوه عالمٌ: the relative keeps its place, the sentence hangs on it
    toks = [tok("VRB", pos_camel="verb")] + inner("NOM", "pron_rel")
    heads, rels = book_links(toks, [0, 1, 5, 3, 2], ["---", "SBJ", "SBJ", "IDF", "MOD"])
    assert (heads, rels) == ([0, 1, 5, 3, 2], ["---", "SBJ", "SBJ", "IDF", "PRD"])
