"""The Basics world's verbs (frontend/public/grow/basics-verbs.json).

The shipped file must be what the engine makes from data/grow/basics_verbs.json today, each
verb's باب must be the one the dictionaries give it, and every form must have the shape its
mood demands, since the quiz's wrong options are these same forms.
"""
from __future__ import annotations

import json
import re

import pytest

from backend.scripts.grow import build_basics_verbs as B
from backend.services.sarf import verb_forms

SOURCE = json.loads(B.SOURCE.read_text(encoding="utf-8"))
SHIPPED = json.loads(B.OUT.read_text(encoding="utf-8"))
VERBS = SHIPPED["verbs"]
IDS = [verb["id"] for verb in VERBS]

FATHA, DAMMA, SUKUN = "َ", "ُ", "ْ"
MARKS = re.compile("[ً-ْ]")


def test_the_shipped_file_is_a_fresh_build():
    assert B.OUT.read_text(encoding="utf-8") == B.text(B.build(SOURCE))


def test_every_verb_has_its_seven_persons():
    assert SHIPPED["persons"] == ["he", "she", "they", "you", "you-all", "I", "we"]
    for verb in VERBS:
        assert list(verb["forms"]) == SHIPPED["persons"], verb["id"]
        for person, forms in verb["forms"].items():
            wanted = {"past", "present", "subj", "juss"} | ({"command"} if person in B.ADDRESSED else set())
            assert set(forms) == wanted, (verb["id"], person)


@pytest.mark.parametrize("verb", VERBS, ids=IDS)
def test_the_bab_is_the_dictionaries(verb):
    assert verb_forms.babs_of(verb["root"])["form_key"] == verb["bab"]


@pytest.mark.parametrize("verb", VERBS, ids=IDS)
def test_every_form_holds_the_root_in_order(verb):
    for person, forms in verb["forms"].items():
        for mood, form in forms.items():
            letters = MARKS.sub("", form)
            assert re.search(".*".join(verb["root"]), letters), (verb["id"], person, mood, form)


@pytest.mark.parametrize("verb", VERBS, ids=IDS)
def test_each_mood_ends_as_it_should(verb):
    forms = verb["forms"]
    for person in ("he", "she", "you", "I", "we"):
        assert forms[person]["present"].endswith(DAMMA)
        assert forms[person]["subj"] == forms[person]["present"][:-1] + FATHA
        assert forms[person]["juss"].endswith(SUKUN)
    for person in ("they", "you-all"):
        assert forms[person]["present"].endswith("ونَ")
        assert forms[person]["subj"] == forms[person]["juss"] == forms[person]["present"][:-2] + "ا"
    assert forms["you"]["command"].startswith("ا") and forms["you"]["command"].endswith(SUKUN)
    assert forms["you-all"]["command"].endswith("وا")


def test_the_english_is_three_plain_forms():
    for verb in SOURCE["verbs"]:
        assert set(verb["en"]) == {"base", "past", "s3"}, verb["id"]
        for form in verb["en"].values():
            assert re.fullmatch("[a-z]+( [a-z]+)?", form), (verb["id"], form)
    assert len(set(IDS)) == len(IDS)
