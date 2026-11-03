"""A verb typed without harakat is read active or passive by guess: the card says so, and its nouns
say their jobs rest on it. Typed vowels that settle the voice leave no flag."""
import re

from backend.scripts.nahw.score_iraab import fresh_sentences, routed
from backend.services.text.arabic_text import words


def cards(sentence: str) -> list[dict]:
    return routed(sentence, None)["words"]


def test_a_bare_verb_says_it_was_read_active_and_its_noun_says_its_job_depends_on_it():
    verb, noun = cards("كتب الدرس")
    assert verb["role"] == "فعل" and verb["assumed"] == {"vox": "p"}
    assert "passive" in verb["notes"] and "لعدم كتابة الحركات" in verb["reason"]
    assert noun["assumed"] == {"via": 0} and "«كتب»" in noun["reason"]


def test_a_typed_vowel_that_rules_the_other_voice_out_leaves_no_flag():
    for sentence in ("كَتَبَ الدَّرْسَ", "كَتَبَ الدرس", "كُتِبَ الدرس"):
        assert not any(card["assumed"] for card in cards(sentence)), sentence


def test_the_vowelled_fresh_sentences_carry_no_flag():
    vowelled = [row for row in fresh_sentences() if all(re.search("[ً-ْ]", w) for w in words(row["sentence"]))][:40]
    assert len(vowelled) == 40
    assert [row["id"] for row in vowelled if any(c["assumed"] for c in cards(row["sentence"]))] == []
