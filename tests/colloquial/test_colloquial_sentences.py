"""A word topic's example sentences: the spine gives each slot's English, a dialect says every one."""
from backend.services.colloquial import loader
from backend.services.colloquial.wordlist import outline_faults

KNOWN = {w: {"english": w, "group": "people"} for w in "a b c d e f g h".split()}


def _spine(sentences):
    return [{"unit": "unit-20", "lessons": [{"lesson": "lesson-01", "words": list("abcdefgh"), "sentences": sentences}]}]


def test_a_spine_sentence_uses_only_its_topic_words_and_has_a_slot_and_english():
    good = [{"slot": "one", "english": "One a.", "uses": ["a"]}]
    assert not [f for f in outline_faults(_spine(good), KNOWN) if "sentence" in f]
    bad = [{"slot": "one", "english": "One.", "uses": ["zz"]}, {"slot": "one", "english": ""}]
    said = " | ".join(outline_faults(_spine(bad), KNOWN))
    assert "uses 'zz'" in said and "slot 'one' twice" in said and "no slot or no English" in said


def test_a_dialect_says_every_sentence_slot_once_and_no_other():
    plan = {"lesson": "lesson-01", "sentences": [{"slot": "x", "english": "X."}, {"slot": "y", "english": "Y."}]}
    said, faults = loader._sentences(plan, {"sentences": [{"slot": "x", "arabic": "س", "transliteration": "s"}]})
    assert [s["slot"] for s in said] == ["x"] and said[0]["english"] == "X." and said[0]["arabic"] == "س"
    assert any("does not say the sentence 'y'" in f for f in faults)
    _, faults = loader._sentences(plan, {"sentences": [{"slot": "x"}, {"slot": "x"}, {"slot": "y"}, {"slot": "z"}]})
    assert any("'x' twice" in f for f in faults) and any("'z', which spine.json does not have" in f for f in faults)


def test_a_said_sentence_with_no_arabic_is_a_fault_even_on_a_word_list():
    faults = loader._lesson_faults({"lesson": "lesson-01", "title": "T", "sentences": [{"slot": "x", "english": "X.", "transliteration": "s"}]}, set())
    assert any("sentence 1 has no arabic" in f for f in faults)
