"""Smoke tests for the torch-free CATiB parser (backend/services/syntax/catib_onnx.py).

Skips cleanly, rather than failing, when the model files have not been
built into backend/data/parser/ and backend/data/disambig/ (see catib_onnx.py's
docstring and backend/scripts/build_disambig_onnx.py).
"""
import subprocess
import sys
from pathlib import Path

import pytest

from backend.services.syntax.catib_onnx import _files_present, parse

pytestmark = pytest.mark.skipif(
    not _files_present(), reason="CATiB parser model files not present under backend/data/parser/ and backend/data/disambig/"
)


def test_parsing_never_loads_torch():
    # A fresh process: other tests in this run may have imported torch already.
    # First in the file, so it ends before this process loads the models itself.
    code = ("import sys; from backend.services.syntax.catib_onnx import parse; "
            "parse(['كَتَبَ', 'الطَّالِبُ', 'رِسَالَةً']); "
            "sys.exit(1 if {'torch', 'transformers'} & set(sys.modules) else 0)")
    root = Path(__file__).resolve().parent.parent
    assert subprocess.run([sys.executable, "-c", code], cwd=root).returncode == 0


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

