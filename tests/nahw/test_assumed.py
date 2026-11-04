"""A verb typed without harakat is read active or passive by guess: the card says so, and a noun whose job
is another in the other reading says what it would be. Typed vowels that settle the voice leave no flag."""
import re

from backend.scripts.nahw.score_iraab import fresh_sentences, routed
from backend.services.text.arabic_text import words


def cards(sentence: str) -> list[dict]:
    return routed(sentence, None)["words"]


def test_a_bare_verb_says_it_was_read_active_and_its_noun_says_its_job_depends_on_it():
    verb, noun = cards("كتب الدرس")
    assert verb["role"] == "فعل" and verb["assumed"] == {"vox": "p"}
    assert "passive" in verb["notes"] and "لعدم كتابة الحركات" in verb["reason"]
    assert noun["assumed"] == {"other": "نائب فاعل", "if": 0} and "«كتب»" in noun["reason"]


def test_a_typed_vowel_that_rules_the_other_voice_out_leaves_no_flag():
    for sentence in ("كَتَبَ الدَّرْسَ", "كَتَبَ الدرس", "كُتِبَ الدرس"):
        assert not any(card["assumed"] for card in cards(sentence)), sentence


def test_the_vowelled_fresh_sentences_carry_no_flag():
    vowelled = [row for row in fresh_sentences() if all(re.search("[ً-ْ]", w) for w in words(row["sentence"]))][:40]
    assert len(vowelled) == 40
    assert [row["id"] for row in vowelled if any(c["assumed"] for c in cards(row["sentence"]))] == []


def test_a_verb_the_dictionary_has_no_passive_for_still_names_the_other_voice_on_its_noun():
    verb, noun = cards("شيدت الجسور فوق النهر")[:2]  # the dictionary lacks شُيِّدَتْ: sarf's table has it
    assert verb["assumed"] == {"vox": "p"}
    assert noun["role"] == "فاعل" and noun["assumed"] == {"other": "نائب فاعل", "if": 0}


def test_a_bare_word_that_is_a_noun_or_a_particle_names_the_job_the_other_reading_gives_it():
    shown = cards("قام الطلاب سوى علي")  # علي the name, or على with my ي
    assert shown[3]["role"] == "حرف جر" and shown[3]["assumed"] == {"other": "مضاف إليه", "if": 3}
    assert "«علي»" in shown[3]["reason"]


def test_a_verb_that_takes_no_object_is_not_read_passive_on_a_guess():
    assert not any(card["assumed"] for card in cards("ذهب الولد"))
