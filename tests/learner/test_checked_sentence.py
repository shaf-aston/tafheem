"""When a checked sentence is refused, below the route: the learnt-word minimum comes before the model is asked."""
import pytest

from backend.services import ai
from backend.services.learner import attempts, checked_sentence
from backend.services.learner.checked_sentence import Refused


@pytest.fixture
def learnt(monkeypatch):
    """A learner with `n` learnt words and a model that must be told apart from 'not asked'."""
    asked = []
    monkeypatch.setattr(ai, "is_ai_available", lambda: True)
    monkeypatch.setattr(ai, "checked_sentence", lambda given, ok: asked.append(given) or {"ar": "x", "en": "y"})

    def set_words(n):
        monkeypatch.setattr(attempts, "summary", lambda module, user: [{"item": f"w{i}", "known": True} for i in range(n)])
        monkeypatch.setattr(checked_sentence.sentence_check, "learnt_words", lambda rows: [{"ar": f"ك{i}"} for i in range(len(rows))])

    return asked, set_words


def test_too_few_learnt_words_is_refused_before_the_model_is_asked(learnt):
    asked, set_words = learnt
    set_words(1)
    assert checked_sentence.make("amina") is Refused.TOO_FEW and asked == []


def test_enough_words_but_no_model_is_refused_and_a_model_that_finds_nothing_is_failed(learnt, monkeypatch):
    asked, set_words = learnt
    set_words(50)
    monkeypatch.setattr(ai, "is_ai_available", lambda: False)
    assert checked_sentence.make("amina") is Refused.NO_AI and asked == []
    monkeypatch.setattr(ai, "is_ai_available", lambda: True)
    monkeypatch.setattr(ai, "checked_sentence", lambda given, ok: None)
    assert checked_sentence.make("amina") is Refused.FAILED


def test_a_sentence_comes_back_with_the_words_it_was_asked_to_use(learnt):
    asked, set_words = learnt
    set_words(50)
    done = checked_sentence.make("amina")
    assert done["ar"] == "x" and done["words"] == asked[0] and len(asked[0]) > 0
