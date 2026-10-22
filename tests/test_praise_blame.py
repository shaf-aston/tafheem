"""نعم وبئس وحبذا (Ibn Aqil, باب نعم وبئس): a جامد past verb made for praise or blame; its doer a
noun with ال, or a hidden pronoun its تمييز explains, or the ذا written into حبذا; the raf' noun
after is the one praised or blamed (المخصوص), a مبتدأ."""
from __future__ import annotations

import pytest

from backend.services.nahw_book import doer_written_in, needs_praised
from tests.nahw_helpers import cards, needs_parser


def _names(sentence: str) -> list[str]:
    return [c.get("name") or c["role"] for c in cards(sentence)]


@needs_parser
@pytest.mark.parametrize("sentence, names", [
    ("نِعْمَ الرَّجُلُ زَيْدٌ", ["فعل جامد لإنشاء المدح", "فاعل", "مبتدأ"]),
    ("بِئْسَ الْخُلُقُ الْكَذِبُ", ["فعل جامد لإنشاء الذم", "فاعل", "مبتدأ"]),
    ("سَاءَ الْمَثَلُ الْكَذِبُ", ["فعل جامد لإنشاء الذم", "فاعل", "مبتدأ"]),
    # the تمييز form: the doer is a pronoun hidden in the verb
    ("نِعْمَ رَجُلًا زَيْدٌ", ["فعل جامد لإنشاء المدح", "تمييز", "مبتدأ"]),
    ("بِئْسَ خُلُقًا الْكَذِبُ", ["فعل جامد لإنشاء الذم", "تمييز", "مبتدأ"]),
    # حبذا: ذا is the doer, written into the verb
    ("حَبَّذَا زَيْدٌ", ["فعل جامد لإنشاء المدح، و«ذا» اسم إشارة في محل رفع فاعل", "مبتدأ"]),
])
def test_praise_and_blame(sentence, names):
    assert _names(sentence) == names


@needs_parser
def test_saa_with_an_object_is_a_plain_verb():
    assert _names("سَاءَ الْخَبَرُ زَيْدًا")[0] == "فعل"


@needs_parser
def test_kana_keeps_its_name():
    assert _names("كَانَ الْبَيْتُ نَظِيفًا")[0] == "فعل ناقص"


def test_book_lists():
    assert needs_praised("ساء", "praise_blame") and not needs_praised("نعم", "praise_blame")
    assert doer_written_in("حبذا", "praise_blame") and not doer_written_in("نعم", "praise_blame")
