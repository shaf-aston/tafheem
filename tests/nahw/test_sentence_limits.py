"""Cost and robustness at the input edge: a sentence is capped by words, and one huge word is just one gap."""
import pytest
from fastapi import HTTPException

from backend.config import get_settings
from backend.services.nahw.syntax import teacher, tree
from backend.utils import arabic_sentence
from tests.nahw.test_naming import named, token


def test_a_sentence_over_the_word_limit_is_refused_and_the_limit_itself_is_allowed():
    limit = get_settings().max_sentence_words
    assert len(arabic_sentence(" ".join(["كتب"] * limit)).split()) == limit
    with pytest.raises(HTTPException) as refused:
        arabic_sentence(" ".join(["كتب"] * (limit + 1)))
    assert refused.value.status_code == 422


def test_the_default_limit_is_160_words():
    assert get_settings().max_sentence_words == 160


def test_a_single_thousand_letter_word_passes_the_gate_and_is_named_a_gap_not_a_crash():
    word = "ك" * 1000
    assert arabic_sentence(word) == word
    toks = [token(1, word, word, "NOM", 0, "---", stt="i", cas="n")]
    found = teacher.review([word], toks, named([word], toks))
    drawn = tree.build([word], toks, found)
    assert len(found) == 1 and drawn["words"] == [word]


@pytest.mark.parametrize("text", ["،", "١٢٣", "ـ", "﴿"])
def test_arabic_script_with_no_word_in_it_is_refused_not_a_crash(text):
    with pytest.raises(HTTPException) as refused:
        arabic_sentence(text)
    assert refused.value.status_code == 422


def test_a_failed_read_is_read_again_next_time_not_remembered(monkeypatch):
    from backend.services.nahw import iraab, syntax
    calls = []

    def fails_once(sentence, picks):
        # no parser model needed: the first read breaks, the second comes back whole
        calls.append(sentence)
        return {"roles": [{"role": None, "case": None} for _ in picks], "tree": None, "failed": len(calls) == 1}

    monkeypatch.setattr(syntax, "read", fails_once)
    iraab._kept.cache_clear()
    assert iraab.analyze("كَتَبَ زَيْدٌ", recorded=False)["read_failed"]
    assert not iraab.analyze("كَتَبَ زَيْدٌ", recorded=False)["read_failed"]
    assert len(calls) == 2
