"""Two words of one topic never look the same to a learner (wordlist.bank)."""
from backend.services.colloquial import wordlist


def _bank(said, same=frozenset()):
    ids = list(said)
    known = {i: {"english": i, "group": "food"} for i in ids}
    real = wordlist.meanings
    wordlist.meanings = lambda: known
    try:
        return wordlist.bank(ids, said, "lesson 'x'", same)[1]
    finally:
        wordlist.meanings = real


def test_the_same_letters_without_vowel_marks_are_one_word_to_the_eye():
    faults = _bank({"food": {"arabic": "اكل", "transliteration": "akl"}, "to-eat": {"arabic": "أكل", "transliteration": "akal"}})
    assert any("looks the same as 'food'" in f for f in faults)


def test_vowel_marks_that_differ_tell_them_apart():
    assert not _bank({"food": {"arabic": "أَكْل", "transliteration": "akl"}, "to-eat": {"arabic": "أَكَل", "transliteration": "akal"}})


def test_the_same_marks_on_the_same_letters_are_still_one_word():
    faults = _bank({"kofta": {"arabic": "كُفْتَة", "transliteration": "kofta"}, "meatballs": {"arabic": "كُفْتَة", "transliteration": "kofta"}})
    assert faults


def test_a_listed_homonym_may_share_its_letters():
    said = {"north": {"arabic": "شمال", "transliteration": "shimaal"}, "left": {"arabic": "شمال", "transliteration": "shimaal"}}
    assert _bank(said)
    assert not _bank(said, frozenset({frozenset({"north", "left"})}))


def test_a_womans_form_is_compared_too():
    faults = _bank({"teacher": {"arabic": "مدرس / مدرسة", "transliteration": "mudarris / mudarrisa"},
                    "school": {"arabic": "مدرسة", "transliteration": "madrasa"}})
    assert any("looks the same as 'teacher'" in f for f in faults)
