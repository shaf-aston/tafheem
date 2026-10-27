"""Smoke tests for the torch-free CATiB parser (backend/services/nahw/syntax/catib_onnx.py).

Skips cleanly, rather than failing, when the model files have not been
dropped into backend/data/parser/ (see catib_onnx.py's docstring).
"""

from backend.services.sarf import morphology
from backend.services.nahw.syntax import catib_onnx
from backend.services.nahw.syntax.catib_onnx import parse
from tests.nahw_helpers import needs_parser

pytestmark = needs_parser


def test_verb_subject_object():
    typed = ["كَتَبَ", "الطَّالِبُ", "رِسَالَةً"]
    catib_onnx.warm()
    tokens = parse(typed, morphology.pick(typed, catib_onnx.disambiguator()))
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
    assert parse([], []) == []
