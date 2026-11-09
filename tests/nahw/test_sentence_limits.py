"""Cost and robustness at the input edge: a sentence is capped by words, one huge word is just one gap,
and no sentence reads forever."""
import threading

import pytest
from fastapi import HTTPException

from backend.config import get_settings
from backend.services.nahw.syntax import teacher, tree
from backend.utils import arabic_sentence
from tests.nahw.test_naming import named, token
from tests.nahw_helpers import analyze, needs_parser

READ_CAP_SECONDS = 60  # each reads in under 2 s; a walk round a loop never returns


@needs_parser
@pytest.mark.parametrize("sentence", [
    "وَهُوَ اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ",  # 28:70: two repairs hung وَ and اللَّهُ on each other, and the إلا walk went round
    "هُوَ اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ",  # nearest case: no وَ, never looped
])
def test_a_loop_the_repairs_close_is_undone_before_the_next_repair_walks_it(sentence):
    analyze("بِسْمِ اللَّهِ")  # the models load outside the cap
    read = {}
    worker = threading.Thread(target=lambda: read.update(cards=analyze(sentence)["words"]), daemon=True)
    worker.start()
    worker.join(READ_CAP_SECONDS)
    assert "cards" in read, "still reading"
    assert [c["role"] for c in read["cards"]] == ["مبتدأ", "خبر", "حرف", "اسم لا", "حرف", "بدل"]


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
