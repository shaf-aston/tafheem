"""Loading the CATiB parser: once, whole, and honestly reported.

The load takes seconds, so the second sentence always arrives while the first
is still loading. It used to load everything again beside the first, and a
request in between found the encoder set but no disambiguator, crashed on None
and fell back to the rule engine without a word. The real load is faked here,
so these run without the model files.
"""
import threading
import time

import pytest

from backend.services.syntax import catib_onnx


class _Disambiguator:
    def disambiguate(self, words):
        return []


@pytest.fixture
def fresh(monkeypatch):
    monkeypatch.setattr(catib_onnx, "_parser", None)
    monkeypatch.setattr(catib_onnx, "_load_error", "")
    monkeypatch.setattr(catib_onnx, "_load_lock", threading.Lock())
    return monkeypatch


def test_overlapping_requests_share_one_load(fresh):
    loads = []

    def slow_load():
        loads.append(1)
        time.sleep(0.3)
        return catib_onnx._Parser({}, [], [], None, object(), object(), None, _Disambiguator())

    fresh.setattr(catib_onnx, "_load", slow_load)
    failures = []

    def request(delay):
        time.sleep(delay)
        try:
            catib_onnx.warm()
            catib_onnx._parser.disambiguator.disambiguate(["x"])
        except Exception as exc:  # the old crash: 'NoneType' has no 'disambiguate'
            failures.append(exc)

    threads = [threading.Thread(target=request, args=(d,)) for d in (0, 0.05, 0.15)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert failures == []
    assert len(loads) == 1
    assert catib_onnx.state() == "ready"


def test_failed_load_is_kept_and_reported_not_retried(fresh):
    calls = []

    def broken_load():
        calls.append(1)
        raise ImportError("no module named transformers")

    fresh.setattr(catib_onnx, "_load", broken_load)
    for _ in range(3):
        with pytest.raises(Exception):
            catib_onnx.warm()

    assert len(calls) == 1
    assert catib_onnx.state().startswith("failed: ImportError")
    assert catib_onnx._parser is None


def test_not_loaded_until_asked(fresh):
    assert catib_onnx.state() == "not loaded"
