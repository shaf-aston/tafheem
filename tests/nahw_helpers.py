"""What every whole-sentence nahw test needs, written once: the one condition for skipping
where the parser is absent, the one way of reading a sentence, and the one walk over the
picture. A test module imports these rather than defining its own copy."""
from __future__ import annotations

import pytest

from backend.services.nahw import iraab
from backend.services.sarf import morphology
from backend.services.nahw.syntax.catib_onnx import files_present
from backend.services.quran import corpus as quran_corpus

# Reading a sentence needs CAMeL's data and the parser's model files, neither in git;
# reading its words alone (lemma, case, a recorded ayah's cards) needs only CAMeL's.
needs_camel = pytest.mark.skipif(not morphology._CAMEL_AVAILABLE, reason="CAMeL data not present")
needs_parser = pytest.mark.skipif(
    not (morphology._CAMEL_AVAILABLE and files_present()),
    reason="CAMeL data or CATiB parser files not present",
)
# A foreign name on a verb's shape (آزر) is read as the name from the Qur'an's corpus, a built file
# not in git (morphology._quran_name); without it the dictionary's verb stands.
needs_corpus = pytest.mark.skipif(not quran_corpus.is_loaded(), reason="Qur'an corpus.db not built")


def analyze(sentence: str) -> dict:
    """The sentence worked out by the rules alone, never read from the treebank's record."""
    return iraab.analyze(sentence, recorded=False)


def cards(sentence: str) -> list[dict]:
    return analyze(sentence)["words"]


def tree_roles(node: dict, key: str = "role") -> list:
    """Every `key` written in the picture (a unit's job, a leaf's role), outermost first,
    the empty ones left out."""
    found = [node[key]] if node.get(key) else []
    for child in node.get("children", []):
        found += tree_roles(child, key)
    return found
