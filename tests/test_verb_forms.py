"""Protects the bab parser: the Wiktionary template grammar, which past matches
which entry, and the reading/merge rules the router relies on.
"""
from __future__ import annotations

from backend.services import conjugation, verb_forms


def test_plain_form_and_vowels():
    assert verb_forms.parse_head("I/a~u") == ("I", ["a~u"])


def test_tags_after_the_dot_are_ignored():
    assert verb_forms.parse_head("I/a~u.pass.vn:كِتَابَة,كَتْب") == ("I", ["a~u"])


def test_present_alternates_expand():
    assert verb_forms.parse_head("I/a~u,i") == ("I", ["a~u", "a~i"])


def test_past_alternates_expand():
    assert verb_forms.parse_head("I/a,i~a") == ("I", ["a~a", "i~a"])


def test_both_sides_expand_as_a_cartesian_product_past_major():
    assert verb_forms.parse_head("I/a~a,i,u") == ("I", ["a~a", "a~i", "a~u"])


def test_bare_form_has_no_known_vowels():
    assert verb_forms.parse_head("I") == ("I", [])


def test_mazid_form_has_no_slash():
    assert verb_forms.parse_head("II") == ("II", [])
    assert verb_forms.parse_head("IV") == ("IV", [])


def test_quadriliteral_codes_map_to_patterns_json_spelling():
    assert verb_forms.parse_head("Iq") == ("IQ", [])
    assert verb_forms.parse_head("IIq") == ("IIQ", [])


def test_higher_mazid_forms_pass_through():
    assert verb_forms.parse_head("IX") == ("IX", [])
    assert verb_forms.parse_head("XII") == ("XII", [])


def test_garbage_before_the_form_is_rejected():
    assert verb_forms.parse_head("ضربI/a~i") is None


def test_garbage_form_letters_are_rejected():
    assert verb_forms.parse_head("Iassimilated/i~a") is None


def test_empty_string_is_rejected():
    assert verb_forms.parse_head("") is None


VERBS = [
    {"form": "I", "past": "كَتَبَ", "babs": ["a~u"]},
    {"form": "II", "past": "كَتَّبَ", "babs": []},
]


def test_pick_chooses_form_i_over_form_ii_by_shaddah():
    assert verb_forms._pick(VERBS, "كتب") == [VERBS[0]]
    assert verb_forms._pick(VERBS, "كتّب") == [VERBS[1]]


def test_pick_returns_empty_when_no_past_matches():
    assert verb_forms._pick(VERBS, "زهزه") == []


def test_pick_exact_vowelled_spelling_beats_a_shared_bare_past():
    """بَخَعَ and بَخِعَ strip to the same bare past; a fully vowelled typed
    word must only match its own entry, not both."""
    verbs = [
        {"form": "I", "past": "بَخَعَ", "babs": ["a~a"]},
        {"form": "I", "past": "بَخِعَ", "babs": ["i~a"]},
    ]
    assert verb_forms._pick(verbs, "بَخِعَ") == [verbs[1]]
    assert verb_forms._pick(verbs, "بخع") == verbs


def test_verdict_one_bab():
    result = verb_forms._verdict([([VERBS[0]], "wiktionary")])
    assert result == {
        "form_key": "I-nasara",
        "readings": [{"label": "كَتَبَ · باب نَصَرَ يَنْصُرُ", "source_keys": ["wiktionary"]}],
    }


def test_verdict_two_babs_are_two_readings():
    verb = {"form": "I", "past": "سَمِعَ", "babs": ["i~a", "i~i"]}
    result = verb_forms._verdict([([verb], "wiktionary")])
    assert result["form_key"] == "I-samia"
    labels = [r["label"] for r in result["readings"]]
    assert labels == ["سَمِعَ · باب سَمِعَ يَسْمَعُ", "سَمِعَ · باب حَسِبَ يَحْسِبُ"]


def test_verdict_form_i_with_no_bab_named_yields_no_reading():
    verb = {"form": "I", "past": "كَتَبَ", "babs": []}
    result = verb_forms._verdict([([verb], "wiktionary")])
    assert result == {"form_key": None, "readings": []}


def test_verdict_mazid_form_ii():
    verb = {"form": "II", "past": "كَتَّبَ", "babs": []}
    result = verb_forms._verdict([([verb], "wiktionary")])
    assert result["form_key"] == "II"
    assert result["readings"][0]["label"] == f"كَتَّبَ · {conjugation.forms()['II']}"


def test_verdict_mazid_form_ix_has_no_form_key_but_keeps_the_label():
    verb = {"form": "IX", "past": "اِحْمَرَّ", "babs": []}
    result = verb_forms._verdict([([verb], "wiktionary")])
    assert result["form_key"] is None
    assert result["readings"][0]["label"] == "اِحْمَرَّ · Form IX"


def test_verdict_no_verb_found_is_empty():
    assert verb_forms._verdict([]) == {"form_key": None, "readings": []}


def test_verdict_merges_identical_labels_from_two_sources_in_babs_order():
    verb = {"form": "I", "past": "كَتَبَ", "babs": ["a~u"]}
    result = verb_forms._verdict([([verb], "lane"), ([verb], "wiktionary")])
    assert len(result["readings"]) == 1
    assert result["readings"][0]["source_keys"] == ["lane", "wiktionary"]


def test_verdict_keeps_disagreeing_babs_as_separate_readings():
    lane_verb = {"form": "I", "past": "زَقَمَ", "babs": ["a~u"]}
    wiki_verb = {"form": "I", "past": "زَقَمَ", "babs": ["a~i"]}
    result = verb_forms._verdict([([lane_verb], "lane"), ([wiki_verb], "wiktionary")])
    assert len(result["readings"]) == 2
    assert result["readings"][0]["source_keys"] == ["lane"]
    assert result["readings"][1]["source_keys"] == ["wiktionary"]


def test_babs_of_merges_across_sources(monkeypatch):
    """babs_of() reads verb_sources.SOURCES at call time, so a test can swap
    it for tiny in-memory adapters without touching either real source."""
    verb = {"form": "I", "past": "كَتَبَ", "babs": ["a~u"]}
    result = verb_forms.babs_of("كَتَبَ", sources={
        "lane": lambda word: [verb],
        "wiktionary": lambda word: [],
    })
    assert result["form_key"] == "I-nasara"
    assert result["readings"][0]["source_keys"] == ["lane"]


def test_record_maps_quadriliteral_form_and_drops_unknown_babs():
    assert verb_forms.record("Iq", "زَهْزَهَ", []) == {"form": "IQ", "past": "زَهْزَهَ", "babs": []}
    assert verb_forms.record("I", "كَتَبَ", ["a~u", "z~z"]) == {"form": "I", "past": "كَتَبَ", "babs": ["a~u"]}


def test_record_rejects_garbage_form():
    assert verb_forms.record("assimilated", "كَتَبَ", []) is None


def test_record_rejects_form_i_whose_only_bab_is_unknown():
    assert verb_forms.record("I", "كَتَبَ", ["z~z"]) is None


def test_every_bab_source_is_registered_and_credited():
    """A source babs.json names but nobody wired, or nobody credits, is a
    reading with no way to say where it came from."""
    from backend.services import provenance, verb_sources

    named = set(conjugation.babs()["sources"])
    credited = {row["key"] for row in provenance.all_sources()}
    assert named <= verb_sources.SOURCES.keys()
    assert named <= credited
