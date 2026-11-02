"""رأى read as itself (morphology.reading_lemma: CAMeL's راوند is not a lemma رأيت carries): of the heart it
takes two objects, of the eye one; the eye's is the everyday sense it is read in, so a name after its
object names that object again, its بدل (Tasheel 3.10.3 p94: رأيت أخاك زيدًا)."""
from __future__ import annotations

import pytest

from tests.nahw_helpers import analyze, needs_parser


def _roles(sentence: str) -> list[str | None]:
    return [w.get("role") for w in analyze(sentence)["words"]]


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("رَأَيْتُ أَخَاكَ زَيْدًا", ["فعل", "مفعول به", "بدل"]),
    ("رأيت أخاك زيدا", ["فعل", "مفعول به", "بدل"]),
])
def test_ra_a_takes_two_objects_or_one_and_its_badal(sentence, roles):
    assert _roles(sentence) == roles
