"""Smoke tests for the torch-free CATiB parser (backend/services/syntax/catib_onnx.py).

Skips cleanly, rather than failing, when the model files have not been
dropped into backend/data/parser/ (see catib_onnx.py's docstring).
"""
import pytest

from backend.services.syntax.catib_onnx import _files_present, parse

pytestmark = pytest.mark.skipif(
    not _files_present(), reason="CATiB parser model files not present under backend/data/parser/"
)


def test_verb_subject_object():
    tokens = parse(["كَتَبَ", "الطَّالِبُ", "رِسَالَةً"])
    by_form = {t["form"]: t for t in tokens}

    verb = by_form["كتب"]
    assert verb["head"] == 0, "the verb should be the sentence root"

    subject = by_form["الطالب"]
    assert tokens[subject["id"] - 1]["head"] == verb["id"]
    assert subject["rel"] == "SBJ"

    obj = by_form["رسالة"]
    assert tokens[obj["id"] - 1]["head"] == verb["id"]
    assert obj["rel"] == "OBJ"


def test_empty_input_returns_empty_list():
    assert parse([]) == []
