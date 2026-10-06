"""Cost and robustness at the input edge: a sentence is capped by words, and one huge word is just one gap."""
import pytest
from fastapi import HTTPException

from backend.config import get_settings
from backend.services.syntax import naming, teacher, tree
from backend.utils import arabic_sentence
from tests.test_naming import token


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
    found = teacher.review([word], toks, naming.roles([word], toks))
    drawn = tree.build([word], toks, found)
    assert len(found) == 1 and drawn["words"] == [word]
