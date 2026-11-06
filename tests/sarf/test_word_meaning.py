"""The model's meaning for a word is optional: no model, or a failing one, leaves the reader the table, not an error."""
import pytest

from backend.services import ai
from backend.services.sarf import morphology, word_meaning


@pytest.fixture
def model(monkeypatch):
    """A model that is reachable and answers; tests break one part at a time."""
    asked = []
    monkeypatch.setattr(morphology, "analyze_word", lambda word: {"lemma": word})
    monkeypatch.setattr(ai, "is_ai_available", lambda: True)
    monkeypatch.setattr(ai, "analyze_sarf", lambda word, tags: asked.append(word) or {"meaning": "to write"})
    return asked


def test_the_models_answer_is_passed_on(model):
    assert word_meaning.of("كتب") == {"meaning": "to write"} and model == ["كتب"]


def test_no_model_means_no_meaning_and_no_call(model, monkeypatch):
    monkeypatch.setattr(ai, "is_ai_available", lambda: False)
    assert word_meaning.of("كتب") is None and model == []


def test_a_failing_model_means_no_meaning_not_an_error(model, monkeypatch):
    def broken(word, tags):
        raise TimeoutError("slow")

    monkeypatch.setattr(ai, "analyze_sarf", broken)
    assert word_meaning.of("كتب") is None
